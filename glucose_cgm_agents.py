
from crewai import Agent, Task, Crew
import fitz  # PyMuPDF
from dotenv import load_dotenv
import os

# === Load API Key ===
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# === Step 1: Read the PDF ===
def extract_pdf_text(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# === Step 2: Setup Your Agents ===
llm_config = {"model": "gpt-3.5-turbo", "api_key": os.getenv("OPENAI_API_KEY")}

extractor = Agent(
    role="Extractor Agent",
    goal="Extract food items and glucose readings from CGM text, identifying the impact of each meal.",
    backstory="You are a skilled medical assistant that processes CGM data and identifies glucose responses to specific foods.",
    verbose=True,
    llm_config=llm_config
)

analyzer = Agent(
    role="Analyzer Agent",
    goal="Identify which specific food items and combinations caused glucose spikes or were glucose-friendly.",
    backstory="You are a nutrition-aware analyst who can interpret blood sugar effects caused by real meals.",
    verbose=True,
    llm_config=llm_config
)

reporter = Agent(
    role="Reporter Agent",
    goal="Create a personalized glucose report using specific meal names, glucose readings, and helpful insights.",
    backstory="You explain food-glucose patterns in a friendly, clear way to help users eat better.",
    verbose=True,
    llm_config=llm_config
)

menu_analyzer = Agent(
    role="Menu Advisor",
    goal="Review restaurant menus and recommend or avoid items based on user's personal glucose history.",
    backstory="You understand how specific ingredients affect glucose for this unique person and suggest smart, stable choices.",
    verbose=True,
    llm_config=llm_config
)

# === Step 3: Define CGM Report Agent Workflow ===
def run_cgm_analysis(pdf_text):
    task1 = Task(
        description=(
            "From the Dexcom Clarity CGM report text, extract a structured list of meals and their glucose readings.\n"
            "- Include meal type (breakfast, lunch, dinner, snack)\n"
            "- Food items eaten\n"
            "- Glucose level recorded after each meal\n"
            "- Label each entry as either 'spike' (>140 mg/dL) or 'friendly' (70–130 mg/dL)\n"
            "**Only extract meals from the text. Do NOT create or assume foods. Do not add examples that are not present in the text.**\n\n"
            "Return something like:\n"
            "Lunch: Chickpeas salad + roti paneer → 150 mg/dL (spike)"
        ),
        expected_output="Detailed meal list with glucose values and classification",
        agent=extractor
    )

    task2 = Task(
        description=(
            "Based on the extracted meals and glucose readings, analyze:\n"
            "- Identify which specific foods caused spikes or were friendly\n"
            "- Look for patterns or combos that help\n"
            "- Only use meals present in the original Dexcom report — do not generate or assume extra foods."
        ),
        expected_output="List of spike-triggering foods and stable-food combos",
        agent=analyzer,
        context=[task1]
    )

    task3 = Task(
        description=(
            "Write a glucose report for the user.\n"
            "- Use ONLY the meals extracted from the CGM report\n"
            "- Do NOT mention meals like pasta, spaghetti, etc., unless they are explicitly mentioned in the data.\n"
            "- Your job is to help the user understand how their real food impacted their glucose."
        ),
        expected_output="Full user-friendly glucose summary with personalized advice",
        agent=reporter,
        context=[task2]
    )

    crew = Crew(
        agents=[extractor, analyzer, reporter],
        tasks=[task1, task2, task3],
        verbose=True
    )

    result = crew.kickoff()
    return result

# === Step 4: Menu Analyzer Based on Personal CGM Pattern ===
def analyze_menu(menu_text, user_glucose_summary):
    task = Task(
        description=(
            "You are given the following:\n\n"
            f"🧠 User's glucose history summary:\n{user_glucose_summary}\n\n"
            f"📋 Restaurant Menu:\n{menu_text}\n\n"
            "Your job:\n"
            "- Match menu items with foods that previously caused glucose spikes (flag these ❌)\n"
            "- Match menu items with foods that were friendly (mark these ✅)\n"
            "- Suggest safer alternatives or combinations (e.g., 'grilled chicken + greens' instead of 'paneer wrap')\n"
            "- Use knowledge of carbs, sugar, fiber, and ingredients to make intelligent suggestions.\n\n"
            "Return result in this format:\n\n"
            "✅ Safe Dishes:\n- Dish – why it’s safe\n\n"
            "❌ Avoid:\n- Dish – matches your spike foods or contains risky ingredients\n\n"
            "🧠 Smart Combos:\n- Combo – why it helps with glucose stability"
        ),
        expected_output="Safe, avoid, and smart combos based on personal glucose history",
        agent=menu_analyzer
    )

    crew = Crew(
        agents=[menu_analyzer],
        tasks=[task],
        verbose=True
    )

    return crew.kickoff()
