import streamlit as st
from restaurant_recommender import get_nearby_restaurants, validate_coordinates
from glucose_cgm_agents import analyze_menu
from google_menu_search_agent import simulate_menu
from real_menu_fetcher import get_real_menu
from google_maps_scraper import get_real_menu_from_google_maps
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import openai
import os
import threading
import time
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up page configuration with custom theme
st.set_page_config(page_title="🌍 CGM-Aware Travel Assistant", layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {color: #2C3E50; font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem;}
    .sub-header {color: #34495E; font-size: 1.5rem; font-weight: 500; margin-bottom: 1.5rem;}
    .card {border-radius: 15px; border: 1px solid #E0E0E0; padding: 1.5rem; margin-bottom: 1rem; background: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);}
    .highlight {background-color: #F8F9FA; padding: 1rem; border-radius: 10px; margin: 1rem 0;}
    .restaurant-card {border-radius: 15px; border: 1px solid #E0E0E0; padding: 1.5rem; margin: 1rem 0; background: white; transition: transform 0.3s ease, box-shadow 0.3s ease;}
    .restaurant-card:hover {transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);}
    .restaurant-name {color: #2C3E50; font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem;}
    .restaurant-info {color: #7F8C8D; font-size: 1rem; margin-bottom: 0.5rem;}
    .menu-section {background-color: #F8F9FA; padding: 1rem; border-radius: 10px; margin: 1rem 0;}
    .menu-title {color: #2C3E50; font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;}
    .cgm-safe {color: #27AE60; font-weight: 600;}
    .cgm-avoid {color: #E74C3C; font-weight: 600;}
    .cgm-combo {color: #3498DB; font-weight: 600;}
    .map-link {background-color: #3498DB; color: white; padding: 0.5rem 1rem; border-radius: 5px; text-decoration: none; display: inline-block; margin-top: 1rem;}
    .map-link:hover {background-color: #2980B9; text-decoration: none; color: white;}
    .stButton>button {background-color: #3498DB; color: white; border: none; border-radius: 5px; padding: 0.5rem 1rem; font-weight: 600;}
    .stButton>button:hover {background-color: #2980B9;}
</style>
""", unsafe_allow_html=True)

# Header with improved styling
st.markdown('<p class="main-header">🌍 Smart Restaurant Finder</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Find and analyze restaurant menus based on your CGM data</p>', unsafe_allow_html=True)

# Location input
st.markdown('<div class="card">', unsafe_allow_html=True)

# Predefined locations for easier selection
predefined_locations = [
    "Current Location",
    "San Francisco, CA",
    "New York, NY",
    "Chicago, IL",
    "Los Angeles, CA",
    "Seattle, WA",
    "Austin, TX",
    "Boston, MA"
]

# Let user select from predefined locations or enter their own
location_option = st.radio(
    "Choose a location option:",
    ["Select from popular cities", "Enter custom location"]
)

if location_option == "Select from popular cities":
    st.markdown('<p class="menu-title">🏙️ Select a city</p>', unsafe_allow_html=True)
    location_search = st.selectbox("City selection", predefined_locations, label_visibility="collapsed")
else:
    st.markdown('<p class="menu-title">📍 Enter your location</p>', unsafe_allow_html=True)
    location_search = st.text_input("Location input", placeholder="e.g. San Francisco, CA", label_visibility="collapsed")

# Use hardcoded coordinates for predefined locations to avoid geocoding issues
predefined_coordinates = {
    "San Francisco, CA": (37.7749, -122.4194),
    "New York, NY": (40.7128, -74.0060),
    "Chicago, IL": (41.8781, -87.6298),
    "Los Angeles, CA": (34.0522, -118.2437),
    "Seattle, WA": (47.6062, -122.3321),
    "Austin, TX": (30.2672, -97.7431),
    "Boston, MA": (42.3601, -71.0589)
}

# Use browser geolocation if "Current Location" is selected
use_current_location = location_search == "Current Location"
if use_current_location:
    st.info("📍 Using your current location. The app will detect your location when searching for restaurants.")

# For predefined locations, use hardcoded coordinates
elif location_search in predefined_coordinates:
    lat, lng = predefined_coordinates[location_search]
    st.success(f"Using location: {location_search}")
    map_data = {"latitude": [lat], "longitude": [lng]}
    st.map(map_data)
    # Store coordinates in session state
    st.session_state['search_lat'] = lat
    st.session_state['search_lng'] = lng
    st.session_state['search_address'] = location_search

# For custom locations, try geocoding
elif location_search and location_option == "Enter custom location":
    try:
        # Use a more reliable geocoding service with longer timeout
        geolocator = Nominatim(user_agent="glucose-buddy-app", timeout=10)
        location = geolocator.geocode(location_search)
        if location:
            st.success(f"Found location: {location.address}")
            map_data = {"latitude": [location.latitude], "longitude": [location.longitude]}
            st.map(map_data)
            # Store coordinates in session state
            st.session_state['search_lat'] = location.latitude
            st.session_state['search_lng'] = location.longitude
            st.session_state['search_address'] = location.address
        else:
            st.warning("Location not found. Please try a different search term or use one of the predefined locations.")
    except Exception as e:
        st.error(f"Error finding location: {str(e)}")
        st.warning("Geocoding service may be temporarily unavailable. Please try one of the predefined locations.")

st.markdown('</div>', unsafe_allow_html=True)

# Cuisine selection with better UI
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<p class="menu-title">🍽️ Select your preferred cuisines</p>', unsafe_allow_html=True)
cuisines = st.multiselect(
    "Select cuisines",
    ["Indian", "Chinese", "Italian", "Mexican", "Japanese", "Thai", "Mediterranean", "Korean", "American", "International"],
    default=["Indian"],
    label_visibility="collapsed"
)

# Radius selection
st.markdown('<p class="menu-title">🔍 Set search radius</p>', unsafe_allow_html=True)
radius = st.slider("Search radius (meters)", min_value=1000, max_value=20000, value=5000, step=1000)
st.markdown('</div>', unsafe_allow_html=True)

# Main search button
if st.button("🔍 Find & Analyze Restaurants", use_container_width=True):
    if "glucose_summary" not in st.session_state or not st.session_state["glucose_summary"]:
        st.warning("Please upload and analyze your CGM report in the Home tab first.")
    else:
        # Get location for search
        if use_current_location:
            # For "Current Location", use a default location (San Francisco)
            # This is a workaround since browser geolocation isn't reliable in Streamlit
            st.info("📍 Using San Francisco as your current location for demo purposes...")
            
            # Use San Francisco coordinates
            lat = 37.7749
            lng = -122.4194
            location = f"{lat},{lng}"
            
            with st.spinner("🔍 Searching for restaurants in San Francisco..."):
                # For each cuisine, search for restaurants
                all_restaurants = []
                
                for cuisine in cuisines:
                    with st.spinner(f"🔍 Searching for {cuisine} restaurants..."):
                        # Search for restaurants of this cuisine type
                        restaurants_for_cuisine, error_msg = get_nearby_restaurants(
                            location, 
                            radius_meters=radius, 
                            cuisine_types=[cuisine]
                        )
                        
                        if not error_msg and restaurants_for_cuisine:
                            # Take up to 3 restaurants for this cuisine
                            all_restaurants.extend(restaurants_for_cuisine[:3])
                
                # Set the results
                restaurants = all_restaurants
                error = None if restaurants else "No restaurants found for the selected cuisines."
        else:
            # Use coordinates from the location search
            if 'search_lat' in st.session_state and 'search_lng' in st.session_state:
                lat = st.session_state['search_lat']
                lng = st.session_state['search_lng']
                location = f"{lat},{lng}"
                
                with st.spinner("🔍 Searching for restaurants near {location_search}..."):
                    # Pass all selected cuisines to the restaurant finder
                    restaurants, error = get_nearby_restaurants(location, radius_meters=radius, cuisine_types=cuisines)
            else:
                st.error("Please enter a valid location or use 'Current Location'.")
                restaurants = []
                error = "No location specified."
        
        # Process and display restaurant results
        if error:
            st.error(error)
        elif not restaurants:
            st.warning("No restaurants found in this area. Try increasing the search radius or changing location.")
        else:
            # Display a map with the location
            st.markdown('<div class="highlight">', unsafe_allow_html=True)
            st.markdown(f"### 📍 Showing restaurants near {location_search if 'location_search' in locals() and location_search else f'{lat}, {lng}'}")
            map_data = {"latitude": [float(lat)], "longitude": [float(lng)]}
            st.map(map_data)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show restaurant results
            st.markdown(f"### 🍴️ Found {len(restaurants)} restaurants")
            
            # Limit to 3 restaurants per cuisine
            filtered_restaurants = []
            cuisine_count = {cuisine: 0 for cuisine in cuisines}
            
            # Filter to max 3 restaurants per cuisine
            for restaurant in restaurants:
                cuisine = restaurant.get("cuisine", "")
                # Check if this restaurant's cuisine matches any of our selected cuisines
                for selected_cuisine in cuisines:
                    if selected_cuisine.lower() in cuisine.lower() or selected_cuisine.lower() in restaurant.get("name", "").lower():
                        # Only add if we haven't reached the limit for this cuisine
                        if cuisine_count[selected_cuisine] < 3:
                            filtered_restaurants.append(restaurant)
                            cuisine_count[selected_cuisine] += 1
            
            # Show the limited number of restaurants
            st.markdown(f"Showing top {len(filtered_restaurants)} restaurants (max 3 per cuisine)")
            
            # Create columns for restaurant cards
            cols = st.columns(3)
            
            # Display each restaurant in a card
            for i, restaurant in enumerate(filtered_restaurants):
                with cols[i % 3]:
                    name = restaurant.get("name", "Unknown Restaurant")
                    rating = restaurant.get("rating", "N/A")
                    address = restaurant.get("address", "Address not found")
                    price = restaurant.get("price", "$")
                    place_id = restaurant.get("place_id", "")
                    detected_cuisine = restaurant.get("cuisine", "")
                    
                    # Create a card for the restaurant
                    st.markdown(f'''
                    <div class="restaurant-card">
                        <div class="restaurant-name">{name}</div>
                        <div class="restaurant-info">⭐ Rating: {rating} | 💰 Price: {price}</div>
                        <div class="restaurant-info">🍽️ Cuisine: {detected_cuisine}</div>
                        <div class="restaurant-info">📍 {address}</div>
                    ''', unsafe_allow_html=True)
                    
                    # Create an expander for the menu and analysis
                    with st.expander("View Menu & CGM Analysis"):
                        # Determine which cuisine to use for this restaurant
                        # If the restaurant's cuisine is detected and in our list, use it
                        # Otherwise use the first selected cuisine
                        detected_cuisine = detected_cuisine if detected_cuisine in cuisines else (cuisines[0] if cuisines else "International")
                        
                        # Create a placeholder for menu loading message
                        menu_placeholder = st.empty()
                        menu_placeholder.info("⏳ Searching for real menu...")
                        
                        # Try to get a real menu
                        menu = None
                        menu_source = ""
                        is_real = False
                        
                        # Try to get a real menu using multiple methods
                        try:
                            # First try Google Maps
                            with st.spinner(f"🔍 Searching for real menu on Google Maps for {name}..."):
                                maps_menu, maps_success, maps_url = get_real_menu_from_google_maps(
                                    restaurant_name=name,
                                    location=address
                                )
                                
                                if maps_success:
                                    menu = maps_menu
                                    menu_source = "Real Menu (Google Maps)"
                                    is_real = True
                                    menu_placeholder.success("✅ Found real menu on Google Maps!")
                                else:
                                    # If Google Maps fails, try the web scraper
                                    menu_placeholder.info("⏳ Trying web search for menu...")
                                    with st.spinner(f"🔍 Searching web for menu of {name}..."):
                                        real_menu, is_real, menu_url = get_real_menu(
                                            restaurant_name=name,
                                            address=address,
                                            place_id=place_id if place_id else ""
                                        )
                                        
                                        if is_real:
                                            menu = real_menu
                                            menu_source = "Real Menu (Web)"
                                            menu_placeholder.success("✅ Found real menu from web search!")
                                        else:
                                            # If no real menu found, fall back to AI simulation
                                            menu_placeholder.info("⏳ Generating AI menu simulation...")
                                            with st.spinner(f"🤖 Generating menu for {name}..."):
                                                # Pass restaurant name without forcing cuisine in the name
                                                menu = simulate_menu(
                                                    restaurant_name=name,
                                                    cuisine_type=detected_cuisine
                                                )
                                                menu_source = "AI-Simulated"
                        except Exception as e:
                            st.error(f"Error searching for menu: {str(e)}")
                            # Fall back to AI simulation
                            menu_placeholder.info("⏳ Generating AI menu simulation...")
                            with st.spinner(f"🤖 Generating menu for {name}..."):
                                menu = simulate_menu(
                                    restaurant_name=name,
                                    cuisine_type=detected_cuisine
                                )
                                menu_source = "AI-Simulated"
                        
                        # Clear the placeholder
                        menu_placeholder.empty()

                        # Make sure we have a menu before analyzing
                        if menu:

                            with st.spinner("🤝 Analyzing menu with your CGM data..."):
                                # Make sure we have glucose data before analyzing
                                if "glucose_summary" in st.session_state and st.session_state["glucose_summary"]:
                                    summary = analyze_menu(str(menu), st.session_state["glucose_summary"])
                                    # Convert CrewOutput to string
                                    summary_str = str(summary)
                                    
                                    # Display the menu with better formatting
                                    st.markdown(f'''
                                    <div class="menu-section">
                                        <div class="menu-title">📋 {menu_source} ({detected_cuisine} Cuisine)</div>
                                        {str(menu).replace("\n", "<br>")}
                                    </div>
                                    ''', unsafe_allow_html=True)
                                    
                                    # Display CGM analysis with better formatting
                                    st.markdown(f'''
                                    <div class="menu-section">
                                        <div class="menu-title">🤝 CGM-Based Recommendations</div>
                                        {summary_str.replace("\n", "<br>").replace("✅", "<span class='cgm-safe'>✅</span>").replace("❌", "<span class='cgm-avoid'>❌</span>").replace("🤝", "<span class='cgm-combo'>🤝</span>")}
                                    </div>
                                    ''', unsafe_allow_html=True)
                                else:
                                    # Display just the menu without analysis if no CGM data
                                    st.markdown(f'''
                                    <div class="menu-section">
                                        <div class="menu-title">📋 {menu_source} ({detected_cuisine} Cuisine)</div>
                                        {str(menu).replace("\n", "<br>")}
                                    </div>
                                    ''', unsafe_allow_html=True)
                                    
                                    st.warning("Please upload and analyze your CGM report in the Home tab to get personalized recommendations.")
                        
                        # Add Google Maps link
                        map_url = f"https://www.google.com/maps/search/?api=1&query={name.replace(' ', '+')}+{address.replace(' ', '+')}"
                        st.markdown(f'''
                            <a href="{map_url}" target="_blank" class="map-link">📍 Open in Google Maps</a>
                        </div>
                        ''', unsafe_allow_html=True)

# Add helpful tips at the bottom
with st.expander("💡 Tips for using this tool"):
    st.markdown('''
    ### How to get the most out of the Restaurant Finder
    
    1. **Upload your CGM data first** - Go to the Home tab and upload your CGM report to get personalized recommendations
    2. **Try different cuisines** - Select multiple cuisines to see a variety of restaurant options
    3. **Adjust the search radius** - If you don't see enough options, increase the search radius
    4. **Check the CGM analysis** - Look for ✅ Safe Dishes that match your glucose patterns
    5. **Save your favorites** - Use the Google Maps link to save restaurants for later
    
    Remember, the AI-generated menus are simulations based on typical dishes for each cuisine and restaurant. Actual menus may vary.
    ''')

