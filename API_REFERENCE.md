# Enterprise CIA API Reference

> Complete API documentation for Enterprise CIA competitive intelligence platform
> Base URL: `http://localhost:8765` (development) | `https://your-domain.com` (production)

## Table of Contents

1. [Authentication](#authentication)
2. [Core Intelligence APIs](#core-intelligence-apis)
3. [Integration APIs](#integration-apis)
4. [Analytics APIs](#analytics-apis)
5. [System APIs](#system-apis)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)

---

## Authentication

Most endpoints require authentication using JWT tokens.

### Obtain Token
```
POST /api/v1/auth/login
```

**Request**:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

### Using Authentication
Include token in `Authorization` header:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Core Intelligence APIs

### Impact Card Generation

Generate comprehensive competitive intelligence Impact Card using all 4 You.com APIs.

#### Generate Impact Card
```
POST /api/v1/impact/generate
Content-Type: application/json
```

**Request Body**:
```json
{
  "competitor": "OpenAI",
  "keywords": ["GPT", "ChatGPT", "AI models"]
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| competitor | string | Yes | Competitor company name |
| keywords | array[string] | No | Keywords for monitoring |

**Response**: `200 OK`
```json
{
  "id": 123,
  "competitor_name": "OpenAI",
  "risk_score": 85,
  "risk_level": "HIGH",
  "confidence_score": 0.92,
  "total_sources": 427,
  "impact_areas": [
    {
      "area": "product",
      "score": 90,
      "weight": 0.35,
      "description": "Significant product advancement threat"
    },
    {
      "area": "marketing",
      "score": 75,
      "weight": 0.25,
      "description": "Increased marketing presence"
    },
    {
      "area": "pricing",
      "score": 60,
      "weight": 0.20,
      "description": "Competitive pricing pressure"
    }
  ],
  "key_insights": [
    "Launched GPT-4 Turbo with 128K context window",
    "Introduced custom GPTs marketplace",
    "Expanded enterprise offerings"
  ],
  "recommended_actions": [
    {
      "action": "Evaluate our context window capabilities",
      "priority": "HIGH",
      "timeline": "2 weeks",
      "effort_score": 8
    }
  ],
  "news_data": {
    "articles": [...],
    "total_count": 15
  },
  "search_context": {
    "results": [...],
    "total_count": 8
  },
  "analysis_data": {
    "strategic_implications": "...",
    "reasoning": "..."
  },
  "research_report": {
    "summary": "...",
    "citations": [...]
  },
  "created_at": "2025-10-31T12:00:00Z",
  "generated_at": "2025-10-31T12:00:00Z"
}
```

**API Orchestration Flow**:
1. **News API**: Fetch recent competitor activity (15min cache)
2. **Search API**: Enrich context with market data (1hr cache)
3. **Chat API**: Analyze impact with Custom Agent
4. **ARI API**: Generate 400+ source research report (7day cache)

**Real-time Progress Updates**:
Connect to Socket.IO for live progress:
```javascript
socket.on('impact_card_progress', (data) => {
  console.log(data.step); // "news", "search", "chat", "ari"
  console.log(data.progress); // 0-100
})
```

**Error Responses**:
- `400 Bad Request`: Invalid competitor name or parameters
- `401 Unauthorized`: Missing or invalid token
- `429 Too Many Requests`: Rate limit exceeded
- `503 Service Unavailable`: You.com API temporarily unavailable

---

#### List Impact Cards
```
GET /api/v1/impact/
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Number of records to skip |
| limit | integer | 50 | Maximum records to return |
| competitor | string | - | Filter by competitor name |
| risk_level | string | - | Filter by risk level (LOW, MEDIUM, HIGH) |
| days | integer | 30 | Filter by creation date (last N days) |

**Response**: `200 OK`
```json
{
  "total": 156,
  "items": [
    {
      "id": 123,
      "competitor_name": "OpenAI",
      "risk_score": 85,
      "risk_level": "HIGH",
      "confidence_score": 0.92,
      "created_at": "2025-10-31T12:00:00Z"
    }
  ]
}
```

---

#### Get Impact Card by ID
```
GET /api/v1/impact/{impact_card_id}
```

**Response**: `200 OK` (same structure as generate endpoint)

**Error Responses**:
- `404 Not Found`: Impact card not found

---

#### Provide ML Feedback
```
POST /api/v1/ml/feedback
```

**Request Body**:
```json
{
  "impact_card_id": 123,
  "feedback_type": "risk_score",
  "expected": 70,
  "actual": 85,
  "field": "risk_score"
}
```

**Response**: `200 OK`
```json
{
  "feedback_id": 456,
  "requires_review": true,
  "retraining_triggered": false,
  "message": "Feedback recorded successfully"
}
```

---

### Company Research

Generate instant comprehensive company profiles with 400+ sources via ARI API.

#### Research Company
```
POST /api/v1/research/company
Content-Type: application/json
```

**Request Body**:
```json
{
  "company_name": "Perplexity AI"
}
```

**Response**: `200 OK`
```json
{
  "id": 789,
  "company_name": "Perplexity AI",
  "total_sources": 412,
  "search_results": {
    "count": 8,
    "results": [
      {
        "title": "Perplexity AI Company Profile",
        "snippet": "AI-powered search engine and answer engine...",
        "url": "https://example.com/perplexity-profile",
        "source": "TechCrunch"
      }
    ]
  },
  "research_report": {
    "summary": "Comprehensive analysis of Perplexity AI...",
    "key_insights": [
      "Raised $100M Series B funding",
      "Growing user base to 10M+ monthly active users",
      "Competing directly with Google Search"
    ],
    "citations": [
      {
        "title": "Perplexity AI Raises $100M",
        "url": "https://example.com/funding",
        "credibility": 0.95
      }
    ],
    "generated_at": "2025-10-31T12:00:00Z"
  },
  "api_usage": {
    "search_calls": 1,
    "ari_calls": 1,
    "total_calls": 2
  },
  "created_at": "2025-10-31T12:00:00Z"
}
```

**API Flow**:
1. **Search API**: Get company overview and context
2. **ARI API**: Generate deep 400+ source research report

---

#### List Company Research
```
GET /api/v1/research/
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Number of records to skip |
| limit | integer | 50 | Maximum records to return |
| company_name | string | - | Filter by company name |

**Response**: `200 OK`
```json
{
  "total": 89,
  "items": [
    {
      "id": 789,
      "company_name": "Perplexity AI",
      "total_sources": 412,
      "created_at": "2025-10-31T12:00:00Z"
    }
  ]
}
```

---

#### Export Research as PDF
```
GET /api/v1/research/{research_id}/export/pdf
```

**Response**: `200 OK`
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="Perplexity_AI_Research_Report.pdf"

[PDF Binary Data]
```

---

#### Share Research via Email
```
POST /api/v1/research/{research_id}/share
```

**Request Body**:
```json
{
  "recipients": ["colleague@example.com", "manager@example.com"],
  "message": "Here's the research on Perplexity AI"
}
```

**Response**: `200 OK`
```json
{
  "message": "Research shared successfully",
  "recipients": ["colleague@example.com", "manager@example.com"]
}
```

---

### Competitor Watchlist

Manage competitor monitoring with keyword-based alerts.

#### Create Watch Item
```
POST /api/v1/watch/
```

**Request Body**:
```json
{
  "competitor_name": "Anthropic",
  "keywords": ["Claude", "AI assistant", "constitutional AI"]
}
```

**Response**: `201 Created`
```json
{
  "id": 456,
  "competitor_name": "Anthropic",
  "keywords": ["Claude", "AI assistant", "constitutional AI"],
  "status": "active",
  "created_at": "2025-10-31T12:00:00Z",
  "last_checked": null
}
```

---

#### List Watch Items
```
GET /api/v1/watch/
```

**Response**: `200 OK`
```json
{
  "total": 12,
  "items": [
    {
      "id": 456,
      "competitor_name": "Anthropic",
      "keywords": ["Claude", "AI assistant"],
      "status": "active",
      "last_checked": "2025-10-31T11:45:00Z"
    }
  ]
}
```

---

#### Delete Watch Item
```
DELETE /api/v1/watch/{watch_id}
```

**Response**: `204 No Content`

---

## Integration APIs

### Notion Integration

Sync research and Impact Cards to Notion databases.

#### Test Notion Connection
```
POST /api/v1/integrations/notion/test
```

**Request Body**:
```json
{
  "api_key": "secret_your_notion_api_key",
  "database_id": "abc123def456"
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "message": "Notion connection successful",
  "database_name": "Enterprise CIA Research"
}
```

---

#### Sync Research to Notion
```
POST /api/v1/integrations/notion/sync-research
```

**Request Body**:
```json
{
  "research_id": 789,
  "database_id": "abc123def456"
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "notion_page_id": "xyz789abc123",
  "notion_page_url": "https://notion.so/xyz789abc123"
}
```

---

### Salesforce Integration

Sync Impact Cards to Salesforce CRM as opportunities or leads.

#### Test Salesforce Connection
```
POST /api/v1/integrations/salesforce/test
```

**Request Body**:
```json
{
  "client_id": "your_salesforce_client_id",
  "client_secret": "your_salesforce_client_secret",
  "username": "user@company.com",
  "password": "your_password",
  "security_token": "your_security_token"
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "message": "Salesforce connection successful",
  "instance_url": "https://your-org.salesforce.com"
}
```

---

#### Sync Impact to Salesforce
```
POST /api/v1/integrations/salesforce/sync-impact
```

**Request Body**:
```json
{
  "impact_card_id": 123,
  "sync_as": "opportunity"
}
```

**Response**: `200 OK`
```json
{
  "status": "success",
  "salesforce_id": "006ABC123DEF456",
  "salesforce_url": "https://your-org.salesforce.com/006ABC123DEF456"
}
```

---

## Analytics APIs

Advanced predictive analytics and market intelligence.

### Competitor Trends
```
GET /api/v1/analytics/competitor-trends/{competitor_name}
```

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | integer | 90 | Historical data period |

**Response**: `200 OK`
```json
{
  "competitor": "OpenAI",
  "period_days": 90,
  "risk_score_trend": {
    "current": 85,
    "previous": 78,
    "change": 7,
    "series": [
      {"date": "2025-08-01", "score": 72},
      {"date": "2025-09-01", "score": 78},
      {"date": "2025-10-01", "score": 85}
    ]
  },
  "activity_trend": {
    "total_mentions": 1247,
    "change_percent": 23.5
  },
  "predictions": {
    "next_30_days": {
      "expected_risk_score": 88,
      "confidence": 0.87
    }
  }
}
```

---

### Market Landscape
```
GET /api/v1/analytics/market-landscape
```

**Response**: `200 OK`
```json
{
  "total_competitors": 15,
  "high_risk_competitors": 4,
  "market_dynamics": {
    "most_active_areas": ["product", "pricing"],
    "emerging_threats": ["New AI model launches", "Pricing changes"]
  },
  "competitor_comparison": [
    {
      "competitor": "OpenAI",
      "risk_score": 85,
      "market_share_estimate": "35%"
    }
  ]
}
```

---

### Executive Summary
```
GET /api/v1/analytics/executive-summary
```

**Response**: `200 OK`
```json
{
  "period": "Last 30 days",
  "key_metrics": {
    "total_impact_cards": 23,
    "high_risk_threats": 5,
    "total_research_reports": 12
  },
  "top_competitors": [
    {
      "name": "OpenAI",
      "risk_score": 85,
      "trend": "increasing"
    }
  ],
  "recommended_actions": [
    {
      "priority": "HIGH",
      "action": "Review OpenAI's recent product launches",
      "rationale": "Significant competitive threat detected"
    }
  ]
}
```

---

## System APIs

### Health Checks

#### Basic Health Check
```
GET /health
```

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "Enterprise CIA Backend",
  "version": "1.0.0",
  "powered_by": "You.com APIs"
}
```

---

#### You.com APIs Health Check
```
GET /api/v1/health/you-apis
```

**Response**: `200 OK`
```json
{
  "timestamp": "2025-10-31T12:00:00Z",
  "overall_status": "healthy",
  "apis": {
    "news": {
      "status": "healthy",
      "endpoint": "https://api.ydc-index.io/livenews"
    },
    "search": {
      "status": "healthy",
      "endpoint": "https://api.ydc-index.io/v1/search"
    },
    "chat": {
      "status": "healthy",
      "endpoint": "https://api.you.com/v1/agents/runs"
    },
    "ari": {
      "status": "healthy",
      "endpoint": "https://api.you.com/v1/agents/runs"
    }
  },
  "resilience_status": {
    "circuit_breakers": {
      "news": {"state": "closed", "failure_count": 0},
      "search": {"state": "closed", "failure_count": 0},
      "chat": {"state": "closed", "failure_count": 0},
      "ari": {"state": "closed", "failure_count": 0}
    }
  }
}
```

**Status Values**:
- `healthy`: All systems operational
- `degraded`: Some APIs experiencing issues
- `unhealthy`: Multiple APIs unavailable

---

#### Resilience Status
```
GET /api/v1/health/resilience
```

**Response**: `200 OK`
```json
{
  "timestamp": "2025-10-31T12:00:00Z",
  "summary": {
    "total_circuits": 4,
    "open_circuits": 0,
    "degraded_circuits": 0,
    "healthy_circuits": 4,
    "overall_health": "healthy"
  },
  "details": {
    "circuit_breakers": {
      "news": {
        "state": "closed",
        "failure_count": 0,
        "last_failure": null
      }
    }
  },
  "recommendations": [
    "✅ All APIs operating normally"
  ]
}
```

**Circuit Breaker States**:
- `closed`: Normal operation
- `half_open`: Testing recovery
- `open`: Circuit broken, using fallback

---

### API Usage Metrics
```
GET /api/v1/metrics/usage
```

**Response**: `200 OK`
```json
{
  "period": "Last 30 days",
  "you_api_calls": {
    "news_calls": 1247,
    "search_calls": 892,
    "chat_calls": 456,
    "ari_calls": 234,
    "total_calls": 2829
  },
  "cost_estimate": {
    "total_usd": 141.45,
    "per_api": {
      "news": 24.94,
      "search": 44.60,
      "chat": 45.60,
      "ari": 26.31
    }
  },
  "cache_efficiency": {
    "hit_rate": 0.42,
    "total_cached_calls": 1188,
    "cost_saved_usd": 59.40
  }
}
```

---

## Error Handling

### Standard Error Response

All errors follow this structure:

```json
{
  "error": "Description of the error",
  "status_code": 400,
  "service": "Enterprise CIA",
  "details": {
    "field": "competitor",
    "issue": "Competitor name cannot be empty"
  }
}
```

### HTTP Status Codes

| Status | Meaning | Common Causes |
|--------|---------|---------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 204 | No Content | Resource deleted |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | You.com API temporarily down |

### You.com API Errors

When You.com APIs fail, errors include `api_type` context:

```json
{
  "error": "You.com News API error",
  "status_code": 503,
  "api_type": "news",
  "details": {
    "message": "Timeout after 10 seconds",
    "endpoint": "https://api.ydc-index.io/livenews"
  }
}
```

**API Types**: `news`, `search`, `chat`, `ari`

### Circuit Breaker Behavior

When an API circuit breaker opens:
- Immediate fallback to cached data (if available)
- Error response with `503 Service Unavailable`
- Automatic recovery attempts every 30 seconds

---

## Rate Limiting

### Default Limits

| Endpoint Pattern | Rate Limit | Window |
|------------------|------------|--------|
| `/api/v1/impact/generate` | 10 requests | 1 minute |
| `/api/v1/research/company` | 20 requests | 1 minute |
| `/api/v1/watch/*` | 30 requests | 1 minute |
| `/api/v1/integrations/*` | 15 requests | 1 minute |
| All other endpoints | 100 requests | 1 minute |

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1635780000
```

### Rate Limit Exceeded

When rate limit is exceeded:

**Response**: `429 Too Many Requests`
```json
{
  "error": "Rate limit exceeded",
  "status_code": 429,
  "retry_after": 42
}
```

**Headers**:
```
Retry-After: 42
```

---

## WebSocket Events

Connect to Socket.IO for real-time updates:

```javascript
import io from 'socket.io-client'

const socket = io('http://localhost:8765')

// Impact Card generation progress
socket.on('impact_card_progress', (data) => {
  console.log(data)
  // {
  //   step: "news" | "search" | "chat" | "ari",
  //   progress: 0-100,
  //   message: "Fetching news articles...",
  //   timestamp: "2025-10-31T12:00:00Z"
  // }
})

// Research generation progress
socket.on('research_progress', (data) => {
  console.log(data)
})

// Error notifications
socket.on('error', (data) => {
  console.error(data)
})
```

---

## Code Examples

### Python Client Example

```python
import requests
from typing import Dict, Any

class EnterpriseCIAClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate_impact_card(
        self,
        competitor: str,
        keywords: list[str] = None
    ) -> Dict[str, Any]:
        """Generate Impact Card for competitor"""
        response = requests.post(
            f"{self.base_url}/api/v1/impact/generate",
            json={
                "competitor": competitor,
                "keywords": keywords or []
            },
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def research_company(self, company_name: str) -> Dict[str, Any]:
        """Generate company research report"""
        response = requests.post(
            f"{self.base_url}/api/v1/research/company",
            json={"company_name": company_name},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = EnterpriseCIAClient(
    base_url="http://localhost:8765",
    api_key="your_jwt_token"
)

# Generate Impact Card
impact_card = client.generate_impact_card(
    competitor="OpenAI",
    keywords=["GPT", "ChatGPT"]
)
print(f"Risk Score: {impact_card['risk_score']}")

# Research company
research = client.research_company("Perplexity AI")
print(f"Total Sources: {research['total_sources']}")
```

### JavaScript/TypeScript Client Example

```typescript
import axios, { AxiosInstance } from 'axios'

interface ImpactCard {
  id: number
  competitor_name: string
  risk_score: number
  risk_level: string
  // ... other fields
}

class EnterpriseCIAClient {
  private client: AxiosInstance

  constructor(baseURL: string, apiKey: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    })
  }

  async generateImpactCard(
    competitor: string,
    keywords?: string[]
  ): Promise<ImpactCard> {
    const response = await this.client.post('/api/v1/impact/generate', {
      competitor,
      keywords: keywords || []
    })
    return response.data
  }

  async researchCompany(companyName: string) {
    const response = await this.client.post('/api/v1/research/company', {
      company_name: companyName
    })
    return response.data
  }
}

// Usage
const client = new EnterpriseCIAClient(
  'http://localhost:8765',
  'your_jwt_token'
)

// Generate Impact Card
const impactCard = await client.generateImpactCard(
  'OpenAI',
  ['GPT', 'ChatGPT']
)
console.log(`Risk Score: ${impactCard.risk_score}`)

// Research company
const research = await client.researchCompany('Perplexity AI')
console.log(`Total Sources: ${research.total_sources}`)
```

---

## Support & Documentation

- **Interactive API Docs**: http://localhost:8765/docs (FastAPI auto-generated)
- **GitHub Repository**: [Link to repository]
- **You.com API Docs**: https://documentation.you.com
- **Project Documentation**: [PROJECT_INDEX.md](PROJECT_INDEX.md)

---

**Last Updated**: October 31, 2025
