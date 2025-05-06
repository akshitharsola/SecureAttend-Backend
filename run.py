# run.py
import os
import uvicorn
import asyncio
from app.db.init_db import init_db
from app.db.base_class import Base
from app.db.session import engine
import app.models  # This will import all models in the correct order

if __name__ == "__main__":
    try:
        # Create alembic migrations directory
        os.makedirs("alembic/versions", exist_ok=True)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Run initial setup
        init_db()
        
        # Start the application
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        print(f"Error starting application: {e}")