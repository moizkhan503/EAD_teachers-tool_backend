"""
Main FastAPI application module.
"""
import logging
import logging.config
import time
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.api import endpoints as api_endpoints

# Configure logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': settings.LOG_LEVEL,
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': settings.LOG_LEVEL,
            'propagate': True
        },
    }
})

logger = logging.getLogger(__name__)

# Middleware for request timing
class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

# Initialize FastAPI application with middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    ),
    Middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else ["yourdomain.com"],  # In production, replace with your domain
    ),
    Middleware(ProcessTimeMiddleware),
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for curriculum planning using RAG with Qdrant and Groq",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    middleware=middleware,
)

# Add GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Redirect HTTP to HTTPS in production
if not settings.DEBUG and settings.ENV == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Include API routers
app.include_router(
    api_endpoints.router,
    prefix="/api",
    tags=["API"]
)

# Health check endpoint
@app.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
async def root():
    """Root endpoint for health checks."""
    return {
        "status": "running",
        "name": settings.PROJECT_NAME,
        "version": "0.1.0"
    }

# Exception handlers
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    """Handle 404 Not Found errors."""
    return {
        "success": False,
        "error": "Not Found",
        "message": "The requested resource was not found"
    }

@app.exception_handler(500)
async def server_error_exception_handler(request, exc):
    """Handle 500 Internal Server errors."""
    logger.error(f"Server error: {str(exc)}")
    return {
        "success": False,
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Run application startup tasks."""
    logger.info("Starting up Curriculum Planning API...")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info("Startup complete")

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run application shutdown tasks."""
    logger.info("Shutting down Curriculum Planning API...")
    # Add any cleanup tasks here
    logger.info("Shutdown complete")
