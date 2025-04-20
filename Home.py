
import streamlit as st
from glucose_cgm_agents import extract_pdf_text, run_cgm_analysis
import tempfile
import os
import json

st.set_page_config(page_title="🏠 Glucose Dashboard", layout="wide")

# === Login Form ===
if "user" not in st.session_state:
    with st.form("login_form"):
        username = st.text_input("Enter your username")
        submitted = st.form_submit_button("Login")
        if submitted and username:
            st.session_state["user"] = username
            st.success(f"Welcome back, {username}!")
            st.rerun()
    st.stop()

# === Logout Button ===
st.sidebar.success(f"Logged in as: {st.session_state['user']}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# === File Path for This User ===
user_file = f"data/{st.session_state['user']}.json"
os.makedirs("data", exist_ok=True)

# === Load previously stored glucose summary ===
if "glucose_summary" not in st.session_state:
    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            saved = json.load(f)
            st.session_state["glucose_summary"] = saved.get("summary", "")

# === Custom Styles ===
st.markdown("""
<style>
    .card {
        background-color: #fff;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .highlight {
        background-color: #f9f9f9;
        padding: 1rem;
        border-left: 5px solid #27ae60;
    }
</style>
""", unsafe_allow_html=True)

# === Title ===
st.title("🏠 CGM Dashboard")

# === Upload and Analyze PDF ===
uploaded_file = st.file_uploader("📁 Upload your Dexcom Clarity CGM PDF", type="pdf")

if uploaded_file and st.button("🔍 Analyze"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        pdf_path = tmp_file.name

    with st.spinner("Analyzing CGM Report..."):
        try:
            text = extract_pdf_text(pdf_path)
            summary = run_cgm_analysis(text)
            st.session_state["glucose_summary"] = str(summary)

            with open(user_file, "w") as f:
                json.dump({"summary": str(summary)}, f)

            st.success("✅ Analysis complete and saved to your account!")
        except Exception as e:
            st.error(f"Error: {e}")
    os.remove(pdf_path)

# === Show stored summary ===
if st.session_state.get("glucose_summary"):
    st.markdown("<div class='card highlight'><strong>📊 Glucose Summary:</strong><br>" +
                st.session_state["glucose_summary"].replace("\n", "<br>") + "</div>", unsafe_allow_html=True)


# === Glucose Hacks Section ===
st.markdown("## 💡 Glucose Hacks — Simple. Effective. Science-backed.")

hacks = [
    {"title": "Eat in the Right Order", "icon": "🍽️", "desc": "Eat fiber first, then protein & fats, and finish with starches and sugars to reduce spikes."},
    {"title": "Start with Veggies", "icon": "🥦", "desc": "Begin your meals with vegetables to blunt the glucose impact of the rest of your plate."},
    {"title": "Stop Counting Calories", "icon": "⚖️", "desc": "Not all calories are equal. Nutrients matter more than numbers."},
    {"title": "Savoury Breakfast", "icon": "🍳", "desc": "Start the day with protein, healthy fats, and fiber. Avoid sugary breakfasts."},
    {"title": "All Sugar = Sugar", "icon": "🍬", "desc": "White, brown, or coconut sugar — your body processes them the same. Choose wisely."},
    {"title": "Eat Dessert After Meals", "icon": "🍰", "desc": "Have sweets after a balanced meal, not as a standalone snack."},
    {"title": "Vinegar Hack", "icon": "🥗", "desc": "1 tbsp of vinegar before a meal can reduce glucose spikes by up to 30%."},
    {"title": "Move After Eating", "icon": "🚶‍♂️", "desc": "Walk, clean, or move for 10 mins after meals to reduce glucose spikes."},
    {"title": "Snack Savory", "icon": "🥜", "desc": "Choose protein + fiber snacks (like hummus, eggs, or nuts) over sugar."},
    {"title": "Dress Your Carbs", "icon": "🧀", "desc": "Add fat/protein/fiber to plain carbs to slow glucose absorption."},
    {"title": "Anti-Spike Supplement", "icon": "💊", "desc": "Take before your highest-carb meal to reduce spikes by up to 40%."}
]

# Display 3 hacks per row
for i in range(0, len(hacks), 3):
    cols = st.columns(3)
    for j, col in enumerate(cols):
        if i + j < len(hacks):
            hack = hacks[i + j]
            with col:
                st.markdown(f"""
                    <div style="
                        background-color: #ffffff;
                        border-radius: 15px;
                        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
                        padding: 20px;
                        margin-bottom: 20px;
                        text-align: center;
                        height: 240px;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                    ">
                        <div style="font-size: 40px;">{hack['icon']}</div>
                        <h4 style="margin: 10px 0;">{hack['title']}</h4>
                        <p style="font-size: 14px; color: #444;">{hack['desc']}</p>
                    </div>
                """, unsafe_allow_html=True)
