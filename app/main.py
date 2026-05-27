import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from typing import List, Optional
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
from app.models import Place

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    pool_size=10,        
    max_overflow=20,     
    pool_recycle=300     
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- EXTENDED DESIGN SCHEMAS ---
class DynamicTripRequest(BaseModel):
    interests: List[str]
    city: str
    country: str
    budget: float
    days: int
    negative_constraints: Optional[List[str]] = []

class FeedbackSchema(BaseModel):
    user_id: str
    title: str
    itinerary: List[dict]
    feedback: str

# --- ROUTES ---

@app.get("/")
def root():
    return {"status": "Adaptive AI Engine Online"}

@app.post("/generate")
def generate_trip(req: DynamicTripRequest, db: Session = Depends(get_db)):
    # 1. Fetch from DB & execute AI-ranking passing user negative constraints history profile
    ranked_df = get_smart_recommendations(
        user_interests=req.interests, 
        city=req.city, 
        country=req.country, 
        db=db,
        negative_constraints=req.negative_constraints
    )
    
    if ranked_df.empty:
        return {"city": req.city, "itinerary": [], "message": "No places found matching criteria."}

    # 2. Budget Processing
    final_selection_list, total_cost = apply_budget_constraint(ranked_df, req.budget, req.days)

    # 3. Spatial Route Optimization
    optimized_itinerary = optimize_route(final_selection_list, req.days)

    return {
        "city": req.city,
        "country": req.country,
        "total_budget_used": total_cost,
        "itinerary": optimized_itinerary
    }

@app.post("/api/learn/feedback")
def process_incoming_feedback(telemetry: FeedbackSchema):
    """
    Hook endpoint for processing instant metrics or system model fine-tuning records.
    """
    print(f"📡 System Ingested Telemetry Feedback from User [{telemetry.user_id}]")
    print(f"Critique summary: {telemetry.feedback}")
    return {"status": "synchronized", "feedback_recorded": len(telemetry.feedback)}

# ✅ FIXED: Removed response_model to prevent dependency on non-existent app.schemas module
@app.get("/places")
def get_all_places(db: Session = Depends(get_db)):
    return get_db_places(db)

if __name__ == "__main__":
    server_port = int(os.getenv("PORT", 8000))
    
    # 🌍 PRODUCTION OPTIMIZATION: 
    # Use multi-worker cluster on Render/Production to avoid thread-locking during heavy generation jobs
    if os.getenv("RENDER") or os.getenv("NODE_ENV") == "production":
        uvicorn.run("app.main:app", host="0.0.0.0", port=server_port, workers=4)
    else:
        # Standard lightweight single-process reload configuration for local development PC
        uvicorn.run(app, host="0.0.0.0", port=server_port)