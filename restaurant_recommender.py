
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def validate_coordinates(lat, lng):
    """
    Validate latitude and longitude coordinates
    """
    try:
        lat_float = float(lat)
        lng_float = float(lng)
        
        if not (-90 <= lat_float <= 90) or not (-180 <= lng_float <= 180):
            return False, "Coordinates out of valid range. Latitude must be between -90 and 90, Longitude between -180 and 180."
            
        return True, (lat_float, lng_float)
    except ValueError:
        return False, "Coordinates must be valid numbers."

def get_nearby_restaurants(location, radius_meters=5000, cuisine_types=None):
    """
    Get nearby restaurants using Google Places API
    """
    try:
        # Split and validate coordinates
        if ',' not in location:
            return [], "Invalid location format. Please use 'latitude,longitude'."
            
        lat, lng = location.split(',')
        valid, result = validate_coordinates(lat.strip(), lng.strip())
        
        if not valid:
            return [], result
            
        lat_float, lng_float = result
        base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        params = {
            'location': f"{lat_float},{lng_float}",
            'radius': radius_meters,
            'type': 'restaurant',
            'key': GOOGLE_API_KEY
        }
        
        # Add keyword for cuisine if provided
        if cuisine_types and len(cuisine_types) > 0:
            # Join multiple cuisines with OR for the keyword search
            params['keyword'] = ' OR '.join(cuisine_types)
        
        response = requests.get(base_url, params=params)
        
        # Add debug logging
        if response.status_code != 200:
            print(f"API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return [], f"API Error: Status {response.status_code}"
            
        data = response.json()
        
        if 'error_message' in data:
            print(f"API Error: {data['error_message']}")
            return [], f"API Error: {data['error_message']}"
            
        results = data.get('results', [])
        
        if not results:
            print(f"No results found for location: {location}")
            return [], "No restaurants found in this area. Try a different location or increasing the radius."
            
        # Extract restaurant details
        restaurants = []
        for place in results:
            name = place.get('name', '')
            rating = place.get('rating', 'N/A')
            address = place.get('vicinity', 'Address unavailable')
            place_id = place.get('place_id', '')
            types = place.get('types', [])
            price_level = place.get('price_level', 0)
            
            # Format price level as $ symbols
            price_display = '$' * (price_level if price_level else 1)
            
            # Determine cuisine from types or default to restaurant
            cuisine = next((t for t in types if t != 'restaurant' and not t.startswith('point_of_interest')), 'restaurant')
            cuisine = cuisine.replace('_', ' ').title()
            
            restaurants.append({
                "name": name,
                "rating": rating,
                "address": address,
                "place_id": place_id,
                "cuisine": cuisine,
                "price": price_display
            })
            
        return restaurants, None

    except Exception as e:
        print(f"Error fetching restaurants: {str(e)}")
        return [], f"Error: {str(e)}"
