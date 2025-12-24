import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime, timedelta
import hashlib

# ==================== LICENSE SYSTEM CONFIG ====================
# The password for Admin access to generate licenses
OWNER_PASSWORD = "24434" 
# Prefix for generated codes
LICENSE_PREFIX = "CHEM"
# A secret salt to make hashes unpredictable and secure
SALT = "chem_master_secret_2025"

def create_license():
    """Generates a 30-day license code based on the current date hash."""
    # Current date + 30 days
    expiry = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")
    raw = SALT + expiry
    # Generate MD5 hash and take first 12 characters
    h = hashlib.md5(raw.encode()).hexdigest().upper()[:12]
    return f"{LICENSE_PREFIX}-{h[:4]}-{h[4:8]}-{h[8:]}"

def check_license(code):
    """Verifies if the code matches any valid license for the next 30 days."""
    if not code or not code.startswith(f"{LICENSE_PREFIX}-"):
        return False
    
    clean = code[len(LICENSE_PREFIX)+1:].replace("-", "").upper()
    today = datetime.now().date()
    
    # Check if the code matches any potential valid hash for a 31-day window
    for d in range(0, 31):
        check_date = today + timedelta(days=d)
        expected = hashlib.md5((SALT + check_date.strftime("%Y%m%d")).encode()).hexdigest().upper()[:12]
        if expected == clean:
            return True
    return False

# ==================== UI SETUP & STYLING ====================
st.set_page_config(page_title="ChemiMaster Pro AI", page_icon="🧪", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { border-radius: 8px; height: 3em; font-weight: bold; width: 100%; }
    .auth-container {
        background: white; padding: 30px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;
        max-width: 500px; margin: auto; border: 1px solid #e0e0e0;
    }
    .chat-header { text-align: center; color: #1a365d; margin-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# ==================== AUTHENTICATION STATE ====================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# ==================== LOGIN & ADMIN INTERFACE ====================
if not st.session_state.authenticated:
    st.markdown("<h1 class='chat-header'>🧪 دستیار هوشمند شیمی و مهندسی شیمی</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 ورود کاربران", "⚙️ پنل مدیریت"])
    
    with tab1:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.subheader("فعالسازی دسترسی")
        user_code = st.text_input("کد لایسنس ۳۰ روزه را وارد کنید:", type="password", placeholder="CHEM-XXXX-XXXX-XXXX")
        if st.button("تایید و ورود به اپلیکیشن"):
            if check_license(user_code):
                st.session_state.authenticated = True
                st.success("لایسنس تایید شد. خوش آمدید!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("کد لایسنس نامعتبر یا منقضی شده است.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.subheader("بخش مدیریت ادمین")
        admin_pass = st.text_input("رمز عبور مدیر را وارد کنید:", type="password", key="admin_auth_key")
        if admin_pass == OWNER_PASSWORD:
            st.success("دسترسی مدیریتی تایید شد.")
            if st.button("تولید لایسنس ۳۰ روزه جدید"):
                new_key = create_license()
                st.code(new_key, language=None)
                st.info("این لایسنس به مدت ۳۰ روز از زمان صدور اعتبار دارد.")
        elif admin_pass != "":
            st.error("رمز عبور اشتباه است.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==================== MAIN CHAT INTERFACE ====================
st.title("🧪 ChemiMaster Pro AI")
st.sidebar.success("وضعیت لایسنس: فعال ✅")

if st.sidebar.button("خروج از حساب"):
    st.session_state.authenticated = False
    st.rerun()

# AI Configuration
API_KEY = "" # The environment will provide the API key
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"

SYSTEM_PROMPT = """
You are "ChemiMaster AI", a world-class expert in Chemistry and Chemical Engineering.
Provide highly accurate, technical, and detailed answers.
- Use LaTeX for all chemical formulas and math (e.g., $H_2SO_4$, $PV=nRT$).
- Respond in Persian (Farsi).
- Covered fields: Organic, Inorganic, Analytical, Physical Chemistry, and Chemical Engineering (Unit Operations, Thermodynamics, Reactor Design).
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Message History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input Handling
if prompt := st.chat_input("سوال شیمی خود را اینجا بپرسید..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("در حال پردازش تخصصی..."):
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel(model_name=MODEL_NAME, system_instruction=SYSTEM_PROMPT)
            try:
                response = model.generate_content(prompt)
                full_text = response.text
                st.markdown(full_text)
                st.session_state.messages.append({"role": "assistant", "content": full_text})
            except Exception as e:
                st.error("خطا در برقراری ارتباط با هوش مصنوعی. لطفاً لحظاتی دیگر تلاش کنید.")

st.sidebar.markdown("---")
st.sidebar.caption("ChemiMaster AI v2.5 | 2025")
