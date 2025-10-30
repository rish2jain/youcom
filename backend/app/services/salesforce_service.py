"""Salesforce integration service for CRM workflows"""
import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64

logger = logging.getLogger(__name__)


class SalesforceService:
    """Service for integrating with Salesforce API"""

    def __init__(self, instance_url: str, access_token: str):
        self.instance_url = instance_url.rstrip('/')
        self.access_token = access_token
        self.api_version = "v58.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    @classmethod
    async def authenticate(
        cls,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        security_token: str,
        instance_url: str = "https://login.salesforce.com"
    ) -> Dict[str, Any]:
        """Authenticate with Salesforce using OAuth2 password flow"""
        try:
            auth_url = f"{instance_url}/services/oauth2/token"
            
            data = {
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "username": username,
                "password": f"{password}{security_token}"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    auth_url,
                    data=data,
                    timeout=10.0
                )

                if response.status_code == 200:
                    auth_data = response.json()
                    return {
                        "status": "success",
                        "access_token": auth_data["access_token"],
                        "instance_url": auth_data["instance_url"],
                        "id": auth_data["id"]
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }

        except Exception as e:
            logger.error(f"❌ Salesforce authentication failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def test_connection(self) -> Dict[str, Any]:
        """Test the Salesforce API connection"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.instance_url}/services/data/{self.api_version}/sobjects/",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": "Successfully connected to Salesforce"
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"❌ Salesforce connection test failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def create_account(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update an Account record for a company"""
        try:
            company_name = company_data.get("company_name", "")
            research_data = company_data.get("research_data", {})
            
            # Prepare account data
            account_data = {
                "Name": company_name,
                "Type": "Competitor",
                "Description": f"Competitive intelligence data for {company_name}",
                "Website": research_data.get("website", ""),
                "Industry": research_data.get("industry", ""),
                # Custom fields (would need to be created in Salesforce)
                "CIA_Total_Sources__c": research_data.get("total_sources", 0),
                "CIA_Last_Research_Date__c": datetime.utcnow().isoformat(),
                "CIA_Research_Summary__c": research_data.get("summary", "")[:32000]  # Salesforce text limit
            }

            # Remove empty fields
            account_data = {k: v for k, v in account_data.items() if v}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.instance_url}/services/data/{self.api_version}/sobjects/Account/",
                    headers=self.headers,
                    json=account_data,
                    timeout=30.0
                )

                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"✅ Created Salesforce Account for {company_name}")
                    return {
                        "status": "success",
                        "account_id": result["id"],
                        "company": company_name
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ Failed to create Salesforce Account: {error_msg}")
                    return {"status": "error", "error": error_msg}

        except Exception as e:
            logger.error(f"❌ Salesforce Account creation failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def create_opportunity(self, impact_card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an Opportunity record based on competitive impact"""
        try:
            competitor_name = impact_card_data.get("competitor_name", "")
            risk_score = impact_card_data.get("risk_score", 0)
            risk_level = impact_card_data.get("risk_level", "unknown")
            
            # Determine opportunity stage based on risk level
            stage_mapping = {
                "critical": "Qualification",
                "high": "Needs Analysis", 
                "medium": "Prospecting",
                "low": "Prospecting"
            }
            
            opportunity_data = {
                "Name": f"Competitive Response - {competitor_name}",
                "StageName": stage_mapping.get(risk_level.lower(), "Prospecting"),
                "CloseDate": (datetime.utcnow().date() + datetime.timedelta(days=90)).isoformat(),
                "Type": "Existing Customer - Upgrade",
                "Description": f"Competitive threat from {competitor_name} (Risk Score: {risk_score})",
                # Custom fields
                "CIA_Competitor_Name__c": competitor_name,
                "CIA_Risk_Score__c": risk_score,
                "CIA_Risk_Level__c": risk_level.title(),
                "CIA_Impact_Summary__c": impact_card_data.get("impact_summary", "")[:32000]
            }

            # Remove empty fields
            opportunity_data = {k: v for k, v in opportunity_data.items() if v}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.instance_url}/services/data/{self.api_version}/sobjects/Opportunity/",
                    headers=self.headers,
                    json=opportunity_data,
                    timeout=30.0
                )

                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"✅ Created Salesforce Opportunity for {competitor_name}")
                    return {
                        "status": "success",
                        "opportunity_id": result["id"],
                        "competitor": competitor_name
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ Failed to create Salesforce Opportunity: {error_msg}")
                    return {"status": "error", "error": error_msg}

        except Exception as e:
            logger.error(f"❌ Salesforce Opportunity creation failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def create_task(
        self,
        subject: str,
        description: str,
        assigned_to_id: Optional[str] = None,
        related_to_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Task record for follow-up actions"""
        try:
            task_data = {
                "Subject": subject,
                "Description": description,
                "Status": "Not Started",
                "Priority": "Normal",
                "ActivityDate": (datetime.utcnow().date() + datetime.timedelta(days=7)).isoformat()
            }

            if assigned_to_id:
                task_data["OwnerId"] = assigned_to_id
            
            if related_to_id:
                task_data["WhatId"] = related_to_id

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.instance_url}/services/data/{self.api_version}/sobjects/Task/",
                    headers=self.headers,
                    json=task_data,
                    timeout=30.0
                )

                if response.status_code == 201:
                    result = response.json()
                    logger.info(f"✅ Created Salesforce Task: {subject}")
                    return {
                        "status": "success",
                        "task_id": result["id"],
                        "subject": subject
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ Failed to create Salesforce Task: {error_msg}")
                    return {"status": "error", "error": error_msg}

        except Exception as e:
            logger.error(f"❌ Salesforce Task creation failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def query_records(self, soql_query: str) -> Dict[str, Any]:
        """Execute a SOQL query"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.instance_url}/services/data/{self.api_version}/query/",
                    headers=self.headers,
                    params={"q": soql_query},
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "records": result.get("records", []),
                        "total_size": result.get("totalSize", 0)
                    }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ Salesforce query failed: {error_msg}")
                    return {"status": "error", "error": error_msg}

        except Exception as e:
            logger.error(f"❌ Salesforce query failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.instance_url}/services/oauth2/userinfo",
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "status": "success",
                        "user_id": user_data.get("user_id"),
                        "name": user_data.get("name"),
                        "email": user_data.get("email"),
                        "organization_id": user_data.get("organization_id")
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }

        except Exception as e:
            logger.error(f"❌ Failed to get Salesforce user info: {str(e)}")
            return {"status": "error", "error": str(e)}


def get_salesforce_service(instance_url: str, access_token: str) -> SalesforceService:
    """Factory function to create Salesforce service instance"""
    return SalesforceService(instance_url, access_token)