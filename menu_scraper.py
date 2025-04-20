import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import openai
import os

# Load API Keys
SERP_API_KEY = os.getenv("SERPAPI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# 🔍 Step 1: Search Google for menu links using SerpAPI
def search_menu_link(restaurant_name, location):
    query = f"{restaurant_name} {location} menu"
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "hl": "en"
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        links = [r.get("link") for r in results.get("organic_results", [])]

        print("🔍 SerpAPI Search Results:")
        for link in links:
            print(link)

        for r in results.get("organic_results", []):
            title = r.get("title", "").lower()
            url = r.get("link", "")
            if "menu" in title or "menu" in url:
                return url
        return None
    except Exception as e:
        print(f"❌ SerpAPI error: {e}")
        return None


# 🧼 Step 2: Scrape the menu text from the found link
def scrape_menu_from_link(menu_url):
    try:
        response = requests.get(menu_url, headers=HEADERS, timeout=10)
        print(f"📄 Scraping: {menu_url}")
        print("🧾 HTML Preview:", response.text[:500])

        soup = BeautifulSoup(response.text, "html.parser")
        dishes = []

        for tag in soup.find_all(["li", "p", "span", "div"]):
            text = tag.get_text(strip=True)
            if (
                text
                and 4 < len(text) < 60
                and any(word in text.lower() for word in [
                    "chicken", "paneer", "rice", "tikka", "noodle", "wrap",
                    "soup", "biryani", "tofu", "salad", "vada", "idly", "roll", "pizza", "pasta"
                ])
            ):
                dishes.append(text)

        dishes = list(dict.fromkeys(dishes))  # remove duplicates
        return "\n".join(dishes[:15]) if dishes else "⚠️ No menu items found."

    except Exception as e:
        return f"⚠️ Error scraping menu: {e}"


# 🧠 Step 3: Fallback — Generate a realistic menu using GPT
def simulate_menu_with_gpt(restaurant_name, cuisine):
    prompt = f"""
    Simulate a realistic menu for a restaurant called '{restaurant_name}' that serves {cuisine} food.
    Return a bullet list of 10 dishes only. No explanations.
    """
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250
        )
        return res["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ GPT fallback failed: {e}"
