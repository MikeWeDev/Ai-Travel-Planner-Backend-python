from pydantic import BaseModel
from typing import List,Optional

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

class TripResponse(BaseModel):
    city: str
    places: List[Place]
