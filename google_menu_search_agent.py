from crewai import Agent, Task, Crew
import os
import re
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

menu_agent = Agent(
    role="Menu Generator",
    goal="Generate accurate restaurant menus based on cuisine type and restaurant name",
    backstory="""You are an expert in international cuisines and restaurant menus. 
    You understand the authentic dishes of each cuisine and create realistic menu items.
    You can detect the likely cuisine of a restaurant from its name and ensure menu items match that cuisine.""",
    verbose=True,
    llm_config={"model": "gpt-4", "api_key": OPENAI_API_KEY}
)

def detect_cuisine_from_name(restaurant_name):
    """Attempt to detect cuisine from restaurant name as a backup"""
    name_lower = restaurant_name.lower()
    
    cuisine_keywords = {
        "Indian": ["india", "indian", "curry", "spice", "tandoor", "masala", "biryani"],
        "Chinese": ["china", "chinese", "wok", "dragon", "panda", "bamboo", "dynasty"],
        "Italian": ["italy", "italian", "pasta", "pizza", "trattoria", "ristorante", "osteria"],
        "Mexican": ["mexico", "mexican", "taco", "burrito", "cantina", "jalisco"],
        "Japanese": ["japan", "japanese", "sushi", "ramen", "tokyo", "sakura"],
        "Thai": ["thai", "bangkok", "siam"],
        "Mediterranean": ["mediterranean", "greek", "lebanon", "lebanese", "falafel"],
        "Korean": ["korea", "korean", "seoul", "gangnam"],
        "American": ["american", "grill", "diner", "burger", "steakhouse"]
    }
    
    for cuisine, keywords in cuisine_keywords.items():
        if any(keyword in name_lower for keyword in keywords):
            return cuisine
            
    return None

def simulate_menu(restaurant_name, cuisine_type=None):
    # If cuisine type not provided or is empty, try to detect from name
    if not cuisine_type:
        detected_cuisine = detect_cuisine_from_name(restaurant_name)
        cuisine_type = detected_cuisine if detected_cuisine else "International"
    
    cuisine_prompts = {
        "Indian": "Include authentic dishes like curry, naan, biryani, tandoori items, chaat, dosa",
        "Chinese": "Include authentic dishes like dim sum, stir-fries, noodles, rice dishes, dumplings",
        "Italian": "Include authentic dishes like pasta, pizza, risotto, antipasti, bruschetta, tiramisu",
        "Mexican": "Include authentic dishes like tacos, enchiladas, burritos, quesadillas, mole, guacamole",
        "Japanese": "Include authentic dishes like sushi, ramen, tempura, teriyaki dishes, udon, sashimi",
        "Thai": "Include authentic dishes like pad thai, curry, tom yum, satay, larb, som tam",
        "Mediterranean": "Include authentic dishes like hummus, falafel, kebab, shawarma, tabbouleh, dolma",
        "Korean": "Include authentic dishes like bibimbap, bulgogi, kimchi dishes, Korean BBQ, japchae",
        "American": "Include authentic dishes like burgers, steaks, sandwiches, salads, mac and cheese",
        "International": "Include a variety of popular dishes from different cuisines"
    }

    cuisine_prompt = cuisine_prompts.get(cuisine_type, cuisine_prompts["International"])
    
    task = Task(
        description=f"""Generate a realistic menu for '{restaurant_name}'.
        This is specifically a {cuisine_type} restaurant.
        {cuisine_prompt}.
        Include appetizers, main courses, and desserts.
        List 8-10 popular dishes that would be found in this type of restaurant.
        Make sure all dishes are authentic to {cuisine_type} cuisine.
        Format as a clean bullet list with emoji icons for each category.
        
        For example:
        🥗 Appetizers:
        • [Appetizer 1]
        • [Appetizer 2]
        
        🍲 Main Courses:
        • [Main Course 1]
        • [Main Course 2]
        
        🍰 Desserts:
        • [Dessert 1]
        • [Dessert 2]
        """,
        expected_output=f"Authentic {cuisine_type} restaurant menu with categorized dishes",
        agent=menu_agent
    )

    crew = Crew(agents=[menu_agent], tasks=[task])
    return crew.kickoff()
