import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import updated services
from app.services.data import (
    get_db_places, 
    get_smart_recommendations, 
    apply_budget_constraint, 
    optimize_route
)
from app.models import TripRequest, TripResponse, Place

load_dotenv()

# --- DATABASE SETUP ---
DATABASE_URL = os.getenv("DATABASE_URL")

# UPDATED ENGINE FOR POOLER SUPPORT
# We added pool_size and pool_recycle to keep the connection healthy
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    pool_size=10,        # Keeps 10 connections ready
    max_overflow=20,     # Allows extra connections if busy
    pool_recycle=300     # Refreshes connection every 5 minutes
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROUTES ---

@app.get("/")
def root():
    return {"status": "Backend Engine is running on Cloud DB (via Pooler)"}

@app.post("/generate")
def generate_trip(req: TripRequest, db: Session = Depends(get_db)):
    # 1. Fetch data from DB and Rank (Vector Similarity)
    ranked_df = get_smart_recommendations(req.interests, req.city, req.country, db)
    
    if ranked_df.empty:
        return {"city": req.city, "itinerary": [], "message": "No places found."}

    # 2. Budget Logic
    final_selection_list, total_cost = apply_budget_constraint(ranked_df, req.budget)

    # 3. Route Optimization
    optimized_itinerary = optimize_route(final_selection_list)

    return {
        "city": req.city,
        "country": req.country,
        "total_budget_used": total_cost,
        "itinerary": optimized_itinerary
    }

@app.get("/places", response_model=List[Place])
def get_all_places(db: Session = Depends(get_db)):
    """Fetches all places directly from Supabase"""
    return get_db_places(db)

if __name__ == "__main__":
    server_port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=server_port)