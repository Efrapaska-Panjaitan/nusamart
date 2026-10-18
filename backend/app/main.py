from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.api.v1.routers import auth, catalog, customer, orders, admin
settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", description="NusaMart e-commerce REST API")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
                   allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type", "Idempotency-Key"])
app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["Authentication"])
app.include_router(catalog.router, prefix=settings.api_v1_prefix, tags=["Catalog"])
app.include_router(customer.router, prefix=settings.api_v1_prefix, tags=["Customer"])
app.include_router(orders.router, prefix=settings.api_v1_prefix, tags=["Checkout & Orders"])
app.include_router(admin.router, prefix=f"{settings.api_v1_prefix}/admin", tags=["Admin"])

@app.get("/", include_in_schema=False)
def root(): return {"name": settings.app_name, "docs": "/docs", "health": "/health"}
@app.get("/health", tags=["Health"])
def health(): return {"status": "ok"}
@app.get("/health/ready", tags=["Health"])
def readiness():
    from sqlalchemy import text
    from app.db.session import engine
    try:
        with engine.connect() as connection: connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "disconnected"})
    return {"status": "ready", "database": "connected"}
