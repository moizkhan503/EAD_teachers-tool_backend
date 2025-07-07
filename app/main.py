"""
Main FastAPI application module.
"""
import logging
import logging.config
import time
import traceback
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

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
    # Allow all hosts in production for Railway
    # You might want to restrict this to your domain in the future
    Middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    ),
    Middleware(ProcessTimeMiddleware),
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for curriculum planning using RAG with Qdrant and Groq",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    middleware=middleware,
)

# Add GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Redirect HTTP to HTTPS in production - Railway handles this automatically
# if not settings.DEBUG and settings.ENV == "production":
#     app.add_middleware(HTTPSRedirectMiddleware)

# Include API router
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
async def not_found_exception_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "The requested resource was not found."},
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server errors with detailed logging."""
    error_detail = {
        "error": str(exc),
        "type": exc.__class__.__name__,
        "path": request.url.path,
    }
    
    # Log the full traceback for debugging
    logger.error(
        f"Internal Server Error: {str(exc)}\n"
        f"Path: {request.url.path}\n"
        f"Traceback: {''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )

# Add validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Add HTTP exception handler
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

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
