# Enterprise CIA - Quick Start Implementation Guide

**48-Hour Hackathon Build Guide**

---

## Pre-Build Checklist

### **Environment Setup**

- [ ] You.com API credentials obtained
- [ ] Development environment (Node.js 18+, Python 3.11+)
- [ ] Code editor (VS Code recommended)
- [ ] Git repository initialized
- [ ] Docker installed (optional but recommended)

### **API Access**

1. **Sign up at You.com Developer Portal**
2. **Obtain API keys for:**
   - News API
   - Search API
   - Custom Agents API
   - Chat/ARI API

3. **Create `.env` file:**
```bash
YOU_API_KEY=your_api_key_here
YOU_NEWS_ENDPOINT=https://api.you.com/news
YOU_SEARCH_ENDPOINT=https://api.you.com/search
YOU_AGENTS_ENDPOINT=https://api.you.com/agents
YOU_ARI_ENDPOINT=https://api.you.com/chat

DATABASE_URL=postgresql://localhost/cia_dev
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_secret_key
```

---

## Hour-by-Hour Implementation

### **Hours 1-4: Project Foundation**

#### **Backend Setup (Python + FastAPI)**

```bash
# Create project structure
mkdir cia-backend && cd cia-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic python-dotenv requests spacy

# Download NER model
python -m spacy download en_core_web_sm
```

**File: `backend/app/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Enterprise CIA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Enterprise CIA API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Run:** `uvicorn app.main:app --reload`

---

#### **Frontend Setup (Next.js + Tailwind)**

```bash
# Create Next.js app
npx create-next-app@latest cia-frontend --typescript --tailwind --app
cd cia-frontend

# Install dependencies
npm install @tanstack/react-query axios socket.io-client recharts lucide-react
```

**File: `frontend/src/app/page.tsx`**
```tsx
export default function Home() {
  return (
    <div className="min-h-screen p-8">
      <h1 className="text-3xl font-bold">Enterprise CIA</h1>
      <p className="mt-4 text-gray-600">
        Competitive Intelligence Agent - Powered by You.com
      </p>
    </div>
  );
}
```

**Run:** `npm run dev`

---

### **Hours 5-8: Watchlist Management**

#### **Backend: Database Models**

**File: `backend/app/models/watch.py`**
```python
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.database import Base

class WatchItem(Base):
    __tablename__ = "watch_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String)  # company, product, market, regulation
    name = Column(String, nullable=False)
    keywords = Column(JSON)  # List of keywords
    domains = Column(JSON)  # List of domains
    priority = Column(String)  # high, medium, low
    owners = Column(JSON)  # List of email addresses
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### **Backend: CRUD Endpoints**

**File: `backend/app/api/watch.py`**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.watch import WatchItem
from app.schemas.watch import WatchItemCreate, WatchItemResponse

router = APIRouter(prefix="/api/watch", tags=["watch"])

@router.get("/", response_model=List[WatchItemResponse])
def list_watch_items(db: Session = Depends(get_db)):
    return db.query(WatchItem).filter(WatchItem.is_active == True).all()

@router.post("/", response_model=WatchItemResponse)
def create_watch_item(item: WatchItemCreate, db: Session = Depends(get_db)):
    db_item = WatchItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

#### **Frontend: Watchlist Component**

**File: `frontend/src/components/WatchList.tsx`**
```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import axios from "axios";

interface WatchItem {
  id: string;
  name: string;
  type: string;
  priority: string;
  keywords: string[];
}

export function WatchList() {
  const { data: watchItems, isLoading } = useQuery({
    queryKey: ["watchItems"],
    queryFn: async () => {
      const response = await axios.get("http://localhost:8000/api/watch");
      return response.data as WatchItem[];
    },
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Watchlist</h2>
      <div className="space-y-3">
        {watchItems?.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between p-3 border rounded"
          >
            <div>
              <h3 className="font-medium">{item.name}</h3>
              <p className="text-sm text-gray-500">{item.type}</p>
            </div>
            <span
              className={`px-2 py-1 text-xs rounded ${
                item.priority === "high"
                  ? "bg-red-100 text-red-700"
                  : "bg-yellow-100 text-yellow-700"
              }`}
            >
              {item.priority}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

### **Hours 9-12: News Ingestion**

#### **Backend: You.com News API Client**

**File: `backend/app/services/you_client.py`**
```python
import os
import requests
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class YouComClient:
    def __init__(self):
        self.api_key = os.getenv("YOU_API_KEY")
        self.news_endpoint = os.getenv("YOU_NEWS_ENDPOINT")
        self.search_endpoint = os.getenv("YOU_SEARCH_ENDPOINT")

    def fetch_news(self, keywords: List[str], max_results: int = 20) -> List[Dict]:
        """Fetch news from You.com News API"""
        try:
            query = " OR ".join(keywords)
            response = requests.get(
                f"{self.news_endpoint}/search",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "q": query,
                    "max_results": max_results,
                    "language": "en"
                },
                timeout=10
            )
            response.raise_for_status()

            # Log API call for proof
            logger.info({
                "you_api": "news",
                "endpoint": "/search",
                "status": response.status_code,
                "latency_ms": response.elapsed.total_seconds() * 1000
            })

            return response.json().get("articles", [])

        except Exception as e:
            logger.error(f"News API error: {e}")
            return []

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search using You.com Search API"""
        try:
            response = requests.get(
                f"{self.search_endpoint}/web",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"q": query, "top_k": top_k},
                timeout=10
            )
            response.raise_for_status()

            logger.info({
                "you_api": "search",
                "endpoint": "/web",
                "status": response.status_code,
                "latency_ms": response.elapsed.total_seconds() * 1000
            })

            return response.json().get("results", [])

        except Exception as e:
            logger.error(f"Search API error: {e}")
            return []
```

#### **Backend: News Ingestion Worker**

**File: `backend/app/workers/ingest.py`**
```python
import spacy
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.watch import WatchItem
from app.models.news import NewsItem
from app.services.you_client import YouComClient

nlp = spacy.load("en_core_web_sm")

def ingest_news():
    """Worker function to ingest news for all active watchlists"""
    db = SessionLocal()
    you_client = YouComClient()

    try:
        # Get active watchlists
        watchlists = db.query(WatchItem).filter(WatchItem.is_active == True).all()

        for watch in watchlists:
            # Fetch news for this watchlist
            articles = you_client.fetch_news(watch.keywords)

            for article in articles:
                # Extract entities
                doc = nlp(article["title"] + " " + article.get("snippet", ""))
                entities = [
                    {"type": ent.label_, "text": ent.text}
                    for ent in doc.ents
                    if ent.label_ in ["ORG", "PRODUCT", "PERSON"]
                ]

                # Check if matches watchlist
                if matches_watch(entities, watch):
                    # Create NewsItem
                    news_item = NewsItem(
                        watch_id=watch.id,
                        source=article.get("source", "Unknown"),
                        title=article["title"],
                        url=article["url"],
                        raw_text=article.get("content", ""),
                        entities=entities,
                        is_breaking=article.get("is_breaking", False),
                        published_at=article.get("published_at")
                    )
                    db.add(news_item)

        db.commit()

    finally:
        db.close()

def matches_watch(entities, watch_item):
    """Check if entities match watchlist keywords"""
    for entity in entities:
        if entity["text"].lower() in [k.lower() for k in watch_item.keywords]:
            return True
    return False
```

---

### **Hours 13-16: Frontend News Feed**

**File: `frontend/src/components/NewsFeed.tsx`**
```tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Badge } from "@/components/ui/badge";

interface NewsItem {
  id: string;
  title: string;
  source: string;
  published_at: string;
  url: string;
  sentiment: number;
  is_breaking: boolean;
}

export function NewsFeed({ watchId }: { watchId?: string }) {
  const { data: newsItems } = useQuery({
    queryKey: ["news", watchId],
    queryFn: async () => {
      const params = watchId ? `?watch_id=${watchId}` : "";
      const response = await axios.get(`http://localhost:8000/api/news${params}`);
      return response.data as NewsItem[];
    },
    refetchInterval: 30000, // Refresh every 30s
  });

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">News Feed</h2>
        <Badge variant="outline">Live</Badge>
      </div>

      <div className="space-y-4">
        {newsItems?.map((item) => (
          <div
            key={item.id}
            className="p-4 border rounded-lg hover:bg-gray-50 transition"
          >
            {item.is_breaking && (
              <Badge className="mb-2 bg-red-500">BREAKING</Badge>
            )}

            <h3 className="font-medium mb-1">
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-blue-600"
              >
                {item.title}
              </a>
            </h3>

            <div className="flex items-center gap-3 text-sm text-gray-500">
              <span>{item.source}</span>
              <span>•</span>
              <span>{new Date(item.published_at).toLocaleString()}</span>
              <span>•</span>
              <SentimentBadge sentiment={item.sentiment} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SentimentBadge({ sentiment }: { sentiment: number }) {
  if (sentiment > 0.2) {
    return <Badge className="bg-green-500">Positive</Badge>;
  } else if (sentiment < -0.2) {
    return <Badge className="bg-red-500">Negative</Badge>;
  }
  return <Badge variant="secondary">Neutral</Badge>;
}
```

---

### **Hours 17-24: Sentiment & Search Integration**

#### **Backend: Basic Sentiment Analysis**

**File: `backend/app/services/sentiment.py`**
```python
def analyze_sentiment(text: str) -> float:
    """Simple keyword-based sentiment analysis
    Returns: -1.0 (very negative) to 1.0 (very positive)
    """
    positive_words = [
        "success", "growth", "profit", "gain", "positive", "up",
        "increase", "strong", "win", "breakthrough", "innovation"
    ]
    negative_words = [
        "loss", "decline", "failure", "down", "negative", "weak",
        "decrease", "problem", "issue", "concern", "risk", "threat"
    ]

    text_lower = text.lower()

    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    total = pos_count + neg_count
    if total == 0:
        return 0.0

    return (pos_count - neg_count) / total
```

---

### **Hours 25-28: Custom Agent Integration**

#### **Backend: Impact Extraction Service**

**File: `backend/app/services/extraction.py`**
```python
import requests
import os
from typing import Dict

class ExtractionService:
    def __init__(self):
        self.agents_endpoint = os.getenv("YOU_AGENTS_ENDPOINT")
        self.api_key = os.getenv("YOU_API_KEY")

    def extract_impact(self, news_item: Dict, watch_item: Dict, context_docs: list) -> Dict:
        """Extract competitive impact using You.com Custom Agent"""

        prompt = f"""
System: You are an enterprise competitive intelligence extraction agent.

Analyze the following news and extract structured intelligence:

News: {news_item['title']}
Content: {news_item['raw_text']}
Watch Keywords: {', '.join(watch_item['keywords'])}

Context Docs:
{self._format_context(context_docs)}

Extract in JSON format:
{{
  "event_type": "product_launch|pricing_change|partnership|regulatory_action",
  "affected_products": ["list of our products affected"],
  "impact_axes": [
    {{"axis": "market|product|regulatory", "level": "high|medium|low", "rationale": "explanation"}}
  ],
  "recommended_actions": [
    {{"owner": "PM|Marketing|Legal", "action": "specific task", "due_days": 1-7, "priority": "high|medium|low"}}
  ],
  "sources": [{{"title": "...", "url": "..."}}],
  "confidence": 0.0-1.0
}}
"""

        try:
            response = requests.post(
                f"{self.agents_endpoint}/run",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"prompt": prompt, "format": "json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Extraction error: {e}")
            return {"confidence": 0.0, "error": str(e)}

    def _format_context(self, docs: list) -> str:
        return "\n".join([f"- {doc['title']}: {doc['url']}" for doc in docs])
```

---

### **Hours 29-36: Impact Card Assembly & UI**

#### **Backend: Card Assembly Logic**

**File: `backend/app/services/assembly.py`**
```python
from sqlalchemy.orm import Session
from app.models.impact_card import ImpactCard
from app.models.extraction import ExtractionResult
import yaml

def assemble_impact_card(extraction: ExtractionResult, db: Session) -> ImpactCard:
    """Assemble an Impact Card from extraction results"""

    # Load rules
    with open("app/rules/rules.yaml") as f:
        rules = yaml.safe_load(f)

    # Apply rules
    risk_level = apply_rules(extraction, rules)

    # Create card
    card = ImpactCard(
        watch_id=extraction.watch_id,
        news_ids=[extraction.news_id],
        summary=generate_summary(extraction),
        risk_level=risk_level,
        impact_axes={
            axis["axis"]: axis["level"]
            for axis in extraction.impact_axes
        },
        actions=extraction.recommended_actions,
        evidence_sources=extraction.sources,
        confidence=extraction.confidence
    )

    db.add(card)
    db.commit()
    return card

def apply_rules(extraction: ExtractionResult, rules: list) -> str:
    """Apply rules DSL to determine risk level"""
    for rule in rules:
        if matches_rule(extraction, rule["when"]):
            return rule["then"]["risk_level"]
    return "low"

def matches_rule(extraction: ExtractionResult, conditions: dict) -> bool:
    """Check if extraction matches rule conditions"""
    if "event_type" in conditions:
        if extraction.event_type != conditions["event_type"]:
            return False
    # Add more condition matching logic
    return True

def generate_summary(extraction: ExtractionResult) -> str:
    """Generate human-readable summary"""
    return f"Impact detected: {extraction.event_type}"
```

#### **Frontend: Impact Card Component**

**File: `frontend/src/components/ImpactCard.tsx`**
```tsx
"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronDown, ExternalLink } from "lucide-react";
import { useState } from "react";

interface ImpactCard {
  id: string;
  summary: string;
  risk_level: "high" | "medium" | "low";
  impact_axes: Record<string, string>;
  actions: Array<{
    owner: string;
    title: string;
    priority: string;
    status: string;
  }>;
  evidence_sources: Array<{
    title: string;
    url: string;
  }>;
}

export function ImpactCard({ card }: { card: ImpactCard }) {
  const [showEvidence, setShowEvidence] = useState(false);

  const riskColor = {
    high: "bg-red-500",
    medium: "bg-yellow-500",
    low: "bg-green-500",
  };

  return (
    <div className="bg-white border rounded-lg p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold mb-2">{card.summary}</h3>
          <Badge className={riskColor[card.risk_level]}>
            {card.risk_level.toUpperCase()} RISK
          </Badge>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleDeepDive(card.id)}
        >
          Deep Dive
        </Button>
      </div>

      {/* Impact Axes */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        {Object.entries(card.impact_axes).map(([axis, level]) => (
          <div key={axis} className="text-center p-3 bg-gray-50 rounded">
            <div className="text-xs text-gray-500 uppercase">{axis}</div>
            <div className="font-semibold">{level}</div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="mb-4">
        <h4 className="text-sm font-medium mb-2">Recommended Actions</h4>
        <ul className="space-y-2">
          {card.actions.map((action, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-1" />
              <div>
                <span className="font-medium">{action.owner}:</span>{" "}
                {action.title}
                <Badge variant="outline" className="ml-2">
                  {action.priority}
                </Badge>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Evidence */}
      <div>
        <button
          onClick={() => setShowEvidence(!showEvidence)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <ChevronDown
            className={`w-4 h-4 transition-transform ${
              showEvidence ? "rotate-180" : ""
            }`}
          />
          Evidence ({card.evidence_sources.length} sources)
        </button>

        {showEvidence && (
          <ul className="mt-2 space-y-1 ml-6">
            {card.evidence_sources.map((source, i) => (
              <li key={i}>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                >
                  {source.title}
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function handleDeepDive(cardId: string) {
  // Trigger ARI deep dive
  console.log("Triggering deep dive for card:", cardId);
}
```

---

### **Hours 37-40: ARI Deep Research**

#### **Backend: ARI Service**

**File: `backend/app/services/ari_service.py`**
```python
import requests
import os
from typing import Dict

class ARIService:
    def __init__(self):
        self.ari_endpoint = os.getenv("YOU_ARI_ENDPOINT")
        self.api_key = os.getenv("YOU_API_KEY")

    def generate_report(self, impact_card: Dict, watch_item: Dict) -> Dict:
        """Generate deep research report using You.com ARI"""

        query = f"""
Generate a comprehensive competitive intelligence report on {watch_item['name']}.

Context: {impact_card['summary']}

Required sections:
1. Product Overview
2. Market Positioning
3. Pricing Strategy
4. Customer Sentiment
5. Competitive Threats
6. Recommendations

Include 400+ sources and direct citations.
"""

        try:
            response = requests.post(
                f"{self.ari_endpoint}/research",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "query": query,
                    "format": "pdf",
                    "sources": 400
                },
                timeout=180  # 3 minutes
            )
            response.raise_for_status()

            return {
                "status": "ready",
                "url": response.json()["report_url"],
                "source_count": response.json()["source_count"]
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}
```

---

### **Hours 41-44: Polish & Testing**

#### **Seed Data Script**

**File: `scripts/seed_watch.py`**
```python
from app.database import SessionLocal
from app.models.watch import WatchItem

db = SessionLocal()

watchlists = [
    WatchItem(
        type="company",
        name="Acme Corp",
        keywords=["Acme", "Acme Cloud", "Feature Y", "pricing"],
        domains=["acme.com"],
        priority="high",
        owners=["pm@company.com"]
    ),
    WatchItem(
        type="market",
        name="Data Privacy Regulations",
        keywords=["GDPR", "data retention", "privacy fines"],
        domains=["gdpr.eu"],
        priority="medium",
        owners=["legal@company.com"]
    )
]

for watch in watchlists:
    db.add(watch)

db.commit()
print("Watchlist seeded!")
```

---

### **Hours 45-48: Demo Recording**

#### **Demo Checklist**

- [ ] All APIs functioning correctly
- [ ] Seed data loaded
- [ ] UI polished and responsive
- [ ] Network tab showing API calls
- [ ] Screen recording software ready
- [ ] Microphone tested
- [ ] Demo script rehearsed 3+ times
- [ ] Backup screenshots prepared

#### **README Template**

```markdown
# Enterprise Competitive Intelligence Agent (CIA)

## What It Does
Automated competitive monitoring and intelligence using You.com's APIs.

## You.com APIs Used
1. **News API** - Real-time news monitoring
2. **Search API** - Context enrichment
3. **Custom Agents** - Impact extraction
4. **ARI/Chat** - Deep research reports

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Seed Data
```bash
python scripts/seed_watch.py
```

## API Usage Proof
Visit http://localhost:3000/api-usage to see all You.com API calls logged.

## Demo Video
[Link to 3-minute demo video]

## Architecture
```
News API → Search API → Custom Agent → Impact Card
                              ↓
                           ARI → Deep Report
```

## Team
[Your name and contact]
```

---

## Common Issues & Solutions

### **Issue: You.com API Rate Limits**
**Solution:** Implement exponential backoff and caching
```python
import time
from functools import wraps

def rate_limit_retry(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        wait = 2 ** attempt
                        time.sleep(wait)
                    else:
                        raise
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator
```

### **Issue: Slow News Ingestion**
**Solution:** Use background workers
```python
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def ingest_news_task():
    ingest_news()

# Schedule every 30 seconds
from celery.schedules import crontab
app.conf.beat_schedule = {
    'ingest-news': {
        'task': 'tasks.ingest_news_task',
        'schedule': 30.0,
    },
}
```

### **Issue: Frontend CORS Errors**
**Solution:** Configure FastAPI CORS properly
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Performance Optimization

### **Database Indexing**
```sql
CREATE INDEX idx_news_watch_id ON news_items(watch_id);
CREATE INDEX idx_news_published_at ON news_items(published_at DESC);
CREATE INDEX idx_impact_risk ON impact_cards(risk_level);
```

### **Frontend Caching**
```tsx
const { data } = useQuery({
  queryKey: ["news"],
  queryFn: fetchNews,
  staleTime: 30000, // 30 seconds
  cacheTime: 3600000, // 1 hour
});
```

---

## Final Pre-Submission Checklist

- [ ] All 4 You.com APIs integrated
- [ ] API usage logging implemented
- [ ] Clean, responsive UI
- [ ] Demo video recorded (< 3 minutes)
- [ ] README complete with setup instructions
- [ ] GitHub repository public
- [ ] Devpost submission filled out
- [ ] Architecture diagram included
- [ ] Source code commented
- [ ] No API keys committed to repo

---

## Resources

- [You.com API Docs](https://docs.you.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Devpost Submission Tips](https://info.devpost.com)

---

**Good luck with your hackathon submission!**
