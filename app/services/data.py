import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from geopy.distance import geodesic

# --- TASK 1: THE DB FETCHING ENGINE ---

# THIS IS THE FUNCTION YOUR main.py WAS MISSING!
def get_db_places(db: Session, city: str = None, country: str = None):
    """
    Fetches locations from Postgres and returns them as a list of dicts.
    Used by the /places endpoint.
    """
    query_str = "SELECT * FROM locations"
    params = {}
    
    if city and country:
        query_str += " WHERE city ILIKE :city AND country ILIKE :country"
        params = {"city": city, "country": country}
    
    result = db.execute(text(query_str), params)
    return [dict(row._mapping) for row in result]

def load_places(db: Session):
    """
    Fetches all data from the Supabase 'locations' table.
    Ensures NaN values are replaced for JSON compatibility.
    """
    try:
        query = text("SELECT * FROM locations")
        result = db.execute(query)
        
        df = pd.DataFrame([dict(row._mapping) for row in result])
        
        if df.empty:
            return []
            
        df = df.replace({np.nan: None})
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error loading from DB: {e}")
        return []


# --- TASK 2: THE AI MATCHING ENGINE ---
def get_smart_recommendations(user_interests: list, city: str, country: str, db: Session):
    """
    Queries the Cloud DB for specific city/country, then ranks via AI.
    """
    query = text("""
        SELECT * FROM locations 
        WHERE city ILIKE :city AND country ILIKE :country
    """)
    result = db.execute(query, {"city": city, "country": country})
    filtered_df = pd.DataFrame([dict(row._mapping) for row in result])

    if filtered_df.empty:
        return filtered_df

    filtered_df['description'] = filtered_df['description'].fillna('')
    filtered_df['category'] = filtered_df['category'].fillna('')

    vectorizer = TfidfVectorizer(stop_words='english')
    combined_text_data = filtered_df['category'] + " " + filtered_df['description']
    
    try:
        content_matrix = vectorizer.fit_transform(combined_text_data)
        user_query = " ".join(user_interests)
        user_vector = vectorizer.transform([user_query])

        scores = cosine_similarity(user_vector, content_matrix).flatten()
        filtered_df['ai_score'] = scores
    except ValueError:
        filtered_df['ai_score'] = 0.5

    return filtered_df.sort_values(by='ai_score', ascending=False)


# --- TASK 3: THE OPTIMIZATION ALGORITHM ---
def apply_budget_constraint(ranked_df, max_budget: float):
    """
    Greedy Algorithm to select places that fit the financial limit.
    """
    itinerary = []
    current_cost = 0

    for index, row in ranked_df.iterrows():
        try:
            price = float(row['entry_fee']) if row['entry_fee'] else 0.0
        except (ValueError, TypeError):
            price = 0.0
        
        if current_cost + price <= max_budget:
            place_dict = row.to_dict()
            place_dict = {k: (v if not (isinstance(v, float) and np.isnan(v)) else None) 
                         for k, v in place_dict.items()}
            
            itinerary.append(place_dict)
            current_cost += price
        
        if len(itinerary) >= 5:
            break
            
    return itinerary, current_cost


# --- TASK 4: THE ROUTE OPTIMIZER ---
def optimize_route(selected_places: list):
    """
    Nearest Neighbor optimization for travel distance.
    """
    if not selected_places:
        return []

    temp_places = list(selected_places)
    optimized_route = []
    
    current_place = temp_places.pop(0)
    optimized_route.append(current_place)

    while temp_places:
        closest_index = 0
        min_distance = float('inf')
        
        for i, next_place in enumerate(temp_places):
            dist = geodesic(
                (current_place['latitude'], current_place['longitude']),
                (next_place['latitude'], next_place['longitude'])
            ).km
            
            if dist < min_distance:
                min_distance = dist
                closest_index = i
        
        current_place = temp_places.pop(closest_index)
        optimized_route.append(current_place)

    return optimized_route