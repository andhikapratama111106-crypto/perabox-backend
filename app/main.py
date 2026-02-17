from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, services, bookings, users, technicians, payments

app = FastAPI(
    title="PERABOX API",
    description="Homecare Service Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(technicians.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to PERABOX API",
        "docs": "/docs",
        "health": "/health",
    }
