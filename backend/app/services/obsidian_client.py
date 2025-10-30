"""
Obsidian API Client for vault access and note management
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings
from app.services.encryption_service import encryption_service


class ObsidianConnectionError(Exception):
    """Raised when connection to Obsidian fails"""
    pass


class ObsidianAPIError(Exception):
    """Raised when Obsidian API returns an error"""
    pass


class ObsidianVaultError(Exception):
    """Raised when vault operations fail"""
    pass


class ObsidianClient:
    """Obsidian API client for vault access and note management"""
    
    def __init__(self, vault_path: str, api_endpoint: Optional[str] = None, 
                 api_key: Optional[str] = None, api_port: int = 27123):
        self.vault_path = Path(vault_path)
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.api_port = api_port
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Validate vault path
        if not self.vault_path.exists():
            raise ObsidianVaultError(f"Vault path does not exist: {vault_path}")
        
        if not self.vault_path.is_dir():
            raise ObsidianVaultError(f"Vault path is not a directory: {vault_path}")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    @classmethod
    def from_encrypted_credentials(cls, vault_path: str, api_endpoint: Optional[str] = None,
                                 encrypted_api_key: Optional[str] = None, api_port: int = 27123):
        """Create client from encrypted API key"""
        api_key = None
        if encrypted_api_key:
            api_key = encryption_service.decrypt(encrypted_api_key)
            if not api_key:
                raise ObsidianConnectionError("Failed to decrypt API key")
        
        return cls(vault_path, api_endpoint, api_key, api_port)
    
    def _get_note_path(self, note_path: str) -> Path:
        """Get full path to note file with path traversal protection"""
        # Ensure .md extension
        if not note_path.endswith('.md'):
            note_path += '.md'
        
        # Construct and resolve paths
        note_path_obj = Path(note_path)
        full_path = (self.vault_path / note_path_obj).resolve()
        vault_path_resolved = self.vault_path.resolve()
        
        # Verify the resolved path is within the vault directory
        try:
            full_path.relative_to(vault_path_resolved)
        except ValueError:
            raise ValueError(f"Invalid note path: {note_path} (path traversal detected)")
        
        return full_path
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash of note content for change detection"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def _make_api_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make request to Obsidian REST API if available"""
        if not self.api_endpoint:
            raise ObsidianAPIError("No API endpoint configured")
        
        url = urljoin(self.api_endpoint, endpoint)
        headers = kwargs.pop("headers", {})
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        response = await self.client.request(method, url, headers=headers, **kwargs)
        
        if response.status_code >= 400:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            raise ObsidianAPIError(f"API error {response.status_code}: {error_data}")
        
        return response
    
    # File system operations (primary method)
    async def create_note(self, note_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        """Create a new note in the vault"""
        full_path = self._get_note_path(note_path)
        
        # Create directory if it doesn't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if note already exists
        if full_path.exists() and not overwrite:
            raise ObsidianVaultError(f"Note already exists: {note_path}")
        
        try:
            # Write note content
            full_path.write_text(content, encoding='utf-8')
            
            return {
                "path": note_path,
                "full_path": str(full_path),
                "content_hash": self._calculate_content_hash(content),
                "created_at": datetime.utcnow().isoformat(),
                "size": len(content)
            }
        except Exception as e:
            raise ObsidianVaultError(f"Failed to create note {note_path}: {str(e)}")
    
    async def read_note(self, note_path: str) -> Dict[str, Any]:
        """Read a note from the vault"""
        full_path = self._get_note_path(note_path)
        
        if not full_path.exists():
            raise ObsidianVaultError(f"Note does not exist: {note_path}")
        
        try:
            content = full_path.read_text(encoding='utf-8')
            stat = full_path.stat()
            
            return {
                "path": note_path,
                "content": content,
                "content_hash": self._calculate_content_hash(content),
                "size": len(content),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            raise ObsidianVaultError(f"Failed to read note {note_path}: {str(e)}")
    
    async def update_note(self, note_path: str, content: str) -> Dict[str, Any]:
        """Update an existing note"""
        full_path = self._get_note_path(note_path)
        
        if not full_path.exists():
            raise ObsidianVaultError(f"Note does not exist: {note_path}")
        
        try:
            # Read current content for comparison
            old_content = full_path.read_text(encoding='utf-8')
            old_hash = self._calculate_content_hash(old_content)
            new_hash = self._calculate_content_hash(content)
            
            # Only update if content has changed
            if old_hash != new_hash:
                full_path.write_text(content, encoding='utf-8')
                updated = True
            else:
                updated = False
            
            return {
                "path": note_path,
                "content_hash": new_hash,
                "updated": updated,
                "updated_at": datetime.utcnow().isoformat(),
                "size": len(content)
            }
        except Exception as e:
            raise ObsidianVaultError(f"Failed to update note {note_path}: {str(e)}")
    
    async def delete_note(self, note_path: str) -> Dict[str, Any]:
        """Delete a note from the vault"""
        full_path = self._get_note_path(note_path)
        
        if not full_path.exists():
            raise ObsidianVaultError(f"Note does not exist: {note_path}")
        
        try:
            full_path.unlink()
            
            return {
                "path": note_path,
                "deleted": True,
                "deleted_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ObsidianVaultError(f"Failed to delete note {note_path}: {str(e)}")
    
    async def note_exists(self, note_path: str) -> bool:
        """Check if a note exists in the vault"""
        full_path = self._get_note_path(note_path)
        return full_path.exists()
    
    async def list_notes(self, folder: str = "", recursive: bool = True) -> List[Dict[str, Any]]:
        """List all notes in the vault or a specific folder"""
        search_path = self.vault_path / folder if folder else self.vault_path
        
        if not search_path.exists():
            return []
        
        notes = []
        pattern = "**/*.md" if recursive else "*.md"
        
        try:
            for note_path in search_path.glob(pattern):
                if note_path.is_file():
                    relative_path = note_path.relative_to(self.vault_path)
                    stat = note_path.stat()
                    
                    notes.append({
                        "path": str(relative_path).replace('.md', ''),
                        "full_path": str(note_path),
                        "name": note_path.stem,
                        "folder": str(relative_path.parent) if relative_path.parent != Path('.') else "",
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            return sorted(notes, key=lambda x: x["modified_at"], reverse=True)
        except Exception as e:
            raise ObsidianVaultError(f"Failed to list notes: {str(e)}")
    
    async def create_folder(self, folder_path: str) -> Dict[str, Any]:
        """Create a folder in the vault"""
        full_path = self.vault_path / folder_path
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "path": folder_path,
                "full_path": str(full_path),
                "created_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ObsidianVaultError(f"Failed to create folder {folder_path}: {str(e)}")
    
    async def search_notes(self, query: str, folder: str = "") -> List[Dict[str, Any]]:
        """Search for notes containing specific text"""
        search_path = self.vault_path / folder if folder else self.vault_path
        results = []
        
        try:
            for note_path in search_path.glob("**/*.md"):
                if note_path.is_file():
                    try:
                        content = note_path.read_text(encoding='utf-8')
                        if query.lower() in content.lower():
                            relative_path = note_path.relative_to(self.vault_path)
                            stat = note_path.stat()
                            
                            # Find matching lines
                            lines = content.split('\n')
                            matching_lines = [
                                {"line_number": i + 1, "content": line.strip()}
                                for i, line in enumerate(lines)
                                if query.lower() in line.lower()
                            ]
                            
                            results.append({
                                "path": str(relative_path).replace('.md', ''),
                                "name": note_path.stem,
                                "folder": str(relative_path.parent) if relative_path.parent != Path('.') else "",
                                "matches": len(matching_lines),
                                "matching_lines": matching_lines[:5],  # Limit to first 5 matches
                                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                            })
                    except Exception:
                        # Skip files that can't be read
                        continue
            
            return sorted(results, key=lambda x: x["matches"], reverse=True)
        except Exception as e:
            raise ObsidianVaultError(f"Failed to search notes: {str(e)}")
    
    # Backlink operations
    async def extract_backlinks(self, content: str) -> List[str]:
        """Extract backlinks from note content"""
        import re
        
        # Extract wikilinks [[Note Name]]
        wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
        
        # Extract markdown links [text](note.md)
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        markdown_note_names = [link[1].replace('.md', '') for link in markdown_links]
        
        # Combine and deduplicate
        all_links = list(set(wikilinks + markdown_note_names))
        
        return all_links
    
    async def add_backlink(self, note_path: str, target_note: str, link_format: str = "wikilink") -> Dict[str, Any]:
        """Add a backlink to a note"""
        if not await self.note_exists(note_path):
            raise ObsidianVaultError(f"Source note does not exist: {note_path}")
        
        note_data = await self.read_note(note_path)
        content = note_data["content"]
        
        # Check if backlink already exists
        existing_links = await self.extract_backlinks(content)
        if target_note in existing_links:
            return {"added": False, "reason": "Backlink already exists"}
        
        # Add backlink based on format
        if link_format == "wikilink":
            backlink = f"[[{target_note}]]"
        else:  # markdown
            backlink = f"[{target_note}]({target_note}.md)"
        
        # Add backlink to the end of the content
        updated_content = content + f"\n\n{backlink}"
        
        await self.update_note(note_path, updated_content)
        
        return {
            "added": True,
            "backlink": backlink,
            "target_note": target_note,
            "format": link_format
        }
    
    # Vault information
    async def get_vault_info(self) -> Dict[str, Any]:
        """Get information about the vault"""
        try:
            notes = await self.list_notes()
            total_size = sum(note["size"] for note in notes)
            
            # Get vault config if it exists
            config_path = self.vault_path / ".obsidian" / "config"
            vault_config = {}
            if config_path.exists():
                try:
                    vault_config = json.loads(config_path.read_text())
                except Exception:
                    pass
            
            return {
                "vault_path": str(self.vault_path),
                "vault_name": self.vault_path.name,
                "total_notes": len(notes),
                "total_size": total_size,
                "api_available": self.api_endpoint is not None,
                "config": vault_config,
                "last_checked": datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise ObsidianVaultError(f"Failed to get vault info: {str(e)}")
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the Obsidian connection"""
        health = {
            "vault_accessible": False,
            "api_accessible": False,
            "can_read": False,
            "can_write": False,
            "errors": []
        }
        
        try:
            # Check vault accessibility
            if self.vault_path.exists() and self.vault_path.is_dir():
                health["vault_accessible"] = True
            else:
                health["errors"].append("Vault path not accessible")
            
            # Check read permissions
            try:
                await self.list_notes()
                health["can_read"] = True
            except Exception as e:
                health["errors"].append(f"Cannot read vault: {str(e)}")
            
            # Check write permissions
            try:
                test_note = "test_connection.md"
                test_content = f"# Test Connection\n\nCreated at: {datetime.utcnow().isoformat()}"
                
                await self.create_note(test_note, test_content, overwrite=True)
                await self.delete_note(test_note)
                health["can_write"] = True
            except Exception as e:
                health["errors"].append(f"Cannot write to vault: {str(e)}")
            
            # Check API if configured
            if self.api_endpoint:
                try:
                    response = await self._make_api_request("GET", "/")
                    health["api_accessible"] = response.status_code == 200
                except Exception as e:
                    health["errors"].append(f"API not accessible: {str(e)}")
            
            health["overall_status"] = "healthy" if not health["errors"] else "unhealthy"
            health["checked_at"] = datetime.utcnow().isoformat()
            
            return health
        except Exception as e:
            health["errors"].append(f"Health check failed: {str(e)}")
            health["overall_status"] = "unhealthy"
            health["checked_at"] = datetime.utcnow().isoformat()
            return health