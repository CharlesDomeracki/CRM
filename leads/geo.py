import json
import math
import urllib.error
import urllib.parse
import urllib.request


def _geocode(params, timeout=8):
    query = urllib.parse.urlencode({**params, "format": "json", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{query}"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "LeadsCRM/1.0 (internal sales tool)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            results = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, OSError):
        return None
    if not results:
        return None
    try:
        return float(results[0]["lat"]), float(results[0]["lon"])
    except (KeyError, TypeError, ValueError):
        return None


def geocode_city_state(city, state, country="USA", timeout=8):
    return _geocode({"city": city, "state": state, "country": country}, timeout=timeout)


def geocode_postalcode(postalcode, country="USA", timeout=8):
    return _geocode({"postalcode": postalcode, "country": country}, timeout=timeout)


def haversine_miles(lat1, lon1, lat2, lon2):
    radius_miles = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * radius_miles * math.asin(math.sqrt(a))
