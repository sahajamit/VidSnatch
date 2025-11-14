# VidSnatch MCP HTTP Transport

VidSnatch now supports **streamable HTTP transport** in addition to the original stdio transport, enabling remote MCP server deployment and web-based integrations.

## Overview

The HTTP transport implements the modern MCP standard for remote communication:
- **Single `/mcp` endpoint** for all MCP communication
- **Server-Sent Events (SSE)** streaming for long-running operations
- **CORS support** for web-based clients
- **Remote deployment** capabilities

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  HTTP Transport │    │  Shared Tools   │
│  (Claude, etc.) │◄──►│   mcp_http_     │◄──►│   mcp_tools.py  │
│                 │    │   server.py     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Configuration  │
                       │  mcp_config.py  │
                       └─────────────────┘
```

## Quick Start

### 1. Start HTTP MCP Server

```bash
# Using Python directly
python3 mcp_http_server.py

# Using entry point (after installation)
vidsnatch-mcp-http
```

The server will start on `http://0.0.0.0:8090` by default.

### 2. Test the Server

```bash
# Check server info
curl http://localhost:8090/

# Initialize MCP connection
curl -X POST http://localhost:8090/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'

# List available tools
curl -X POST http://localhost:8090/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/list"
  }'
```

## Configuration

Configure HTTP transport in `mcp_config.json`:

```json
{
  "download_directory": "./downloads",
  "default_video_quality": "highest",
  "default_audio_quality": "highest",
  "max_file_size_mb": 500,
  "allowed_formats": ["mp4", "webm", "mp3", "m4a"],
  "create_subdirs": true,
  "http_transport": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8090,
    "enable_cors": true,
    "stream_downloads": true
  }
}
```

### Environment Variables

Override configuration with environment variables:

```bash
export VIDSNATCH_HTTP_HOST="127.0.0.1"
export VIDSNATCH_HTTP_PORT="8091"
export VIDSNATCH_HTTP_ENABLE_CORS="true"
export VIDSNATCH_HTTP_STREAM_DOWNLOADS="false"
```

## HTTP Endpoints

### Root Endpoint
- **GET** `/` - Server information and status

### MCP Protocol Endpoint
- **POST** `/mcp` - Main MCP communication endpoint
- **GET** `/mcp` - Server-sent events stream for notifications

## MCP Protocol Support

### Supported Methods

1. **initialize** - Initialize MCP connection
2. **tools/list** - List available tools
3. **tools/call** - Execute tools (with streaming support)

### Available Tools

1. **get_video_info** - Get YouTube video information
2. **download_video** - Download video (with streaming progress)
3. **download_audio** - Download audio (with streaming progress)
4. **download_transcript** - Download transcript (with streaming progress)
5. **download_video_segment** - Download video segment (with streaming progress)
6. **list_downloads** - List downloaded files
7. **get_config** - Get server configuration

## Streaming Downloads

For long-running operations (downloads), the server supports SSE streaming:

```bash
# This will return an SSE stream with progress updates
curl -X POST http://localhost:8090/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "3",
    "method": "tools/call",
    "params": {
      "name": "download_video",
      "arguments": {
        "url": "https://youtube.com/watch?v=VIDEO_ID",
        "quality": "720p"
      }
    }
  }'
```

Response format for streaming:
```
data: {"jsonrpc": "2.0", "id": "3", "result": {"streaming": true, "status": "started"}}

data: {"jsonrpc": "2.0", "id": "3", "result": {"progress": {"status": "starting", "message": "Starting video download...", "progress": 0}}}

data: {"jsonrpc": "2.0", "id": "3", "result": {"progress": {"status": "processing", "message": "Processing downloaded file...", "progress": 90}}}

data: {"jsonrpc": "2.0", "id": "3", "result": {"content": "{\"status\": \"success\", \"file_path\": \"./downloads/video.mp4\"}", "status": "completed"}}
```

## Claude Desktop Integration

### HTTP Transport Configuration

Create or update your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "vidsnatch-http": {
      "command": "python3",
      "args": ["/path/to/VidSnatch/mcp_http_server.py"],
      "env": {
        "VIDSNATCH_DOWNLOAD_DIR": "/Users/username/Downloads/VidSnatch",
        "VIDSNATCH_HTTP_PORT": "8090"
      }
    }
  }
}
```

### Remote Server Configuration

For a remote VidSnatch MCP server:

```json
{
  "mcpServers": {
    "vidsnatch-remote": {
      "transport": {
        "type": "http",
        "url": "http://your-server.com:8090/mcp"
      }
    }
  }
}
```

## Deployment

### Local Development
```bash
# Start HTTP server
python3 mcp_http_server.py
```

### Docker Deployment
```bash
# Build and run with HTTP transport
docker build -t vidsnatch .
docker run -p 8090:8090 -e MODE=http vidsnatch
```

### Production Deployment

For production deployment, consider:
- Using a reverse proxy (nginx)
- Adding authentication/authorization
- Implementing rate limiting
- Using HTTPS with SSL certificates

Example nginx configuration:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location /mcp {
        proxy_pass http://localhost:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE streaming support
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

## Comparison: stdio vs HTTP Transport

| Feature | stdio Transport | HTTP Transport |
|---------|----------------|----------------|
| **Deployment** | Local only | Local + Remote |
| **Streaming** | No | Yes (SSE) |
| **Web Integration** | No | Yes (CORS) |
| **Multiple Clients** | No | Yes |
| **Progress Updates** | No | Yes |
| **Network Overhead** | None | Minimal |
| **Security** | Process isolation | HTTP/network security |

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   export VIDSNATCH_HTTP_PORT="8091"
   python3 mcp_http_server.py
   ```

2. **CORS issues**
   ```json
   {"http_transport": {"enable_cors": true}}
   ```

3. **Connection refused**
   - Check if server is running: `curl http://localhost:8090/`
   - Verify port configuration
   - Check firewall settings

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

See the `examples/` directory for:
- Claude Desktop configurations
- Client integration examples
- Streaming download demos
- Remote deployment scripts

## API Reference

Complete MCP HTTP API documentation is available in the OpenAPI format at `/docs` when running the server (if enabled in development mode).
