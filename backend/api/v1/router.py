"""
API Version 1 Router
====================

Main router that aggregates all v1 endpoint routers.

Author: Prior Auth AI Team
Version: 1.0.0
"""

from fastapi import APIRouter
from backend.api.v1.endpoints import auth, users, pa, patients, providers, payers

# Import endpoint routers (will be created in future phases)
# from backend.api.v1.endpoints import (
#     documents,
#     submissions,
#     appeals,
#     analytics,
#     admin,
#     agents
# )

# Create main v1 router
api_router = APIRouter()


# Health check endpoint (for infrastructure)
@api_router.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service health status.
    Used by load balancers and monitoring systems.
    """
    return {
        "status": "healthy",
        "service": "prior-auth-ai",
        "version": "1.0.0"
    }


# Root endpoint
@api_router.get("/", tags=["root"])
async def root():
    """
    API root endpoint.
    
    Returns basic API information.
    """
    return {
        "message": "Prior Authorization AI Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Include endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    pa.router,
    prefix="/pa",
    tags=["prior-authorizations"]
)

api_router.include_router(
    patients.router,
    prefix="/patients",
    tags=["patients"]
)

api_router.include_router(
    providers.router,
    prefix="/providers",
    tags=["providers"]
)

api_router.include_router(
    payers.router,
    prefix="/payers",
    tags=["payers"]
)


# Additional endpoint routers (to be added in future phases)
# api_router.include_router(
#     pa.router,
#     prefix="/pa",
#     tags=["prior-authorizations"]
# )
# 
# api_router.include_router(
#     documents.router,
#     prefix="/documents",
#     tags=["documents"]
# )
# 
# api_router.include_router(
#     patients.router,
#     prefix="/patients",
#     tags=["patients"]
# )
# 
# api_router.include_router(
#     submissions.router,
#     prefix="/submissions",
#     tags=["submissions"]
# )
# 
# api_router.include_router(
#     appeals.router,
#     prefix="/appeals",
#     tags=["appeals"]
# )
# 
# api_router.include_router(
#     analytics.router,
#     prefix="/analytics",
#     tags=["analytics"]
# )
# 
# api_router.include_router(
#     admin.router,
#     prefix="/admin",
#     tags=["admin"]
# )
# 
# api_router.include_router(
#     agents.router,
#     prefix="/agents",
#     tags=["agents"]
# )