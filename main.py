from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import stock, inventory, indent, vc
import logging
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for FastAPI application.
    Handles startup and shutdown routines.
    """
    # Startup logic
    logger.info("Starting application...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown logic
    logger.info("Shutting down application...")
    # Add any cleanup code here

app = FastAPI(lifespan=lifespan)

app.include_router(stock.router)
app.include_router(inventory.router)
app.include_router(indent.router)
app.include_router(vc.router)

@app.get("/")
def main():
    return {"message": "Welcome to inventory management system"}

if __name__ == "__main__":
    import uvicorn
    import os

    # Use the PORT environment variable if available, otherwise default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)