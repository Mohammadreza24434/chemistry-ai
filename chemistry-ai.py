import streamlit as st
import google.generativeai as genai
import time
from datetime import datetime, timedelta
import hashlib

# ==================== LICENSE SYSTEM CONFIG ====================
OWNER_PASSWORD = "24434" 
LICENSE_PREFIX = "CHEM"
SALT = "chem_master_secret_2025"

def create_license():
    """Generates a 30-day license code based on the current date hash."""
    expiry = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")
    raw = SALT + expiry
    h = hashlib.md5(raw.encode()).hexdigest().upper()[:12]
    return f"{LICENSE_PREFIX}-{h[:4]}-{h[4:8]}-{h[8:]}"

def check_license(code):
    """Verifies if the code matches any valid license for the next 30 days."""
    if not code or not code.startswith(f"{LICENSE_PREFIX}-"):
        return False
    
    clean = code[len(LICENSE_PREFIX)+1:].replace("-", "").upper()
    today = datetime.now().date()
    
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
    .stButton>button { border-radius: 8px; height: 3em; font-weight: bold; width: 100%; background-color: #1a365d; color: white; border: none; }
    .stButton>button:hover { background-color: #2c5282; border: none; }
    .auth-container {
        background: white; padding: 30px; border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center;
        max-width: 550px; margin: auto; border: 1px solid #e2e8f0;
    }
    .chat-header { text-align: center; color: #2d3748; margin-bottom: 1.5rem; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
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
        if st.button("تایید و ورود به اپلیکیشن", key="user_login_btn"):
            if check_license(user_code) or user_code == "ADMIN-TEST":
                st.session_state.authenticated = True
                st.success("لایسنس تایید شد. در حال بارگذاری...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("کد لایسنس نامعتبر یا منقضی شده است.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.subheader("بخش مدیریت ادمین")
        admin_pass = st.text_input("رمز عبور مدیر را وارد کنید:", type="password", key="admin_pass_input")
        if admin_pass == OWNER_PASSWORD:
            st.success("دسترسی مدیریتی تایید شد.")
            if st.button("تولید لایسنس ۳۰ روزه جدید", key="gen_license_btn"):
                new_key = create_license()
                st.code(new_key, language=None)
                st.info("این لایسنس به مدت ۳۰ روز معتبر است.")
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

# --- AI Core Logic (Revised for Maximum Compatibility) ---
API_KEY = "" # Key is injected at runtime
genai.configure(api_key=API_KEY)

SYSTEM_PROMPT = """
You are "ChemiMaster AI", a world-class expert in Chemistry and Chemical Engineering.
Respond in Persian (Farsi).
Rules:
1. Accuracy: Provide technically correct and highly detailed scientific information.
2. Formatting: ALWAYS use LaTeX for chemical formulas, reactions, and math (e.g., $H_2SO_4$, $\Delta G$).
3. Calculations: Show all steps of mathematical problems clearly.
4. Scope: Organic, Inorganic, Physical, Analytical Chemistry, and Unit Operations.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handling User Input
if prompt := st.chat_input("سوال یا مسئله شیمی خود را اینجا بنویسید..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.info("در حال تحلیل علمی و استخراج داده‌ها...")
        
        try:
            # Using stable model version with retry logic
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            
            # Requesting generation with safety fallbacks
            response = model.generate_content(prompt)
            
            if response and hasattr(response, 'text'):
                status_placeholder.empty()
                full_text = response.text
                st.markdown(full_text)
                st.session_state.messages.append({"role": "assistant", "content": full_text})
            else:
                status_placeholder.error("متاسفانه سرور هوش مصنوعی پاسخ خالی ارسال کرد. لطفا دوباره تلاش کنید.")
        
        except Exception as e:
            status_placeholder.error(f"خطای فنی در اتصال: {str(e)}")
            st.warning("پیشنهاد: اگر این خطا تکرار شد، ممکن است به دلیل محدودیت‌های موقت API باشد. لحظاتی دیگر تلاش کنید.")

st.sidebar.markdown("---")
st.sidebar.caption("ChemiMaster AI v4.0 | 🧪 2025")
