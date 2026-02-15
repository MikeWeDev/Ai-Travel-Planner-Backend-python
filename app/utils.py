import csv
from pathlib import Path
from models import Place

DATA_PATH = Path(__file__).parent / "data" / "locations.csv"

def load_places() -> list[Place]:
    places = []

    with open(DATA_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            try:
                place = Place(
                    name=row["name"],
                    category=row["category"].lower(),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    entry_fee=float(row["entry_fee"]),
                    city=row["city"]
                )
                places.append(place)
            except Exception as e:
                print("❌ Skipping row:", row, "Error:", e)

    return places
