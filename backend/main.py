# KidSafe AI Backend - Main Application
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base
from routers import auth_routes, profile_routes, pairing_routes, request_routes, sync_routes, log_routes

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KidSafe AI Backend API",
    version="1.0.0",
    description="Parental Control, Device Pairing, Policy Sync & Activity Management Service"
)

# Enable CORS for cross-origin requests from Dashboard and Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(profile_routes.router)
app.include_router(pairing_routes.router)
app.include_router(request_routes.router)
app.include_router(sync_routes.router)
app.include_router(log_routes.router)

# Mount static files for Parent Web Dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_dashboard():
        return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "KidSafe AI Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
