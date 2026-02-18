from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, services, bookings, users, technicians, payments, chat

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
app.include_router(chat.router, prefix="/api/v1")


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
    """Health check for database validation."""
    import socket
    from app.db.session import engine, SessionLocal
    from sqlalchemy import text
    
    # Get hostname from engine URL
    real_url = str(engine.url)
    hostname = "unknown"
    if "@" in real_url:
        hostname = real_url.split("@")[1].split(":")[0]

    probe_results = {
        "hostname": hostname,
        "dns_a": [],
        "dns_aaaa": [],
        "tcp_5432": "untested",
        "tcp_6543": "untested",
        "engine_url_masked": real_url.replace(real_url.split("@")[0].split(":")[1], "***") if ":" in real_url and "@" in real_url else real_url
    }

    # 1. DNS Probe
    try:
        ais = socket.getaddrinfo(hostname, 0, 0, 0, 0)
        for result in ais:
            family, _, _, _, sockaddr = result
            ip = sockaddr[0]
            if family == socket.AF_INET:
                probe_results["dns_a"].append(ip)
            elif family == socket.AF_INET6:
                probe_results["dns_aaaa"].append(ip)
    except Exception as e:
        probe_results["dns_error"] = str(e)

    # 2. TCP Probe
    def check_port(host, port):
        try:
            sock = socket.create_connection((host, port), timeout=3)
            sock.close()
            return "open"
        except Exception as e:
            return f"closed: {e}"

    probe_results["tcp_5432"] = check_port(hostname, 5432)
    probe_results["tcp_6543"] = check_port(hostname, 6543)

    # 3. DB Connect Probe
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "ok", 
            "message": "Database connection successful",
            "probe": probe_results
        }
    except Exception as e:
        # Get underlying error
        orig_error = getattr(e, "orig", str(e))
        return {
            "status": "error",
            "message": str(e),
            "orig_error": str(orig_error),
            "probe": probe_results
        }
