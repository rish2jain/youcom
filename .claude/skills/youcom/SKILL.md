---
name: youcom
description: You.com API and platform documentation. Use for You.com search API, custom agents, MCP server integration, and AI-powered search functionality.
---

# You.com Skill

Comprehensive assistance with You.com development, focusing on search APIs, custom agents, and MCP server integration.

## When to Use This Skill

This skill should be triggered when:
- **Implementing You.com Search API** - Web search, news search, or real-time information retrieval
- **Building Custom Agents** - Creating AI agents with You.com's agent framework
- **Setting up MCP Server** - Integrating You.com search into Claude Desktop or other MCP clients
- **Using Express Agent** - Quick AI-powered responses for simple queries
- **Working with Live News API** - Fetching current news and events
- **Troubleshooting You.com integrations** - API errors, authentication issues, MCP configuration
- **Migrating from other search APIs** - Moving to You.com from alternatives

**Key Triggers**: MCP setup, search API calls, custom agent creation, news API, API key management

## Key Concepts

### Core Services
- **Search API** - Web search with structured results at `api.ydc-index.io`
- **Live News API** - Real-time news aggregation and filtering
- **Express Agent** - Fast AI responses for straightforward questions
- **Custom Agents** - Build specialized AI agents with custom behavior
- **MCP Server** - Model Context Protocol integration for AI assistants

### Authentication
All You.com APIs use API key authentication via:
- **Header**: `X-API-Key: YOUR_API_KEY` (Search/News APIs)
- **Header**: `Authorization: Bearer YOUR_API_KEY` (Agent APIs)

### MCP Integration
You.com provides both remote (hosted) and local (NPM) MCP server options for seamless integration with Claude Desktop and other MCP-compatible tools.

## Quick Reference

### 1. Basic Search API Call
```bash
curl --request GET \
  --url 'https://api.ydc-index.io/v1/search?query=artificial+intelligence' \
  --header 'X-API-Key: YOUR_API_KEY'
```
**Use when**: You need web search results with citations and structured data.

### 2. Live News API Query
```bash
curl --request GET \
  --url https://api.ydc-index.io/livenews \
  --header 'X-API-Key: YOUR_API_KEY'
```
**Use when**: Fetching current news, trending topics, or recent events.

### 3. Express Agent Simple Query
```bash
curl --request POST \
  --url https://api.you.com/v1/agents/runs \
  --header 'Authorization: Bearer YOUR_API_KEY' \
  --header 'Content-Type: application/json' \
  --data '{
  "agent": "express",
  "input": "What is the capital of France?"
}'
```
**Use when**: You need quick AI-powered answers without complex agent setup.

### 4. Custom Agent with Streaming
```bash
curl --request POST \
  --url https://api.you.com/v1/agents/runs \
  --header 'Authorization: Bearer YOUR_API_KEY' \
  --header 'Content-Type: application/json' \
  --data '{
  "agent": "550e8400-e29b-41d4-a716-446655440000",
  "input": "Summarize today'\''s top AI research headlines and cite sources.",
  "stream": false
}'
```
**Use when**: Running a custom agent you've created with specific capabilities.

### 5. MCP Server Configuration (Remote)
```json
{
  "mcpServers": {
    "ydc-search": {
      "type": "http",
      "url": "https://api.you.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```
**Use when**: Configuring Claude Desktop or other MCP clients to use You.com search remotely.

### 6. MCP Server Configuration (Local NPM)
```bash
npx @youdotcom-oss/mcp
```
**Configuration**:
```json
{
  "mcpServers": {
    "ydc-search": {
      "type": "stdio",
      "command": "npx",
      "args": ["@youdotcom-oss/mcp"],
      "env": {
        "YDC_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```
**Use when**: You want local control or offline development with the MCP server.

### 7. Setting API Key in Code
```python
YOUR_API_KEY = "your_actual_api_key_here"
```
**Use when**: Initializing API connections in your application code.

### 8. Error Response Format
```json
{"detail": "Invalid or expired API key"}
```
**Common error codes**:
- `bad_request` - Malformed request
- `{"detail": "API key is required"}` - Missing authentication
- `{"detail": "Invalid or expired API key"}` - Authentication failure

## Reference Files

This skill includes comprehensive documentation in `references/`:

### api_reference.md
**Focus**: API endpoints, request/response formats, authentication
**Contains**:
- Custom Agent API - Build and run specialized AI agents
- Express Agent API - Simple question-answering endpoint
- Search API - Web search with structured results
- Live News API - Real-time news aggregation
- MCP Server endpoints and tool reference

**Use when**: You need technical details about API endpoints, parameters, or response structures.

### getting_started.md
**Focus**: Quick start guides, initial setup, first API calls
**Contains**:
- Getting your API key from You.com dashboard
- Making your first API calls
- MCP server quick start and setup
- Basic authentication patterns
- Common integration patterns

**Use when**: Starting a new You.com integration or setting up for the first time.

### tools.md
**Focus**: MCP server setup, configuration, troubleshooting
**Contains**:
- Remote vs Local MCP server setup
- Configuration templates for Claude Desktop, Cursor, other MCP clients
- Advanced configuration options
- Transport protocols (HTTP vs stdio)
- Troubleshooting common issues
- IDE integration guides

**Use when**: Configuring MCP integration or debugging connection issues.

### developer_resources.md
**Focus**: Error handling, debugging, best practices
**Contains**:
- Complete error code reference
- Error response formats
- Debugging strategies
- API limitations and rate limits

**Use when**: Handling errors, debugging failed requests, or understanding API constraints.

## Working with This Skill

### For Beginners
1. **Start with `getting_started.md`** - Get your API key and make your first call
2. **Try Express Agent first** - Simplest way to get AI-powered responses
3. **Use the Quick Reference** - Copy-paste examples and modify for your use case
4. **Set up MCP** - If using Claude Desktop, follow the MCP configuration examples

### For Intermediate Users
1. **Explore Custom Agents** - Build specialized agents for specific tasks
2. **Integrate Search API** - Add web search capabilities to your applications
3. **Use Live News API** - Build news aggregation or monitoring features
4. **Review `api_reference.md`** - Deep dive into all available parameters and options

### For Advanced Users
1. **Review `tools.md`** - Advanced MCP configurations and custom transport protocols
2. **Implement error handling** - Use `developer_resources.md` for robust error management
3. **Optimize agent performance** - Streaming responses, custom prompts, agent configuration
4. **Build complex integrations** - Combine multiple You.com APIs for sophisticated workflows

### Navigation Tips
- **API endpoint questions** → `api_reference.md`
- **First-time setup** → `getting_started.md`
- **MCP configuration** → `tools.md`
- **Error debugging** → `developer_resources.md`
- **Quick code snippets** → Use Quick Reference section above

## Common Use Cases

### 1. Adding Web Search to an AI Application
Use the Search API to retrieve real-time web information for AI context enrichment.

### 2. Building a News Aggregator
Combine Live News API with filtering to create topic-specific news feeds.

### 3. Claude Desktop Integration
Set up the MCP server to give Claude Desktop access to You.com search capabilities.

### 4. Creating Domain-Specific AI Agents
Use Custom Agents API to build specialized assistants (e.g., legal research, medical information, technical support).

### 5. Real-Time Information Retrieval
Express Agent provides quick answers for time-sensitive queries without complex setup.

## Best Practices

### API Key Management
- **Never commit API keys** to version control
- **Use environment variables** for API key storage
- **Rotate keys regularly** for security
- **Use different keys** for development and production

### Error Handling
- **Always check response status** before processing data
- **Implement retry logic** for transient failures
- **Log errors** with context for debugging
- **Handle rate limits** gracefully with backoff strategies

### Performance Optimization
- **Use streaming** for Custom Agents when processing long responses
- **Cache search results** when appropriate to reduce API calls
- **Batch requests** when possible to minimize latency
- **Monitor usage** to stay within rate limits

## Troubleshooting

### MCP Server Connection Issues
1. Verify API key is correctly set in configuration
2. Check that URL is correct (`https://api.you.com/mcp` for remote)
3. Restart Claude Desktop after configuration changes
4. Review `tools.md` for transport protocol issues

### API Authentication Errors
1. Confirm API key is active in You.com dashboard
2. Check correct header format (X-API-Key vs Authorization Bearer)
3. Verify no extra spaces or characters in API key
4. Ensure API key has required permissions for the endpoint

### Search/Agent Response Issues
1. Check query formatting and encoding
2. Verify request payload structure matches API docs
3. Review error response details for specific issues
4. Consult `developer_resources.md` for error codes

## Resources

### Official Links
- **Documentation**: https://documentation.you.com
- **API Dashboard**: https://api.you.com (get API keys)
- **MCP GitHub**: https://github.com/youdotcom-oss/mcp

### Support
- Review error messages in `developer_resources.md`
- Check MCP troubleshooting in `tools.md`
- Consult API reference for endpoint-specific issues

## Notes

- You.com APIs are production-ready and actively maintained
- MCP server supports both HTTP (remote) and stdio (local) transports
- Custom Agents are in beta - expect continued feature development
- Search API provides citations and source attribution
- All examples use placeholder API keys - replace with your actual key

## Updating

To refresh this skill with updated documentation:
1. Re-run the documentation scraper with the same configuration
2. The skill will be rebuilt with the latest information from You.com
3. Review changelog for API updates or breaking changes
