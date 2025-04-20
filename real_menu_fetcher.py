import requests
import os
import json
import re
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('real_menu_fetcher')

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

def get_place_details(place_id):
    """
    Get detailed information about a place using Google Places API
    """
    try:
        url = f"https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': place_id,
            'fields': 'name,website,url,formatted_address,formatted_phone_number,price_level,rating,reviews,photos',
            'key': GOOGLE_API_KEY
        }
        
        logger.info(f"Fetching place details for place_id: {place_id}")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.error(f"API Error: Status {response.status_code}")
            return None
            
        data = response.json()
        
        if 'error_message' in data:
            logger.error(f"API Error: {data['error_message']}")
            return None
            
        result = data.get('result', {})
        logger.info(f"Successfully retrieved place details for: {result.get('name', 'Unknown place')}")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching place details: {str(e)}")
        return None

def fetch_from_yelp(restaurant_name, location):
    """
    Try to fetch menu information from Yelp
    Note: This is a simplified version that doesn't use the actual Yelp API
    but instead scrapes public Yelp pages
    """
    try:
        # Format the search query for Yelp
        search_query = f"{restaurant_name} {location} site:yelp.com"
        
        # Use Google Search to find the Yelp page
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": search_query,
            "api_key": SERPAPI_API_KEY
        }
        
        logger.info(f"Searching for Yelp page: {search_query}")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.warning(f"SerpAPI search failed: {response.status_code}")
            return None
            
        data = response.json()
        organic_results = data.get('organic_results', [])
        
        yelp_url = None
        for result in organic_results:
            if 'yelp.com' in result.get('link', ''):
                yelp_url = result.get('link')
                break
                
        if not yelp_url:
            logger.warning("No Yelp page found")
            return None
            
        # Now fetch the Yelp page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Fetching Yelp page: {yelp_url}")
        response = requests.get(yelp_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Failed to fetch Yelp page: {response.status_code}")
            return None
            
        # Parse the page to find menu items
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for menu section
        menu_section = soup.find('section', {'aria-label': 'Menu'}) or soup.find('section', {'data-testid': 'menu-section'})
        
        if not menu_section:
            # Try to find any section that might contain menu items
            menu_section = soup.find('section', string=lambda text: text and 'menu' in text.lower())
            
        if not menu_section:
            logger.warning("No menu section found on Yelp page")
            return None
            
        # Extract menu items
        menu_items = []
        menu_categories = {}
        
        # Look for menu item elements
        item_elements = menu_section.find_all(['div', 'li'], class_=lambda c: c and ('menu-item' in str(c).lower() or 'dish-name' in str(c).lower()))
        
        if not item_elements:
            # Try a more general approach
            item_elements = menu_section.find_all(['h4', 'h5', 'p'])
            
        for item in item_elements:
            text = item.get_text().strip()
            if text and len(text) > 5 and len(text) < 100:
                menu_items.append(text)
                
        if menu_items:
            logger.info(f"Found {len(menu_items)} menu items on Yelp")
            return {
                'items': menu_items,
                'source': 'Yelp',
                'url': yelp_url
            }
            
        return None
        
    except Exception as e:
        logger.error(f"Error fetching from Yelp: {str(e)}")
        return None

def search_for_menu(restaurant_name, location):
    """
    Search for a restaurant menu using Serper API (Google Search API alternative)
    """
    if not SERPER_API_KEY:
        logger.warning("No Serper API key found. Please add SERPER_API_KEY to your .env file.")
        return None
        
    try:
        url = "https://google.serper.dev/search"
        
        # Create a more specific search query
        query = f"{restaurant_name} restaurant menu {location}"
        logger.info(f"Searching for menu with query: {query}")
        
        payload = json.dumps({
            "q": query,
            "gl": "us",
            "hl": "en",
            "num": 10  # Increased from 5 to get more results
        })
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.request("POST", url, headers=headers, data=payload)
        
        if response.status_code != 200:
            logger.error(f"Serper API Error: Status {response.status_code}")
            return None
            
        data = response.json()
        
        # Look for menu in organic results
        organic_results = data.get('organic', [])
        menu_sites = [
            'allmenus.com', 'menupages.com', 'grubhub.com', 'doordash.com', 
            'ubereats.com', 'seamless.com', 'zomato.com', 'yelp.com',
            'openmenu.com', 'menuism.com', 'singleplatform.com', 'tripadvisor.com',
            'foursquare.com', 'restaurantji.com', 'zmenu.com', 'menu.com'
        ]
        
        # First, prioritize results from known menu sites
        for result in organic_results:
            title = result.get('title', '').lower()
            link = result.get('link', '')
            snippet = result.get('snippet', '').lower()
            
            # Check if this result might contain a menu
            if ('menu' in title or 'menu' in snippet) and any(site in link for site in menu_sites):
                logger.info(f"Found menu on a known menu site: {link}")
                return {
                    'title': result.get('title'),
                    'link': link,
                    'source': 'search',
                    'snippet': snippet
                }
        
        # If no menu found on known sites, try the restaurant's own website
        for result in organic_results:
            title = result.get('title', '').lower()
            link = result.get('link', '')
            snippet = result.get('snippet', '').lower()
            
            # Check if this might be the restaurant's official site with a menu
            if restaurant_name.lower() in link.lower() and ('menu' in title or 'menu' in snippet):
                logger.info(f"Found possible menu on restaurant's own site: {link}")
                return {
                    'title': result.get('title'),
                    'link': link,
                    'source': 'restaurant website',
                    'snippet': snippet
                }
        
        # If still no menu found, try any result that mentions menu
        for result in organic_results:
            title = result.get('title', '').lower()
            link = result.get('link', '')
            snippet = result.get('snippet', '').lower()
            
            if 'menu' in title or 'menu' in snippet:
                logger.info(f"Found possible menu on general site: {link}")
                return {
                    'title': result.get('title'),
                    'link': link,
                    'source': 'general search',
                    'snippet': snippet
                }
        
        logger.warning(f"No menu found for {restaurant_name} in {location}")
        return None
        
    except Exception as e:
        logger.error(f"Error searching for menu: {str(e)}")
        return None

def search_for_menu_with_serpapi(restaurant_name, location):
    """
    Alternative search using SerpAPI
    """
    if not SERPAPI_API_KEY:
        logger.warning("No SerpAPI key found. Skipping this search method.")
        return None
        
    try:
        url = "https://serpapi.com/search.json"
        
        params = {
            "q": f"{restaurant_name} menu {location}",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "num": 10,
            "api_key": SERPAPI_API_KEY
        }
        
        logger.info(f"Searching with SerpAPI for: {restaurant_name} menu")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.error(f"SerpAPI Error: Status {response.status_code}")
            return None
            
        data = response.json()
        
        # Look for menu in organic results
        organic_results = data.get('organic_results', [])
        menu_sites = [
            'allmenus.com', 'menupages.com', 'grubhub.com', 'doordash.com', 
            'ubereats.com', 'seamless.com', 'zomato.com', 'yelp.com',
            'openmenu.com', 'menuism.com', 'singleplatform.com', 'tripadvisor.com'
        ]
        
        for result in organic_results:
            title = result.get('title', '').lower()
            link = result.get('link', '')
            snippet = result.get('snippet', '').lower()
            
            # Check if this result might contain a menu
            if ('menu' in title or 'menu' in snippet) and any(site in link for site in menu_sites):
                logger.info(f"SerpAPI found menu on: {link}")
                return {
                    'title': result.get('title'),
                    'link': link,
                    'source': 'SerpAPI search',
                    'snippet': snippet
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error with SerpAPI: {str(e)}")
        return None

def extract_menu_items_from_website(url):
    """
    Try to extract menu items from a restaurant website
    This is a simplified version and may not work for all websites
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Attempting to extract menu from: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.warning(f"Failed to fetch website: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # First, check for structured menu data
        menu_data = None
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and ('menu' in data or 'hasMenu' in data or 'Menu' in str(data)):
                    menu_data = data
                    break
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and ('menu' in item or 'hasMenu' in item or 'Menu' in str(item)):
                            menu_data = item
                            break
                    if menu_data:
                        break
            except:
                continue
                
        if menu_data:
            logger.info("Found structured menu data in JSON-LD")
            menu_items = []
            # Try to extract menu items from the structured data
            if 'hasMenuSection' in menu_data:
                for section in menu_data['hasMenuSection']:
                    if 'hasMenuItem' in section:
                        for item in section['hasMenuItem']:
                            if 'name' in item:
                                menu_items.append(item['name'])
            elif 'menu' in menu_data and 'items' in menu_data['menu']:
                for item in menu_data['menu']['items']:
                    if 'name' in item:
                        menu_items.append(item['name'])
                        
            if len(menu_items) >= 3:
                logger.info(f"Extracted {len(menu_items)} menu items from structured data")
                return menu_items, {}
        
        # Look for common menu section identifiers
        menu_keywords = ['menu', 'food', 'appetizer', 'entree', 'main', 'dessert', 'dinner', 'lunch', 'breakfast', 'dish']
        menu_sections = soup.find_all(['section', 'div', 'ul', 'nav'], 
                                    class_=lambda c: c and any(keyword in str(c).lower() for keyword in menu_keywords))
        
        # Also look for elements with menu-related IDs
        for id_keyword in menu_keywords:
            elements = soup.find_all(id=lambda i: i and id_keyword in str(i).lower())
            if elements:
                menu_sections.extend(elements)
        
        if not menu_sections:
            # Try looking for headers that might indicate menu sections
            menu_headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], 
                                       string=lambda s: s and any(keyword in s.lower() for keyword in menu_keywords))
            
            if menu_headers:
                menu_sections = [header.parent for header in menu_headers]
        
        # If still no menu sections found, try to find any div with 'menu' in its text
        if not menu_sections:
            menu_divs = [div for div in soup.find_all('div') 
                        if div.get_text() and 'menu' in div.get_text().lower() 
                        and len(div.get_text()) < 5000]  # Avoid entire page content
            menu_sections = menu_divs
        
        if not menu_sections:
            logger.warning(f"No menu sections found on {url}")
            return None
            
        menu_items = []
        categories = {}
        
        for section in menu_sections:
            # Try to identify the category of this section
            section_text = section.get_text().lower()
            category = None
            
            if any(word in section_text for word in ['appetizer', 'starter', 'small plate']):
                category = 'appetizer'
            elif any(word in section_text for word in ['main', 'entree', 'dinner']):
                category = 'main'
            elif any(word in section_text for word in ['dessert', 'sweet', 'pastry']):
                category = 'dessert'
            
            # Look for list items, divs with prices, or other common menu item patterns
            items = section.find_all(['li', 'div', 'article'], 
                                   class_=lambda c: c and any(word in str(c).lower() 
                                                            for word in ['item', 'dish', 'food', 'menu-item', 'product']))
            
            if not items:
                # Try a more general approach - look for elements with prices
                price_pattern = re.compile(r'\$\d+\.\d{2}|\$\d+')
                items = [elem for elem in section.find_all(['div', 'li', 'p', 'span']) 
                         if price_pattern.search(elem.get_text())]
            
            if not items:
                # Most general approach - just get paragraphs and list items
                items = section.find_all(['li', 'p'])
                
            for item in items:
                text = item.get_text().strip().replace('\n', ' ').replace('\t', ' ')
                # Remove excessive whitespace
                text = re.sub(r'\s+', ' ', text)
                
                if len(text) > 10 and len(text) < 200:  # Reasonable length for a menu item
                    menu_items.append(text)
                    if category:
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(text)
        
        # Remove duplicates and very short items
        menu_items = list(set([item for item in menu_items if len(item) > 10]))
        
        if len(menu_items) >= 3:
            logger.info(f"Extracted {len(menu_items)} menu items from HTML")
            return menu_items, categories
            
        logger.warning(f"Not enough menu items found on {url}")
        return None, None
        
    except Exception as e:
        logger.error(f"Error extracting menu items: {str(e)}")
        return None, None

def get_real_menu(restaurant_name, address, place_id=None):
    """
    Main function to get a real menu for a restaurant
    Falls back to different methods if one fails
    """
    menu_items = None
    menu_categories = None
    menu_source = None
    menu_url = None
    
    logger.info(f"Attempting to find real menu for: {restaurant_name} at {address}")
    
    # Step 1: Try to fetch from Yelp first (often has the most reliable menus)
    location_terms = address.split(',')[0] if address else ""
    try:
        yelp_result = fetch_from_yelp(restaurant_name, location_terms)
        if yelp_result:
            menu_items = yelp_result.get('items')
            if menu_items and len(menu_items) >= 3:
                menu_source = "Yelp"
                menu_url = yelp_result.get('url')
                logger.info(f"Successfully found menu on Yelp with {len(menu_items)} items")
    except Exception as e:
        logger.error(f"Error fetching from Yelp: {str(e)}")
    
    # Step 2: If no Yelp menu, try to get place details and website
    if not menu_items and place_id:
        try:
            place_details = get_place_details(place_id)
            if place_details:
                website = place_details.get('website')
                if website:
                    result = extract_menu_items_from_website(website)
                    if result is not None and isinstance(result, tuple) and len(result) == 2:
                        menu_items, menu_categories = result
                        if menu_items:
                            menu_source = "Restaurant's official website"
                            menu_url = website
                            logger.info(f"Successfully found menu on restaurant website with {len(menu_items)} items")
        except Exception as e:
            logger.error(f"Error extracting from restaurant website: {str(e)}")
    
    # Step 3: If no menu found yet, try searching with Serper API
    if not menu_items:
        try:
            search_result = search_for_menu(restaurant_name, location_terms)
            if search_result:
                menu_url = search_result.get('link')
                if menu_url:
                    result = extract_menu_items_from_website(menu_url)
                    if result is not None and isinstance(result, tuple) and len(result) == 2:
                        menu_items, menu_categories = result
                        if menu_items:
                            menu_source = search_result.get('source', 'Online search')
                            logger.info(f"Successfully found menu via Serper search with {len(menu_items)} items")
        except Exception as e:
            logger.error(f"Error with Serper search: {str(e)}")
    
    # Step 4: Try with SerpAPI as a last resort
    if not menu_items:
        try:
            serpapi_result = search_for_menu_with_serpapi(restaurant_name, location_terms)
            if serpapi_result:
                menu_url = serpapi_result.get('link')
                if menu_url:
                    result = extract_menu_items_from_website(menu_url)
                    if result is not None and isinstance(result, tuple) and len(result) == 2:
                        menu_items, menu_categories = result
                        if menu_items:
                            menu_source = serpapi_result.get('source', 'SerpAPI search')
                            logger.info(f"Successfully found menu via SerpAPI with {len(menu_items)} items")
        except Exception as e:
            logger.error(f"Error with SerpAPI search: {str(e)}")
    
    # Format the menu if we found one
    if menu_items and len(menu_items) >= 3:
        formatted_menu = "🍽️ Real Menu Items:\n\n"
        appetizers = []
        mains = []
        desserts = []
        has_categorized_items = False
        
        # If we have categorized items from the website extraction, use those
        if menu_categories and any(len(items) > 0 for items in menu_categories.values()):
            has_categorized_items = True
            if 'appetizer' in menu_categories and menu_categories['appetizer']:
                formatted_menu += "🥗 Appetizers:\n"
                for item in menu_categories['appetizer'][:5]:  # Limit to 5 items per category
                    formatted_menu += f"• {item}\n"
                formatted_menu += "\n"
                
            if 'main' in menu_categories and menu_categories['main']:
                formatted_menu += "🍲 Main Courses:\n"
                for item in menu_categories['main'][:8]:  # Show more main courses
                    formatted_menu += f"• {item}\n"
                formatted_menu += "\n"
                
            if 'dessert' in menu_categories and menu_categories['dessert']:
                formatted_menu += "🍰 Desserts:\n"
                for item in menu_categories['dessert'][:3]:
                    formatted_menu += f"• {item}\n"
                formatted_menu += "\n"
        else:
            # Group items into categories if possible
            appetizer_keywords = ['appetizer', 'starter', 'small plate', 'salad', 'soup', 'side']
            dessert_keywords = ['dessert', 'sweet', 'cake', 'ice cream', 'chocolate', 'pudding', 'pie']
            main_keywords = ['entree', 'main', 'plate', 'special', 'signature', 'house']
            
            for item in menu_items:
                item_lower = item.lower()
                if any(keyword in item_lower for keyword in appetizer_keywords):
                    appetizers.append(item)
                elif any(keyword in item_lower for keyword in dessert_keywords):
                    desserts.append(item)
                elif any(keyword in item_lower for keyword in main_keywords):
                    mains.append(item)
                else:
                    # If we can't categorize it, assume it's a main course
                    mains.append(item)
            
            # Add categorized items
            if appetizers:
                has_categorized_items = True
                formatted_menu += "🥗 Appetizers:\n"
                for item in appetizers[:5]:  # Limit to 5 items per category
                    formatted_menu += f"• {item}\n"
                formatted_menu += "\n"
                
            if mains:
                has_categorized_items = True
                formatted_menu += "🍲 Main Courses:\n"
                for item in mains[:8]:  # Show more main courses
                    formatted_menu += f"• {item}\n"
                formatted_menu += "\n"
                
            if desserts:
                has_categorized_items = True
                formatted_menu += "🍰 Desserts:\n"
                for item in desserts[:3]:
                    formatted_menu += f"• {item}\n"
                formatted_menu += "\n"
        
        # If we couldn't categorize anything, just list all items
        if not has_categorized_items:
            formatted_menu += "Menu Items:\n"
            for item in menu_items[:15]:  # Limit to 15 items total
                formatted_menu += f"• {item}\n"
            formatted_menu += "\n"
            
        # Add source information
        if menu_source and menu_url:
            formatted_menu += f"\nMenu source: {menu_source}\n"
            formatted_menu += f"View full menu: {menu_url}\n"
            
        logger.info(f"Successfully formatted real menu with source: {menu_source}")
        return formatted_menu, True, menu_url
    
    # Return None if no menu found
    logger.warning(f"Could not find a real menu for {restaurant_name}")
    return None, False, None
