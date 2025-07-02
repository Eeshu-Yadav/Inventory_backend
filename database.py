from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from models.inventory import Request, RequestItem, ReqIssue
from models.indent import Indent
from models.stock import Stock, Item
from typing import List, Type
from beanie import Document


load_dotenv()


# PostgreSQL database configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
MAX_CONNECTION_RETRIES = 3
CONNECTION_TIMEOUT_MS = 5000


# Async init function for DB
async def init_db():
    """
    Initialize the MongoDB connection and Beanie document models.
    Handles connection errors and retries automatically.
    """
    client = AsyncIOMotorClient(
        MONGO_URI,
        serverSelectionTimeoutMS=CONNECTION_TIMEOUT_MS
    )
    try:
        # Test the connection
        await client.admin.command('ping')
        db = client[DB_NAME]
        
        # Get all Document models automatically
        document_models: List[Type[Document]] = [
            Request, RequestItem, ReqIssue, 
            Indent, Stock, Item
        ]
        
        await init_beanie(
            database=db,
            document_models=document_models
        )
        print("✅ Database connection established successfully")


        
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        raise


