import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from typing import List
from pydantic import BaseModel
from app.models import TripRequest, TripResponse, Place

# Importing all 3 core engine components
from app.services.data import (
    load_places, 
    get_smart_recommendations, 
    apply_budget_constraint, 
    optimize_route
)

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

class TripRequest(BaseModel):
    city: str
    country: str
    interests: List[str] 
    budget: float
    duration: int 

# ---------------------------
# ROOT (Health Check)
# ---------------------------
@app.get("/")
def root():
    return {"status": "Backend Engine is running"}

# ---------------------------
# GENERATE TRIP (Day 4 & 5 Logic)
# ---------------------------
@app.post("/generate")
def generate_trip(req: TripRequest):
    """
    Main AI Pipeline: 
    1. AI Ranking (TF-IDF) 
    2. Constraint Optimization (Budget)
    3. Spatial Optimization (Route/TSP)
    """
    
    # Step 1: Get AI-ranked places using Vector Similarity (Day 4)
    ranked_df = get_smart_recommendations(req.interests, req.city, req.country)
    
    if ranked_df.empty:
        return {
            "city": req.city, 
            "itinerary": [], 
            "total_budget_used": 0,
            "message": "No places found matching your criteria in this location."
        }

    # Step 2: Apply the Budget Constraint - Greedy Algorithm (Day 4)
    final_selection_list, total_cost = apply_budget_constraint(ranked_df, req.budget)

    if not final_selection_list:
        return {
            "city": req.city, 
            "itinerary": [], 
            "total_budget_used": 0,
            "message": "No places found within your budget."
        }

    # Step 3: Route Optimization - Nearest Neighbor/TSP (Day 5)
    optimized_itinerary = optimize_route(final_selection_list)

    # Return the full "Smart" response back to the Node.js caller
    return {
        "city": req.city,
        "country": req.country,
        "total_budget_used": total_cost,
        "itinerary_count": len(optimized_itinerary),
        "itinerary": optimized_itinerary
    }

# ---------------------------
# DEBUG — get all places
# ---------------------------
@app.get("/places", response_model=List[Place])
def get_all_places():
    """
    Utility endpoint to verify your CSV data is loading correctly.
    """
    raw_places = load_places()
    # Convert to Place objects if they come back as dicts
    places = [Place(**p) if isinstance(p, dict) else p for p in raw_places]
    print(f"📍 Debug: Loaded {len(places)} places from CSV")
    return places

# ---------------------------
# SERVER RUNNER
# ---------------------------
if __name__ == "__main__":
    # Get configuration from .env or use defaults
    # Use 'PORT' as it is the standard name for deployment platforms like Render/Heroku
    server_port = int(os.getenv("PORT", 8000))
    server_host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Python Engine starting on {server_host}:{server_port}")
    uvicorn.run(app, host=server_host, port=server_port)