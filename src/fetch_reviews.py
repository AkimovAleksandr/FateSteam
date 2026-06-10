import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


STEAM_REVIEWS_URL = "https://store.steampowered.com/appreviews/1710670"


def fetch_reviews(
    app_id: int,
    start_date: str,
    end_date: str,
    num_per_page: int = 100,
) -> list:
    """Load Steam reviews for the selected app and date range."""
    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    reviews = []
    cursor = "*"

    while True:
        params = {
            "json": 1,
            "filter": "recent",
            "language": "all",
            "day_range": 365,
            "num_per_page": num_per_page,
            "cursor": cursor,
        }

        response = requests.get(
            f"https://store.steampowered.com/appreviews/{app_id}",
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()

        for item in payload.get("reviews", []):
            created = item.get("timestamp_created", 0)
            if start_ts <= created <= end_ts:
                reviews.append(item)

        if not payload.get("cursor") or payload.get("cursor") == cursor:
            break

        cursor = payload.get("cursor")
        time.sleep(1)

    return reviews


def save_reviews(reviews: list, start_date: str, end_date: str) -> Path:
    """Save raw reviews to data/ as a JSON file."""
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"raw_reviews_{start_date}_{end_date}.json"
    output_path.write_text(
        json.dumps(reviews, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Steam reviews for Tracery of Fate"
    )
    parser.add_argument("--app-id", type=int, default=1710670)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    args = parser.parse_args()

    reviews = fetch_reviews(args.app_id, args.start_date, args.end_date)
    path = save_reviews(reviews, args.start_date, args.end_date)
    print(f"Saved {len(reviews)} reviews to {path}")


if __name__ == "__main__":
    main()
