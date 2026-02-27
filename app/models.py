from pydantic import BaseModel
from typing import List, Optional

class TripRequest(BaseModel):
    city: str
    country: str
    days: int
    budget: float
    interests: List[str]

class Place(BaseModel):
    name: str
    category: str
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: float
    longitude: float
    entry_fee: float

# --- ADD THIS TO SUPPORT THE TIMELINE STRUCTURE ---
class DayPlan(BaseModel):
    day: int
    title: str
    activities: List[Place]

class TripResponse(BaseModel):
    city: str
    country: str
    total_budget_used: float
    # Change "places" to "itinerary" so it matches your route logic
    itinerary: List[DayPlan]