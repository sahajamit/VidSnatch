#!/usr/bin/env python3
"""
Development server runner for VidSnatch
"""

import uvicorn
from web_app import app

if __name__ == "__main__":
    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
