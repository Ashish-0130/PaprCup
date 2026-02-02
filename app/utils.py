import math
import html
from typing import Optional

def calculate_haversine_distance(
    lat1: float, lon1: float, 
    lat2: float, lon2: float
) -> float:
    """
    Calculates distance between two lat/lon points in Kilometers.
    """
    if None in [lat1, lon1, lat2, lon2]:
        return float('inf')

    R = 6371 # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2) + \
        math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * \
        (math.sin(dlon / 2) ** 2)
        
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def sanitize_message(content: str) -> str:
    """
    Prevents XSS by escaping HTML characters.
    """
    if not content:
        return ""
    return html.escape(content.strip())