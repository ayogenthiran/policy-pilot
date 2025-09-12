#!/usr/bin/env python3
"""
Development server startup script for Policy Pilot RAG Backend.
"""

import uvicorn
from src.config.settings import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info("Starting Policy Pilot RAG Backend development server...")
    
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True
    )
