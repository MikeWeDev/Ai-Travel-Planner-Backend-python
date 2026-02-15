from typing import List
from app.models import Place


def calculate_match_score(place: Place, interests: List[str]) -> float:
    """
    Calculates how relevant a place is based on user interests.
    """
    if not interests:
        return 0.5  # neutral relevance

    place_category = place.category.lower()
    interests = [i.lower() for i in interests]

    if place_category in interests:
        return 1.0

    # soft matching (optional, expandable later)
    related_categories = {
        "history": ["museum", "historical"],
        "culture": ["festival", "community"],
        "nature": ["wildlife", "park"],
    }

    for interest in interests:
        if place_category in related_categories.get(interest, []):
            return 0.7

    return 0.0
def filter_and_score_places(
    places: List[Place],
    city: str,
    country: str,
    interests: List[str]
) -> List[dict]:

    results = []

    for place in places:
        if place.city.lower() != city.lower():
            continue

        if place.country.lower() != country.lower():
            continue

        score = calculate_match_score(place, interests)

        if score > 0:
            results.append({
                "place": place,
                "score": score
            })

    # sort by score (highest first)
    results.sort(key=lambda x: x["score"], reverse=True)

    return results
