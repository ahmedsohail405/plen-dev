"""Where Alex finds prospects.

  osm     : OpenStreetMap Overpass API. Free, no key. Businesses that list a website.
  google  : Google Places API (New) Text Search. Best coverage; needs GOOGLE_PLACES_API_KEY (paid, ask Ahmed).
  csv     : any list you have (columns: business_name, website, category, area, address, phone, email).

Alex does not scrape Google Maps, Yelp or other sites whose terms forbid it.
Every source yields dicts: business_name, website, category, area, address, phone, email, source, source_ref.
"""
from __future__ import annotations

import csv
import time
from urllib.parse import urlparse

import requests

from config import GOOGLE_PLACES_KEY

UA = "PlenDevAlex/1.0 (+https://plendev.com/audit-bot)"

# Plen Dev's target areas and industries (see plen-dev/keywords-and-packages.md)
AREAS = {
    "brooklyn": 'area["name"="Brooklyn"]["boundary"="administrative"]',
    "queens": 'area["name"="Queens"]["boundary"="administrative"]',
    "manhattan": 'area["name"="Manhattan"]["boundary"="administrative"]',
    "nassau": 'area["name"="Nassau County"]["admin_level"="6"]',
    "suffolk": 'area["name"="Suffolk County"]["admin_level"="6"]["is_in:state"!="MA"]',
    "bronx": 'area["name"="The Bronx"]["boundary"="administrative"]',
    "staten_island": 'area["name"="Staten Island"]["boundary"="administrative"]',
    "westchester": 'area["name"="Westchester County"]["admin_level"="6"]',
    "bergen": 'area["name"="Bergen County"]["admin_level"="6"]',
    "hudson_nj": 'area["name"="Hudson County"]["admin_level"="6"]',
    "essex_nj": 'area["name"="Essex County"]["admin_level"="6"]["is_in:state"="NJ"]',
}
# Home areas first: Ahmed's SEO targets (Brooklyn, Queens, Long Island), then the rest of the metro.
AREA_ORDER = ["brooklyn", "queens", "nassau", "suffolk", "manhattan", "bronx", "staten_island",
              "westchester", "bergen", "hudson_nj", "essex_nj"]
CATEGORIES = {  # category -> OSM tag filters
    "dental": ['["amenity"="dentist"]', '["healthcare"="dentist"]'],
    "real_estate": ['["office"="estate_agent"]'],
    "home_healthcare": ['["healthcare"="home_care"]', '["healthcare"="nurse"]'],
    "medical": ['["amenity"="doctors"]', '["amenity"="clinic"]', '["healthcare"="physiotherapist"]'],
    "legal": ['["office"="lawyer"]'],
    "accounting": ['["office"="accountant"]', '["office"="tax_advisor"]'],
    "beauty": ['["shop"="beauty"]', '["shop"="hairdresser"]'],
    "fitness": ['["leisure"="fitness_centre"]'],
    "contractor": ['["craft"="plumber"]', '["craft"="electrician"]', '["craft"="roofer"]', '["craft"="hvac"]'],
    "restaurant": ['["amenity"="restaurant"]'],
    "veterinary": ['["amenity"="veterinary"]'],
    "auto": ['["shop"="car_repair"]', '["shop"="car"]'],
    # Every other kind of business that lists a website
    "office": ['["office"="company"]', '["office"="consulting"]', '["office"="insurance"]', '["office"="financial"]',
               '["office"="architect"]', '["office"="it"]', '["office"="marketing"]', '["office"="employment_agency"]',
               '["office"="logistics"]', '["office"="property_management"]', '["office"="engineer"]'],
    "retail": ['["shop"="furniture"]', '["shop"="jewelry"]', '["shop"="clothes"]', '["shop"="bicycle"]',
               '["shop"="optician"]', '["shop"="florist"]', '["shop"="hardware"]', '["shop"="electronics"]'],
    "trades": ['["craft"="carpenter"]', '["craft"="painter"]', '["craft"="locksmith"]', '["craft"="builder"]',
               '["craft"="window_construction"]', '["shop"="kitchen"]', '["shop"="flooring"]'],
    "hospitality": ['["tourism"="hotel"]', '["amenity"="cafe"]', '["amenity"="bar"]', '["shop"="bakery"]'],
    "education": ['["amenity"="driving_school"]', '["amenity"="language_school"]', '["amenity"="music_school"]',
                  '["amenity"="childcare"]', '["amenity"="kindergarten"]'],
    "services": ['["shop"="dry_cleaning"]', '["shop"="laundry"]', '["amenity"="funeral_hall"]',
                 '["shop"="funeral_directors"]', '["amenity"="storage_rental"]', '["shop"="travel_agency"]',
                 '["amenity"="events_venue"]', '["shop"="pet_grooming"]'],
    "wellness": ['["leisure"="sports_centre"]', '["shop"="massage"]', '["healthcare"="psychotherapist"]',
                 '["healthcare"="optometrist"]', '["healthcare"="chiropractor"]', '["amenity"="pharmacy"]'],
    "nonprofit_religious": ['["office"="ngo"]', '["office"="association"]'],
}
SKIP_HOSTS = ("facebook.com", "instagram.com", "yelp.com", "google.com", "linktr.ee", "twitter.com", "x.com",
              "tiktok.com", "linkedin.com", "zocdoc.com", "healthgrades.com", "nyc.gov", "ny.gov")


def plan():
    """Every (area, category) pair, home areas first. The worker walks this list with a saved cursor."""
    return [(a, c) for a in AREA_ORDER for c in CATEGORIES]


def clean_site(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    host = (urlparse(url).hostname or "").lower()
    if not host or "." not in host or host.endswith((".gov", ".edu", ".mil")) or any(host == h or host.endswith("." + h) for h in SKIP_HOSTS):
        return ""
    return f"{urlparse(url).scheme}://{urlparse(url).netloc.lower()}/"


def osm(area: str, category: str, limit: int = 200,
        endpoint: str = "https://overpass-api.de/api/interpreter") -> list[dict]:
    filters = CATEGORIES[category]
    body = "".join(f'nwr(area.a){f}["website"];nwr(area.a){f}["contact:website"];' for f in filters)
    q = f'[out:json][timeout:90];{AREAS[area]}->.a;({body});out tags center {limit};'
    r = requests.post(endpoint, data={"data": q}, headers={"User-Agent": UA}, timeout=120)
    r.raise_for_status()
    out = []
    for el in r.json().get("elements", []):
        t = el.get("tags", {})
        site = clean_site(t.get("website") or t.get("contact:website", ""))
        if not site or not t.get("name"):
            continue
        addr = " ".join(x for x in [t.get("addr:housenumber"), t.get("addr:street"), t.get("addr:city"), t.get("addr:postcode")] if x)
        out.append({"business_name": t["name"], "website": site, "category": category, "area": area,
                    "address": addr, "phone": t.get("phone") or t.get("contact:phone", ""),
                    "email": t.get("email") or t.get("contact:email", ""),
                    "source": "osm", "source_ref": f"{el['type']}/{el['id']}"})
    time.sleep(2)  # be gentle with the public Overpass server
    return out


def google_places(query: str, category: str, area: str, max_results: int = 60) -> list[dict]:
    """e.g. google_places("dentist in Bay Ridge, Brooklyn", "dental", "brooklyn"). Needs GOOGLE_PLACES_API_KEY."""
    if not GOOGLE_PLACES_KEY:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is not set (Ahmed has to approve and create it)")
    out, token = [], None
    while len(out) < max_results:
        body = {"textQuery": query, "pageSize": 20, **({"pageToken": token} if token else {})}
        r = requests.post("https://places.googleapis.com/v1/places:searchText", json=body, timeout=30, headers={
            "X-Goog-Api-Key": GOOGLE_PLACES_KEY,
            "X-Goog-FieldMask": "places.id,places.displayName,places.websiteUri,places.formattedAddress,"
                                "places.nationalPhoneNumber,places.businessStatus,nextPageToken"})
        r.raise_for_status()
        d = r.json()
        for pl in d.get("places", []):
            site = clean_site(pl.get("websiteUri", ""))
            if site and pl.get("businessStatus", "OPERATIONAL") == "OPERATIONAL":
                out.append({"business_name": pl["displayName"]["text"], "website": site, "category": category,
                            "area": area, "address": pl.get("formattedAddress", ""),
                            "phone": pl.get("nationalPhoneNumber", ""), "email": "",
                            "source": "google_places", "source_ref": pl["id"]})
        token = d.get("nextPageToken")
        if not token:
            break
        time.sleep(2)
    return out


def from_csv(file: str, default_category: str = "", default_area: str = "") -> list[dict]:
    out = []
    with open(file, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            site = clean_site(row.get("website", ""))
            if site:
                out.append({"business_name": row.get("business_name") or row.get("name", ""), "website": site,
                            "category": row.get("category") or default_category,
                            "area": row.get("area") or default_area, "address": row.get("address", ""),
                            "phone": row.get("phone", ""), "email": row.get("email", ""),
                            "source": "csv", "source_ref": file})
    return out
