"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.common.logging import configure_logging
from app.security.router import router as security_router
from app.transaction.router import router as transaction_router
from app.customer.router import router as customer_router
from app.audit.router import router as audit_router
from app.case_management.router import router as case_router
from app.investigation.router import router as investigation_router
from app.alert.router import router as alert_router
from app.rules.router import router as rules_router
from app.dashboard.router import router as dashboard_router
from app.admin.router import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    configure_logging()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="AML Transaction Monitoring Platform",
    description="AI-powered Anti-Money Laundering transaction monitoring and case management system",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Register routers
app.include_router(security_router, prefix="/api")
app.include_router(transaction_router, prefix="/api/v1/transactions", tags=["transactions"])
app.include_router(customer_router, prefix="/api/v1/customers", tags=["customers"])
app.include_router(audit_router, prefix="/api/v1", tags=["audit"])
app.include_router(case_router, prefix="/api/v1/cases", tags=["cases"])
app.include_router(investigation_router, prefix="/api/v1/cases", tags=["investigation"])
app.include_router(alert_router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(rules_router, prefix="/api/v1/rules", tags=["rules"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
