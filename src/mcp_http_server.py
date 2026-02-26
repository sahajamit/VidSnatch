#!/usr/bin/env python3
"""
VidSnatch MCP HTTP Server - Model Context Protocol server with HTTP transport and SSE streaming
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from .mcp_config import load_config, ensure_download_directory
from .mcp_tools import MCPTools


class MCPRequest(BaseModel):
    """MCP request model"""
    jsonrpc: str = "2.0"
    id: Optional[str | int] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP response model"""
    jsonrpc: str = "2.0"
    id: Optional[str | int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class MCPHTTPServer:
    """HTTP-based MCP server with SSE streaming support"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = logging.getLogger("vidsnatch-mcp-http")
        
        # Setup logging for HTTP mode (can use normal logging)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        ensure_download_directory(self.config)
        self.tools = MCPTools(self.config, self.logger)
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="VidSnatch MCP HTTP Server",
            description="HTTP transport for VidSnatch MCP server with SSE streaming",
            version="1.0.0"
        )
        
        # Add CORS middleware if enabled
        if self.config.get("http_transport", {}).get("enable_cors", True):
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=False,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
            )
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup HTTP routes for MCP protocol"""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server info"""
            return {
                "name": "VidSnatch MCP HTTP Server",
                "version": "1.0.0",
                "description": "HTTP transport for VidSnatch MCP server",
                "mcp_endpoint": "/mcp",
                "transport": "http",
                "streaming_supported": True
            }
        
        @self.app.post("/mcp")
        async def mcp_endpoint(request: MCPRequest):
            """Main MCP communication endpoint"""
            try:
                self.logger.info(f"MCP Request: {request.method}")
                
                # Handle different MCP methods
                if request.method == "initialize":
                    return await self.handle_initialize(request)
                elif request.method == "tools/list":
                    return await self.handle_tools_list(request)
                elif request.method == "tools/call":
                    return await self.handle_tools_call(request)
                else:
                    return MCPResponse(
                        id=request.id,
                        error={
                            "code": -32601,
                            "message": f"Method not found: {request.method}"
                        }
                    ).dict()
                    
            except Exception as e:
                self.logger.error(f"MCP endpoint error: {str(e)}")
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                ).dict()
        
        @self.app.get("/mcp")
        async def mcp_notifications():
            """SSE endpoint for server notifications (optional)"""
            return StreamingResponse(
                self.notification_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
    
    async def handle_initialize(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return MCPResponse(
            id=request.id,
            result={
                "protocolVersion": "2025-06-18",
                "capabilities": {
                    "tools": {},
                    "notifications": {},
                    "streaming": True
                },
                "serverInfo": {
                    "name": "vidsnatch-http",
                    "version": "1.0.0"
                }
            }
        ).dict()
    
    async def handle_tools_list(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools_list = [
            {
                "name": "get_video_info",
                "description": "Get detailed information about a YouTube video",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "YouTube video URL or video ID"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "download_video",
                "description": "Download a YouTube video",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "YouTube video URL or video ID"},
                        "quality": {"type": "string", "description": "Video quality", "default": "highest"},
                        "resolution": {"type": "string", "description": "Specific resolution (optional)"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "download_audio",
                "description": "Download audio from a YouTube video",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "YouTube video URL or video ID"},
                        "quality": {"type": "string", "description": "Audio quality", "default": "highest"},
                        "format": {"type": "string", "description": "Audio format", "default": "mp3"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "download_transcript",
                "description": "Download transcript from a YouTube video",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "YouTube video URL or video ID"},
                        "language": {"type": "string", "description": "Language code", "default": "en"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "download_video_segment",
                "description": "Download a specific segment from a YouTube video",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "YouTube video URL or video ID"},
                        "start_time": {"type": "number", "description": "Start time in seconds"},
                        "end_time": {"type": "number", "description": "End time in seconds"},
                        "quality": {"type": "string", "description": "Video quality", "default": "highest"}
                    },
                    "required": ["url", "start_time", "end_time"]
                }
            },
            {
                "name": "list_downloads",
                "description": "List all files in the download directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "search_videos",
                "description": "Search YouTube for videos matching a query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query string"},
                        "sort_by": {
                            "type": "string",
                            "description": "Sort order: relevance, date, or views",
                            "default": "relevance",
                            "enum": ["relevance", "date", "views"]
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_config",
                "description": "Get current server configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        return MCPResponse(
            id=request.id,
            result={"tools": tools_list}
        ).dict()
    
    async def handle_tools_call(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tools/call request with optional streaming"""
        if not request.params:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": "Missing params"}
            ).dict()
        
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        if not tool_name:
            return MCPResponse(
                id=request.id,
                error={"code": -32602, "message": "Missing tool name"}
            ).dict()
        
        # Check if streaming is requested and supported for this tool
        streaming_tools = ["download_video", "download_audio", "download_transcript", "download_video_segment"]
        should_stream = (
            self.config.get("http_transport", {}).get("stream_downloads", True) and
            tool_name in streaming_tools
        )
        
        if should_stream:
            # Return streaming response
            return StreamingResponse(
                self.stream_tool_execution(request.id, tool_name, arguments),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # Return regular JSON response
            try:
                result = await self.execute_tool(tool_name, arguments)
                return MCPResponse(id=request.id, result={"content": [{"type": "text", "text": result}]}).dict()
            except Exception as e:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32603, "message": str(e)}
                ).dict()
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result"""
        if tool_name == "get_video_info":
            return self.tools.get_video_info(arguments.get("url"))
        elif tool_name == "download_video":
            return self.tools.download_video(
                arguments.get("url"),
                arguments.get("quality", "highest"),
                arguments.get("resolution")
            )
        elif tool_name == "download_audio":
            return self.tools.download_audio(
                arguments.get("url"),
                arguments.get("quality", "highest"),
                arguments.get("format", "mp3")
            )
        elif tool_name == "download_transcript":
            return self.tools.download_transcript(
                arguments.get("url"),
                arguments.get("language", "en")
            )
        elif tool_name == "download_video_segment":
            return self.tools.download_video_segment(
                arguments.get("url"),
                arguments.get("start_time"),
                arguments.get("end_time"),
                arguments.get("quality", "highest")
            )
        elif tool_name == "list_downloads":
            return self.tools.list_downloads()
        elif tool_name == "search_videos":
            return self.tools.search_videos(
                arguments.get("query"),
                arguments.get("sort_by", "relevance")
            )
        elif tool_name == "get_config":
            return self.tools.get_config()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def stream_tool_execution(
        self, 
        request_id: Optional[str], 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Stream tool execution with progress updates"""
        
        progress_updates = []
        
        def progress_callback(update: Dict[str, Any]):
            progress_updates.append(update)
        
        try:
            # Execute tool with progress callback in thread pool (avoid blocking async generator)
            loop = asyncio.get_event_loop()
            
            # Start the tool execution in background
            if tool_name == "download_video":
                task = loop.run_in_executor(
                    None,
                    lambda: self.tools.download_video(
                        arguments.get("url"),
                        arguments.get("quality", "highest"),
                        arguments.get("resolution"),
                        progress_callback
                    )
                )
            elif tool_name == "download_audio":
                task = loop.run_in_executor(
                    None,
                    lambda: self.tools.download_audio(
                        arguments.get("url"),
                        arguments.get("quality", "highest"),
                        arguments.get("format", "mp3"),
                        progress_callback
                    )
                )
            elif tool_name == "download_transcript":
                task = loop.run_in_executor(
                    None,
                    lambda: self.tools.download_transcript(
                        arguments.get("url"),
                        arguments.get("language", "en"),
                        progress_callback
                    )
                )
            elif tool_name == "download_video_segment":
                task = loop.run_in_executor(
                    None,
                    lambda: self.tools.download_video_segment(
                        arguments.get("url"),
                        arguments.get("start_time"),
                        arguments.get("end_time"),
                        arguments.get("quality", "highest"),
                        progress_callback
                    )
                )
            else:
                raise ValueError(f"Streaming not supported for tool: {tool_name}")
            
            # Wait for completion (don't send progress updates as they close the connection)
            result = await task
            
            # Send final result
            final_response = MCPResponse(
                id=request_id,
                result={"content": [{"type": "text", "text": result}]}
            )
            yield f"data: {json.dumps(final_response.dict())}\n\n"
            
        except Exception as e:
            error_response = MCPResponse(
                id=request_id,
                error={"code": -32603, "message": str(e)}
            )
            yield f"data: {json.dumps(error_response.dict())}\n\n"
    
    async def notification_stream(self) -> AsyncGenerator[str, None]:
        """Generate server-sent events for notifications"""
        # This is a placeholder for server notifications
        # In a real implementation, you might want to send periodic status updates
        while True:
            await asyncio.sleep(30)  # Send a heartbeat every 30 seconds
            heartbeat = {"type": "heartbeat", "timestamp": asyncio.get_event_loop().time()}
            yield f"data: {json.dumps(heartbeat)}\n\n"


def main(host=None, port=None):
    """Main entry point for HTTP MCP server"""
    import uvicorn

    server = MCPHTTPServer()

    # Get HTTP configuration, CLI args override config values
    http_config = server.config.get("http_transport", {})
    host = host or http_config.get("host", "0.0.0.0")
    port = port or http_config.get("port", 8090)
    
    server.logger.info(f"🚀 Starting VidSnatch MCP HTTP server...")
    server.logger.info(f"📡 MCP endpoint: http://{host}:{port}/mcp")
    server.logger.info(f"📊 Server info: http://{host}:{port}/")
    server.logger.info(f"🔄 Streaming: {'enabled' if http_config.get('stream_downloads', True) else 'disabled'}")
    
    uvicorn.run(
        server.app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
