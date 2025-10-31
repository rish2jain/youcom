# Youcom - Api Reference

**Pages:** 6

---

## Custom Agent (Beta)

**URL:** https://documentation.you.com/api-reference/custom-agents

**Examples:**

Example 1 (unknown):
```unknown
curl --request POST \
  --url https://api.you.com/v1/agents/runs \
  --header 'Authorization: <api-key>' \
  --header 'Content-Type: application/json' \
  --data '{
  "agent": "550e8400-e29b-41d4-a716-446655440000",
  "input": "Summarize today'\''s top AI research headlines and cite sources.",
  "stream": false
}'
```

---

## Express Agent (Beta)

**URL:** https://documentation.you.com/api-reference/express

**Examples:**

Example 1 (unknown):
```unknown
curl --request POST \
  --url https://api.you.com/v1/agents/runs \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '{
  "agent": "express",
  "input": "What is the capital of France?"
}'
```

---

## Search

**URL:** https://documentation.you.com/api-reference/search

**Examples:**

Example 1 (unknown):
```unknown
curl --request GET \
  --url https://api.ydc-index.io/v1/search \
  --header 'X-API-Key: <api-key>'
```

---

## MCP Server

**URL:** https://documentation.you.com/tools/mcp-server#you-search-tool

**Contents:**
- ​Introduction
- ​Quick Start
- Remote Server
- Local NPM Package
  - ​Prerequisites
  - ​Standard Configuration Templates
- ​Setup Guides
- ​Search Tool Reference
  - ​you-search Tool
- ​Advanced Configuration

Local Development Setup

IDE Integration Issues

**Examples:**

Example 1 (unknown):
```unknown
https://api.you.com/mcp
```

Example 2 (unknown):
```unknown
npx @youdotcom-oss/mcp
```

Example 3 (unknown):
```unknown
CopyAsk AI{
  "mcpServers": {
    "ydc-search": {
      "type": "http",
      "url": "https://api.you.com/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

Example 4 (unknown):
```unknown
{
  "mcpServers": {
    "ydc-search": {
      "type": "http",
      "url": "https://api.you.com/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

---

## MCP Server

**URL:** https://documentation.you.com/tools/mcp-server#search-tool-reference

**Contents:**
- ​Introduction
- ​Quick Start
- Remote Server
- Local NPM Package
  - ​Prerequisites
  - ​Standard Configuration Templates
- ​Setup Guides
- ​Search Tool Reference
  - ​you-search Tool
- ​Advanced Configuration

Local Development Setup

IDE Integration Issues

**Examples:**

Example 1 (unknown):
```unknown
https://api.you.com/mcp
```

Example 2 (unknown):
```unknown
npx @youdotcom-oss/mcp
```

Example 3 (unknown):
```unknown
CopyAsk AI{
  "mcpServers": {
    "ydc-search": {
      "type": "http",
      "url": "https://api.you.com/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

Example 4 (unknown):
```unknown
{
  "mcpServers": {
    "ydc-search": {
      "type": "http",
      "url": "https://api.you.com/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

---

## Live News

**URL:** https://documentation.you.com/api-reference/news

**Examples:**

Example 1 (unknown):
```unknown
curl --request GET \
  --url https://api.ydc-index.io/livenews \
  --header 'X-API-Key: <api-key>'
```

---
