"""
core/emergency_lookup.py

Looks up official emergency numbers for a country from the public
Emergency Number API (https://emergencynumberapi.com) — free, no API
key required. Used so escalation responses reference REAL numbers
instead of the LLM guessing/hallucinating them.

Falls back gracefully to a generic phrase if the country is unknown,
not mapped, or the lookup fails for any reason (network issue, rate
limit, etc.) — a lookup failure should never block an escalation
response from going out.
"""

from __future__ import annotations
import requests

# Maps supported country names to ISO 3166-1 alpha-2 codes, which
# the API expects. Add more countries here as needed.
COUNTRY_CODES = {
    "United States": "US",
    "United Kingdom": "GB",
    "Pakistan": "PK",
    "India": "IN",
}

# Simple in-memory cache so repeated requests for the same country
# within one running process don't keep re-hitting the API.
_CACHE: dict[str, str] = {}


def get_emergency_numbers(country: str | None) -> str:
    """
    Returns a short, human-readable string of verified emergency
    numbers for the given country, e.g.:
      "Emergency: 911 | Police: 911 | Ambulance: 911 | Fire: 911"
    Falls back to "your local emergency number" if unknown/unavailable.
    """
    if not country:
        return "your local emergency number"

    if country in _CACHE:
        return _CACHE[country]

    code = COUNTRY_CODES.get(country)
    if not code:
        return "your local emergency number"

    try:
        resp = requests.get(
            f"https://emergencynumberapi.com/api/country/{code}",
            timeout=5,
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("error"):
            return "your local emergency number"
        data = payload.get("data", {})
    except Exception:
        # Network issue, timeout, rate limit, bad JSON, etc. —
        # never let this block the escalation response.
        return "your local emergency number"

    parts = []
    dispatch = (data.get("dispatch") or {}).get("all") or []
    police = (data.get("police") or {}).get("all") or []
    ambulance = (data.get("ambulance") or {}).get("all") or []
    fire = (data.get("fire") or {}).get("all") or []

    # The API returns [""] (a list with one empty string) rather than []
    # when a service has no number — filter those out.
    dispatch = [n for n in dispatch if n]
    police = [n for n in police if n]
    ambulance = [n for n in ambulance if n]
    fire = [n for n in fire if n]

    if dispatch:
        parts.append(f"Emergency: {', '.join(dispatch)}")
    if police:
        parts.append(f"Police: {', '.join(police)}")
    if ambulance:
        parts.append(f"Ambulance: {', '.join(ambulance)}")
    if fire:
        parts.append(f"Fire: {', '.join(fire)}")

    if data.get("member_112"):
        parts.append("112 also works")

    result = " | ".join(parts) if parts else "your local emergency number"
    _CACHE[country] = result
    return result