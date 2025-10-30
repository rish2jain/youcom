"""Notion integration service for syncing research findings"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class NotionService:
    """Service for integrating with Notion API"""

    def __init__(self, api_token: str, database_id: Optional[str] = None):
        self.api_token = api_token
        self.database_id = database_id
        self.api_base = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Test the Notion API connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/users/me",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "status": "success",
                        "user": user_data.get("name", "Unknown"),
                        "workspace": user_data.get("workspace_name", "Unknown")
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Notion connection test failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def create_company_research_page(
        self,
        company_name: str,
        research_data: Dict[str, Any],
        database_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new page in Notion database for company research"""
        
        db_id = database_id or self.database_id
        if not db_id:
            return {"status": "error", "error": "No database ID provided"}

        try:
            # Extract key information from research data
            search_results = research_data.get("search_results", {})
            research_report = research_data.get("research_report", {})
            total_sources = research_data.get("total_sources", 0)
            
            # Create page properties
            properties = {
                "Company": {
                    "title": [
                        {
                            "text": {
                                "content": company_name
                            }
                        }
                    ]
                },
                "Research Date": {
                    "date": {
                        "start": datetime.utcnow().isoformat()
                    }
                },
                "Total Sources": {
                    "number": total_sources
                },
                "Status": {
                    "select": {
                        "name": "Completed"
                    }
                }
            }

            # Create page content
            children = []
            
            # Add executive summary
            if research_report.get("summary"):
                children.extend([
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": "Executive Summary"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": research_report["summary"]}}]
                        }
                    }
                ])

            # Add key findings
            if search_results.get("results"):
                children.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Key Findings"}}]
                    }
                })
                
                for i, result in enumerate(search_results["results"][:5]):  # Top 5 results
                    title = result.get("title", "Untitled")
                    url = result.get("url", "")
                    snippet = result.get("snippet", "")
                    
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": f"{title}: {snippet}"},
                                    "href": url if url else None
                                }
                            ]
                        }
                    })

            # Create the page
            page_data = {
                "parent": {"database_id": db_id},
                "properties": properties,
                "children": children
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/pages",
                    headers=self.headers,
                    json=page_data,
                    timeout=30.0
                )

                if response.status_code == 200:
                    page = response.json()
                    logger.info(f"✅ Created Notion page for {company_name}")
                    return {
                        "status": "success",
                        "page_id": page["id"],
                        "url": page["url"],
                        "company": company_name
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ Failed to create Notion page: {error_msg}")
                    return {"status": "error", "error": error_msg}

        except Exception as e:
            logger.error(f"❌ Notion page creation failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def create_impact_card_page(
        self,
        competitor_name: str,
        impact_card_data: Dict[str, Any],
        database_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new page in Notion database for impact card"""
        
        db_id = database_id or self.database_id
        if not db_id:
            return {"status": "error", "error": "No database ID provided"}

        try:
            # Extract impact card information
            risk_score = impact_card_data.get("risk_score", 0)
            risk_level = impact_card_data.get("risk_level", "unknown")
            confidence_score = impact_card_data.get("confidence_score", 0)
            impact_summary = impact_card_data.get("impact_summary", "")
            
            # Create page properties
            properties = {
                "Competitor": {
                    "title": [
                        {
                            "text": {
                                "content": competitor_name
                            }
                        }
                    ]
                },
                "Risk Score": {
                    "number": risk_score
                },
                "Risk Level": {
                    "select": {
                        "name": risk_level.title()
                    }
                },
                "Confidence": {
                    "number": confidence_score
                },
                "Analysis Date": {
                    "date": {
                        "start": datetime.utcnow().isoformat()
                    }
                }
            }

            # Create page content
            children = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Impact Analysis"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": impact_summary}}]
                    }
                }
            ]

            # Add recommendations if available
            recommendations = impact_card_data.get("recommendations", [])
            if recommendations:
                children.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": "Recommendations"}}]
                    }
                })
                
                for rec in recommendations:
                    children.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": rec}}]
                        }
                    })

            # Create the page
            page_data = {
                "parent": {"database_id": db_id},
                "properties": properties,
                "children": children
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/pages",
                    headers=self.headers,
                    json=page_data,
                    timeout=30.0
                )

                if response.status_code == 200:
                    page = response.json()
                    logger.info(f"✅ Created Notion impact card for {competitor_name}")
                    return {
                        "status": "success",
                        "page_id": page["id"],
                        "url": page["url"],
                        "competitor": competitor_name
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ Failed to create Notion impact card: {error_msg}")
                    return {"status": "error", "error": error_msg}

        except Exception as e:
            logger.error(f"❌ Notion impact card creation failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def list_databases(self) -> Dict[str, Any]:
        """List available Notion databases"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/search",
                    headers=self.headers,
                    json={
                        "filter": {
                            "value": "database",
                            "property": "object"
                        }
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    databases = []
                    
                    for db in data.get("results", []):
                        databases.append({
                            "id": db["id"],
                            "title": db.get("title", [{}])[0].get("plain_text", "Untitled"),
                            "url": db["url"]
                        })
                    
                    return {
                        "status": "success",
                        "databases": databases
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }

        except Exception as e:
            logger.error(f"❌ Failed to list Notion databases: {str(e)}")
            return {"status": "error", "error": str(e)}


def get_notion_service(api_token: str, database_id: Optional[str] = None) -> NotionService:
    """Factory function to create Notion service instance"""
    return NotionService(api_token, database_id)