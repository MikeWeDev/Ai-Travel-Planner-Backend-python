import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from geopy.distance import geodesic

# --- MISSING FUNCTION: Fixes the ImportError in main.py ---
def load_places():
    """
    Loads raw CSV data and converts it to a list of dicts for the debug endpoint.
    Ensures NaN values are replaced with None for JSON compatibility.
    """
    try:
        # Load the CSV
        df = pd.read_csv("app/data/locations.csv")
        # Replace NaN with None (becomes 'null' in JSON)
        df = df.replace({np.nan: None})
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error loading CSV for debug: {e}")
        return []


# --- TASK 1: THE AI MATCHING ENGINE (Day 4) ---
def get_smart_recommendations(user_interests: list, city: str, country: str):
    """
    Uses TF-IDF and Cosine Similarity to rank places based on user interests.
    """
    try:
        df = pd.read_csv("app/data/locations.csv") 
    except FileNotFoundError:
        print("CRITICAL ERROR: locations.csv not found!")
        return pd.DataFrame()

    # Data Cleaning
    df['description'] = df['description'].fillna('')
    df['category'] = df['category'].fillna('')

    # Hard Filter: City & Country
    filtered_df = df[
        (df['city'].str.lower() == city.lower()) & 
        (df['country'].str.lower() == country.lower())
    ].copy()

    if filtered_df.empty:
        return filtered_df

    # Vectorization (Semantic Search)
    vectorizer = TfidfVectorizer(stop_words='english')
    combined_text_data = filtered_df['category'] + " " + filtered_df['description']
    content_matrix = vectorizer.fit_transform(combined_text_data)
    
    user_query = " ".join(user_interests)
    user_vector = vectorizer.transform([user_query])

    # Calculation
    scores = cosine_similarity(user_vector, content_matrix).flatten()
    filtered_df['ai_score'] = scores

    return filtered_df.sort_values(by='ai_score', ascending=False)


# --- TASK 2: THE OPTIMIZATION ALGORITHM (Day 4) ---
def apply_budget_constraint(ranked_df, max_budget: float):
    """
    A Greedy Algorithm that selects the best-matched places 
    that fit within the user's financial limit.
    """
    itinerary = []
    current_cost = 0

    for index, row in ranked_df.iterrows():
        try:
            price = float(row['entry_fee'])
        except (ValueError, TypeError):
            price = 0.0
        
        # Greedy Choice
        if current_cost + price <= max_budget:
            place_dict = row.to_dict()
            
            # Remove NaN values before sending to JSON (FastAPI requirement)
            place_dict = {k: (v if not (isinstance(v, float) and np.isnan(v)) else None) 
                         for k, v in place_dict.items()}
            
            itinerary.append(place_dict)
            current_cost += price
        
        # Return 5 items per day
        if len(itinerary) >= 5:
            break
            
    return itinerary, current_cost


# --- TASK 3: THE ROUTE OPTIMIZER (Day 5) ---
def optimize_route(selected_places: list):
    """
    Sorts a list of places using the Nearest Neighbor heuristic 
    to minimize travel distance.
    """
    if not selected_places:
        return []

    # Copy list to avoid modifying original during iteration
    temp_places = list(selected_places)
    optimized_route = []
    
    # 1. Start with the first place
    current_place = temp_places.pop(0)
    optimized_route.append(current_place)

    # 2. Heuristic Search
    while temp_places:
        closest_index = 0
        min_distance = float('inf')
        
        for i, next_place in enumerate(temp_places):
            # Haversine formula via Geopy
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