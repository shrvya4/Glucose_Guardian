
import streamlit as st
from glucose_cgm_agents import analyze_menu
import pytesseract
from PIL import Image
import fitz
import tempfile
import os

st.set_page_config(page_title="📸 Menu Analyzer", layout="wide")
st.title("📸 Menu Analyzer")

menu_text = ""
uploaded_menu = st.file_uploader("Upload restaurant menu image or PDF", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_menu:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".menu") as tmp_file:
        tmp_file.write(uploaded_menu.read())
        path = tmp_file.name

    ext = uploaded_menu.name.split(".")[-1]

    try:
        with st.spinner("Extracting menu text..."):
            if ext.lower() in ["png", "jpg", "jpeg"]:
                image = Image.open(path)
                menu_text = pytesseract.image_to_string(image)
            elif ext.lower() == "pdf":
                doc = fitz.open(path)
                menu_text = "\n".join([p.get_text() for p in doc])
        st.text_area("📝 Menu Text", menu_text, height=200)
    except Exception as e:
        st.error(f"OCR Failed: {e}")

if st.button("🍽️ Suggest Dishes"):
    if not st.session_state.get("glucose_summary"):
        st.warning("Please analyze your CGM report first.")
    elif menu_text:
        with st.spinner("Analyzing menu..."):
            result = analyze_menu(menu_text, st.session_state["glucose_summary"])
            st.markdown("### 🍴 Suggestions")
            # Convert CrewOutput to string before splitting
            result_str = str(result)
            for line in result_str.split('\n'):
                if line.strip():
                    st.markdown(f"<div style='border:1px solid #eee;padding:10px;border-radius:10px;margin-bottom:10px;'>{line}</div>", unsafe_allow_html=True)
