"""
MasterProject API Application
FastAPI-based REST API with comprehensive observability features.
"""

import json
import logging
import random
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import JSONResponse

from config import settings

# Try to import database module (optional, graceful fallback)
try:
    from database import check_db_connection, init_db, get_products_by_category, get_product_by_id, count_products_by_category
    DATABASE_ENABLED = settings.DB_ENABLED
except ImportError:
    DATABASE_ENABLED = False

# Try to import cache module (optional, graceful fallback)
try:
    from cache import get_cache, set_cache, get_cache_stats, check_cache_connection, cache_metrics
    CACHE_ENABLED = settings.REDIS_ENABLED
except ImportError:
    CACHE_ENABLED = False

# Try to import X-Ray SDK (optional, graceful fallback)
try:
    from aws_xray_sdk.core import xray_recorder, patch_all
    from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware
    XRAY_ENABLED = True
    # Patch all supported libraries
    patch_all()
except ImportError:
    XRAY_ENABLED = False
    xray_recorder = None


# ============================================================================
# Structured JSON Logging
# ============================================================================
class JSONFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "path"):
            log_entry["path"] = record.path
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "client_ip"):
            log_entry["client_ip"] = record.client_ip
            
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)


# Configure logging
def setup_logging():
    """Configure structured JSON logging."""
    logger = logging.getLogger("masterproject")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with JSON formatting
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger


logger = setup_logging()


# ============================================================================
# Application Lifespan
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    logger.info("Application starting up", extra={"event": "startup"})
    
    # Check database connection
    if DATABASE_ENABLED:
        if check_db_connection():
            logger.info("Database connection established")
            init_db()  # Create tables if they don't exist
        else:
            logger.warning("Database connection failed, running without database")
    
    # Check cache connection
    if CACHE_ENABLED:
        if check_cache_connection():
            logger.info("Redis cache connection established")
        else:
            logger.warning("Redis connection failed, running without cache")
    
    yield
    logger.info("Application shutting down", extra={"event": "shutdown"})


# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title="MasterProject API",
    description="Simple REST API with comprehensive observability",
    version="1.0.0",
    lifespan=lifespan,
)


# Add X-Ray middleware if available
if XRAY_ENABLED:
    xray_recorder.configure(
        service=settings.SERVICE_NAME,
        sampling=True,
        context_missing='LOG_ERROR',
        daemon_address=settings.XRAY_DAEMON_ADDRESS,
    )
    app.add_middleware(XRayMiddleware, recorder=xray_recorder)
    logger.info("X-Ray tracing enabled")
else:
    logger.warning("X-Ray SDK not available, tracing disabled")


# ============================================================================
# Request/Response Middleware
# ============================================================================
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware for request/response logging with timing."""
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Process request
    try:
        response = await call_next(request)
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            f"Request failed: {str(e)}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else None,
            },
            exc_info=True,
        )
        raise
    
    # Calculate duration
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": request.client.host if request.client else None,
        },
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response


# ============================================================================
# API Endpoints
# ============================================================================
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON with health status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
    }


@app.get("/items")
async def get_items(
    request: Request,
    count: int = Query(default=10, ge=1, le=100, description="Number of items to return"),
):
    """
    Get a list of dummy items.
    
    Simulates business logic with random latency.
    
    Args:
        count: Number of items to generate (1-100)
        
    Returns:
        JSON array of dummy items
    """
    # Start X-Ray subsegment for business logic if enabled
    if XRAY_ENABLED and xray_recorder:
        subsegment = xray_recorder.begin_subsegment("business_logic")
    
    try:
        # Simulate business logic with random latency (50-200ms)
        latency_ms = random.randint(50, 200)
        time.sleep(latency_ms / 1000)
        
        # Generate dummy items
        items = []
        for i in range(count):
            items.append({
                "id": str(uuid.uuid4()),
                "name": f"Item {i + 1}",
                "description": f"This is a sample item number {i + 1}",
                "price": round(random.uniform(10.0, 100.0), 2),
                "category": random.choice(["electronics", "clothing", "books", "food"]),
                "in_stock": random.choice([True, False]),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        
        # Add metadata to subsegment
        if XRAY_ENABLED and xray_recorder and subsegment:
            subsegment.put_annotation("item_count", count)
            subsegment.put_metadata("simulated_latency_ms", latency_ms)
            
    finally:
        if XRAY_ENABLED and xray_recorder:
            xray_recorder.end_subsegment()
    
    return {
        "items": items,
        "count": len(items),
        "request_id": getattr(request.state, "request_id", None),
    }


@app.get("/error")
async def trigger_error(request: Request):
    """
    Intentional error endpoint for testing error handling.
    
    Returns:
        500 Internal Server Error with error details
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log error
    logger.error(
        "Intentional error triggered for testing",
        extra={
            "request_id": request_id,
            "path": "/error",
            "method": "GET",
        },
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Intentional error for testing purposes",
            "message": "This endpoint intentionally returns a 500 error",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    endpoints = {
        "health": "/health",
        "items": "/items?count=10",
        "error": "/error",
    }
    
    # Add Phase 3 endpoints if enabled
    if DATABASE_ENABLED:
        endpoints["products"] = "/products?category=electronics"
        endpoints["product_by_id"] = "/products/1"
    
    if CACHE_ENABLED:
        endpoints["cache_stats"] = "/cache/stats"
    
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "endpoints": endpoints,
        "documentation": "/docs",
        "features": {
            "database": DATABASE_ENABLED,
            "cache": CACHE_ENABLED,
            "xray": XRAY_ENABLED,
        },
    }


# ============================================================================
# Phase 3: Database Endpoints
# ============================================================================
if DATABASE_ENABLED:
    @app.get("/products")
    async def get_products(
        request: Request,
        category: Optional[str] = Query(None, description="Filter by category"),
        limit: int = Query(100, ge=1, le=1000, description="Max products to return"),
        offset: int = Query(0, ge=0, description="Offset for pagination"),
    ):
        """
        Get products from database with optional caching.
        
        Args:
            category: Filter by product category
            limit: Maximum number of products to return
            offset: Offset for pagination
            
        Returns:
            JSON array of products with caching metadata
        """
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.time()
        
        # Build cache key
        cache_key = f"products:category:{category or 'all'}:limit:{limit}:offset:{offset}"
        
        # Try cache first if enabled
        cached_result = None
        if CACHE_ENABLED:
            cached_result = get_cache(cache_key)
            if cached_result:
                logger.info(
                    f"Cache HIT for products query",
                    extra={
                        "request_id": request_id,
                        "cache_key": cache_key,
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                    },
                )
                return cached_result
        
        # Cache miss - query database
        try:
            if category:
                products = get_products_by_category(category, limit, offset)
                total_count = count_products_by_category(category)
            else:
                # Get all products (no category filter)
                products = get_products_by_category(None, limit, offset)
                total_count = count_products_by_category(None)
            
            result = {
                "products": products,
                "count": len(products),
                "total": total_count,
                "category": category,
                "limit": limit,
                "offset": offset,
                "request_id": request_id,
                "cached": False,
            }
            
            # Store in cache (2 minute TTL)
            if CACHE_ENABLED:
                set_cache(cache_key, result, ttl=120)
            
            logger.info(
                f"Database query for products",
                extra={
                    "request_id": request_id,
                    "category": category,
                    "count": len(products),
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                },
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error querying products: {e}", extra={"request_id": request_id})
            return JSONResponse(
                status_code=500,
                content={"error": "Database query failed", "request_id": request_id},
            )
    
    @app.get("/products/{product_id}")
    async def get_product(request: Request, product_id: int):
        """
        Get single product by ID with caching.
        
        Args:
            product_id: Product ID
            
        Returns:
            JSON product object or 404
        """
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.time()
        
        # Build cache key
        cache_key = f"product:id:{product_id}"
        
        # Try cache first if enabled
        if CACHE_ENABLED:
            cached_result = get_cache(cache_key)
            if cached_result:
                logger.info(
                    f"Cache HIT for product {product_id}",
                    extra={"request_id": request_id, "product_id": product_id},
                )
                return {**cached_result, "cached": True, "request_id": request_id}
        
        # Cache miss - query database
        try:
            product = get_product_by_id(product_id)
            
            if product is None:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Product not found", "product_id": product_id, "request_id": request_id},
                )
            
            # Store in cache (5 minute TTL)
            if CACHE_ENABLED:
                set_cache(cache_key, product, ttl=300)
            
            logger.info(
                f"Database query for product {product_id}",
                extra={
                    "request_id": request_id,
                    "product_id": product_id,
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                },
            )
            
            return {**product, "cached": False, "request_id": request_id}
            
        except Exception as e:
            logger.error(f"Error querying product {product_id}: {e}", extra={"request_id": request_id})
            return JSONResponse(
                status_code=500,
                content={"error": "Database query failed", "request_id": request_id},
            )


# ============================================================================
# Phase 3: Cache Stats Endpoint
# ============================================================================
if CACHE_ENABLED:
    @app.get("/cache/stats")
    async def get_cache_statistics():
        """
        Get cache performance statistics.
        
        Returns:
            JSON with cache hit rate, metrics, and Redis info
        """
        try:
            stats = get_cache_stats()
            return {
                "status": "healthy",
                "cache_enabled": True,
                "metrics": stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Cache stats unavailable", "cache_enabled": False},
            )


# ============================================================================
# Exception Handlers
# ============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ============================================================================
# Run with Uvicorn
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
