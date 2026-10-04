import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/stations", tags=["stations"])

STATIONS_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "stations"


@router.get("/{station_id}")
def get_station(station_id: str):
    station_file = STATIONS_DIR / f"{station_id}.json"

    if not station_file.exists():
        raise HTTPException(status_code=404, detail="Station not found")

    with station_file.open("r", encoding="utf-8-sig") as file:
        return json.load(file)
