import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('google_maps_scraper')

class GoogleMapsScraper:
    def __init__(self, headless=True):
        """Initialize the Google Maps scraper with Chrome webdriver"""
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        
        # Add user agent to avoid detection
        self.options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = None
    
    def start_browser(self):
        """Start the Chrome browser"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            logger.info("Chrome browser started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start Chrome browser: {str(e)}")
            return False
    
    def close_browser(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
    
    def search_restaurant(self, restaurant_name, location=None):
        """Search for a specific restaurant on Google Maps"""
        if not self.driver:
            if not self.start_browser():
                return None
        
        try:
            # Navigate to Google Maps
            self.driver.get("https://www.google.com/maps")
            logger.info("Navigated to Google Maps")
            
            # Wait for search box to load
            wait = WebDriverWait(self.driver, 10)
            search_box = wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
            
            # Create search query
            search_query = restaurant_name
            if location:
                search_query += f" {location}"
            
            # Enter search query
            search_box.clear()
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.ENTER)
            logger.info(f"Searching for: {search_query}")
            
            # Wait for results to load
            time.sleep(3)
            
            # Check if we have results
            results = self.driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
            if not results:
                logger.warning("No restaurant results found")
                return None
            
            # Click on the first result
            results[0].click()
            logger.info("Clicked on first restaurant result")
            
            # Wait for restaurant details to load
            time.sleep(3)
            
            return True
        
        except Exception as e:
            logger.error(f"Error searching for restaurant: {str(e)}")
            return None
    
    def get_restaurant_menu(self):
        """Extract menu items from the restaurant page"""
        if not self.driver:
            logger.error("Browser not started")
            return None
        
        menu_items = []
        menu_categories = {"appetizer": [], "main": [], "dessert": []}
        
        try:
            # Find and click the "Menu" tab
            initial_tabs = self.driver.find_elements(By.CSS_SELECTOR, "div.Gpq6kf.NlVald")
            logger.info(f"Found {len(initial_tabs)} initial tabs")
            
            menu_clicked = False
            for tab in initial_tabs:
                if "menu" in tab.text.strip().lower():
                    tab.click()
                    menu_clicked = True
                    logger.info("Clicked 'Menu' tab")
                    break
            
            if not menu_clicked:
                logger.warning("Could not find 'Menu' tab")
                
                # Try alternative method - look for "View menu" button
                try:
                    view_menu_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'View menu')]")
                    if view_menu_buttons:
                        view_menu_buttons[0].click()
                        menu_clicked = True
                        logger.info("Clicked 'View menu' button")
                        time.sleep(3)
                except Exception as e:
                    logger.error(f"Error clicking 'View menu' button: {str(e)}")
            
            if not menu_clicked:
                # Try to find menu items directly on the page
                logger.info("Trying to find menu items directly on page")
                menu_elements = self.driver.find_elements(By.CSS_SELECTOR, ".Io6YTe.fontBodyMedium.kR99db.fdkmkc")
                
                if menu_elements:
                    for el in menu_elements:
                        text = el.text.strip()
                        if text and len(text) > 3:
                            menu_items.append(text)
                    
                    logger.info(f"Found {len(menu_items)} menu items directly on page")
                    return menu_items, menu_categories
                else:
                    logger.warning("No menu items found directly on page")
                    return None, None
            
            # Wait for category tabs to load
            time.sleep(3)
            
            # Find category tabs
            all_tabs_after = self.driver.find_elements(By.CSS_SELECTOR, "div.Gpq6kf.NlVald")
            logger.info(f"Found {len(all_tabs_after)} total tabs after clicking Menu")
            
            # Exclude the original tabs
            new_tabs = [tab for tab in all_tabs_after if tab not in initial_tabs]
            logger.info(f"Found {len(new_tabs)} category tabs")
            
            # If no category tabs found, try to get menu items directly
            if not new_tabs:
                menu_elements = self.driver.find_elements(By.CSS_SELECTOR, ".Io6YTe.fontBodyMedium.kR99db.fdkmkc")
                
                if menu_elements:
                    for el in menu_elements:
                        text = el.text.strip()
                        if text and len(text) > 3:
                            menu_items.append(text)
                    
                    logger.info(f"Found {len(menu_items)} menu items without categories")
                    return menu_items, menu_categories
            
            # Click each category tab and extract menu items
            for i, tab in enumerate(new_tabs):
                try:
                    tab_text = tab.text.strip().lower()
                    logger.info(f"Clicking category tab {i+1}: {tab_text}")
                    tab.click()
                    time.sleep(2)
                    
                    # Determine category
                    category = "main"  # Default category
                    if any(keyword in tab_text for keyword in ["appetizer", "starter", "small plate"]):
                        category = "appetizer"
                    elif any(keyword in tab_text for keyword in ["dessert", "sweet", "pastry"]):
                        category = "dessert"
                    
                    # Extract menu items for this category
                    content_elements = self.driver.find_elements(By.CSS_SELECTOR, ".Io6YTe.fontBodyMedium.kR99db.fdkmkc")
                    
                    if content_elements:
                        for el in content_elements:
                            text = el.text.strip()
                            if text and len(text) > 3:
                                menu_items.append(text)
                                menu_categories[category].append(text)
                        
                        logger.info(f"Found {len(content_elements)} items in category '{tab_text}'")
                    else:
                        logger.warning(f"No menu items found in category '{tab_text}'")
                
                except Exception as e:
                    logger.error(f"Error processing category tab {i+1}: {str(e)}")
            
            logger.info(f"Total menu items found: {len(menu_items)}")
            return menu_items, menu_categories
        
        except Exception as e:
            logger.error(f"Error extracting menu: {str(e)}")
            return None, None
    
    def get_restaurant_info(self):
        """Get basic information about the restaurant"""
        if not self.driver:
            logger.error("Browser not started")
            return None
        
        try:
            # Get restaurant name
            name_element = self.driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf.lfPIob")
            name = name_element.text.strip() if name_element else "Unknown Restaurant"
            
            # Get address
            address_element = self.driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']")
            address = address_element.text.strip() if address_element else "Address not found"
            
            # Get rating
            rating_element = self.driver.find_element(By.CSS_SELECTOR, "div.F7nice")
            rating_text = rating_element.text.strip() if rating_element else ""
            
            # Extract rating and review count
            rating = "N/A"
            reviews = "0"
            if rating_text:
                parts = rating_text.split()
                if len(parts) >= 1:
                    rating = parts[0]
                if len(parts) >= 2:
                    reviews = parts[1].strip("()")
            
            # Get cuisine type
            cuisine = "Unknown"
            try:
                cuisine_element = self.driver.find_element(By.CSS_SELECTOR, "button[jsaction='pane.rating.category']")
                cuisine = cuisine_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Get price level
            price_level = "$"
            try:
                price_element = self.driver.find_element(By.CSS_SELECTOR, "span.mgr77e")
                price_text = price_element.text.strip()
                if price_text:
                    price_level = price_text
            except NoSuchElementException:
                pass
            
            return {
                "name": name,
                "address": address,
                "rating": rating,
                "reviews": reviews,
                "cuisine": cuisine,
                "price": price_level,
                "url": self.driver.current_url
            }
        
        except Exception as e:
            logger.error(f"Error getting restaurant info: {str(e)}")
            return {
                "name": "Unknown Restaurant",
                "address": "Address not found",
                "rating": "N/A",
                "reviews": "0",
                "cuisine": "Unknown",
                "price": "$",
                "url": self.driver.current_url if self.driver else ""
            }

def get_real_menu_from_google_maps(restaurant_name, location=None):
    """Main function to get a real menu from Google Maps"""
    scraper = GoogleMapsScraper(headless=True)
    
    try:
        if scraper.start_browser() and scraper.search_restaurant(restaurant_name, location):
            # Get restaurant info
            restaurant_info = scraper.get_restaurant_info()
            
            # Get menu
            menu_items, menu_categories = scraper.get_restaurant_menu()
            
            # Format the menu
            if menu_items and len(menu_items) >= 3:
                formatted_menu = "🍽️ Real Menu Items from Google Maps:\n\n"
                
                # If we have categorized items, use those
                has_categories = False
                
                if menu_categories:
                    if menu_categories["appetizer"]:
                        has_categories = True
                        formatted_menu += "🥗 Appetizers:\n"
                        for item in menu_categories["appetizer"][:5]:
                            formatted_menu += f"• {item}\n"
                        formatted_menu += "\n"
                    
                    if menu_categories["main"]:
                        has_categories = True
                        formatted_menu += "🍲 Main Courses:\n"
                        for item in menu_categories["main"][:8]:
                            formatted_menu += f"• {item}\n"
                        formatted_menu += "\n"
                    
                    if menu_categories["dessert"]:
                        has_categories = True
                        formatted_menu += "🍰 Desserts:\n"
                        for item in menu_categories["dessert"][:3]:
                            formatted_menu += f"• {item}\n"
                        formatted_menu += "\n"
                
                # If no categories, just list all items
                if not has_categories:
                    formatted_menu += "Menu Items:\n"
                    for item in menu_items[:15]:
                        formatted_menu += f"• {item}\n"
                    formatted_menu += "\n"
                
                # Add restaurant info
                if restaurant_info:
                    formatted_menu += f"\nRestaurant: {restaurant_info['name']}\n"
                    formatted_menu += f"Address: {restaurant_info['address']}\n"
                    formatted_menu += f"Rating: {restaurant_info['rating']} ({restaurant_info['reviews']} reviews)\n"
                    formatted_menu += f"Cuisine: {restaurant_info['cuisine']}\n"
                    formatted_menu += f"Price: {restaurant_info['price']}\n"
                    formatted_menu += f"View on Google Maps: {restaurant_info['url']}\n"
                
                scraper.close_browser()
                return formatted_menu, True, restaurant_info['url'] if restaurant_info else None
            
            scraper.close_browser()
    
    except Exception as e:
        logger.error(f"Error in get_real_menu_from_google_maps: {str(e)}")
        if scraper.driver:
            scraper.close_browser()
    
    return None, False, None

# For testing
if __name__ == "__main__":
    menu, success, url = get_real_menu_from_google_maps("Olive Garden", "San Francisco")
    if success:
        print(menu)
    else:
        print("Failed to get menu")
