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
origins = [
    "http://localhost:3000",
    "https://perabox-frontend.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
        "health": "/health/db",
    }


@app.get("/health/db")
async def health_db():
    """Health check for database."""
    from app.db.session import engine, SessionLocal
    from sqlalchemy import text
    
    # Get actual engine URL (masked)
    real_url = str(engine.url)
    if ":" in real_url and "@" in real_url:
        part1 = real_url.split("@")[0]
        part2 = real_url.split("@")[1]
        if ":" in part1:
            user = part1.split(":")[0]
            part1 = f"{user}:***"
        masked_real_url = f"{part1}@{part2}"
    else:
        masked_real_url = real_url

    try:
        db = SessionLocal()
        # Try a simple query
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "ok", 
            "message": "Database connection successful",
            "engine_url": masked_real_url
        }
    except Exception as e:
        import traceback
        # Try to get underlying error
        orig_error = getattr(e, "orig", str(e))
        return {
            "status": "error",
            "message": str(e),
            "orig_error": str(orig_error),
            "engine_url": masked_real_url,
            "traceback": traceback.format_exc()
        }
