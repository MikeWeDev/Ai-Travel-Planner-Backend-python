from fastapi import FastAPI
from typing import List
from app.models import TripRequest, TripResponse, Place
from pydantic import BaseModel
# Importing all 3 core engine components
from app.services.data import (
    load_places, 
    get_smart_recommendations, 
    apply_budget_constraint, 
    optimize_route
)

app = FastAPI()
class TripRequest(BaseModel):
    city: str
    country: str
    interests: List[str] # Or just list
    budget: float
    duration: int # Make sure this isn't str

# ---------------------------
# ROOT (Health Check)
# ---------------------------
@app.get("/")
def root():
    return {"status": "Backend Engine is running", "stage": "Day 5 Complete"}

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
    # This re-orders the budget-friendly places for the shortest path
    optimized_itinerary = optimize_route(final_selection_list)

    # Return the full "Smart" response
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