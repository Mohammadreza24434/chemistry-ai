import streamlit as st
from openai import OpenAI  # نیاز به نصب: pip install openai
import time
from datetime import datetime, timedelta
import hashlib

# ==================== LICENSE SYSTEM CONFIG ====================
OWNER_PASSWORD = "24434"
LICENSE_PREFIX = "CHEM"
SALT = "chem_master_secret_2025"

def create_license():
    expiry = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")
    raw = SALT + expiry
    h = hashlib.md5(raw.encode()).hexdigest().upper()[:12]
    return f"{LICENSE_PREFIX}-{h[:4]}-{h[4:8]}-{h[8:]}"

def check_license(code):
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

# ==================== DEEPSEEK API KEY ====================
try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except KeyError:
    st.error("DEEPSEEK_API_KEY در بخش Secrets پیدا نشد. لطفاً کلید API DeepSeek را وارد کنید.")
    st.stop()

# ایجاد کلاینت سازگار با OpenAI برای DeepSeek
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

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
st.sidebar.markdown("**مدل هوش مصنوعی:** DeepSeek")
if st.sidebar.button("خروج از حساب"):
    st.session_state.authenticated = False
    st.rerun()

SYSTEM_PROMPT = """
You are "ChemiMaster AI", a world-class expert in Chemistry and Chemical Engineering.
Respond in Persian (Farsi).
Rules:
1. Accuracy: Provide technically correct and highly detailed scientific information.
2. Formatting: ALWAYS use LaTeX for chemical formulas, reactions, and math (e.g., $H_2SO_4$, $\Delta G$).
3. Calculations: Show all steps of mathematical problems clearly.
4. Scope: Organic, Inorganic, Physical, Analytical Chemistry, and Unit Operations.
If the question is not related to chemistry or chemical engineering, reply only with:
«ببخشید، فقط سؤالات شیمی و مهندسی شیمی جواب می‌دم. لطفاً در این زمینه بپرس.»
and nothing else.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# نمایش تاریخچه چت
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ورودی کاربر
if prompt := st.chat_input("سوال یا مسئله شیمی خود را اینجا بنویسید..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.info("در حال پردازش با DeepSeek...")

        try:
            # ساخت لیست پیام‌ها برای API (با system prompt در ابتدا)
            api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in st.session_state.messages:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

            # استفاده از مدل deepseek-chat (سریع و قدرتمند)
            # اگر نیاز به استدلال پیچیده‌تر داشتید، به "deepseek-reasoner" تغییر دهید
            response = client.chat.completions.create(
                model="deepseek-chat",          # یا "deepseek-reasoner" برای دقت بالاتر
                messages=api_messages,
                temperature=0.7,
                max_tokens=4096,
                stream=False
            )

            full_response = response.choices[0].message.content.strip()

            if full_response:
                placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                placeholder.error("پاسخ خالی دریافت شد.")

        except Exception as e:
            placeholder.error(f"خطا در ارتباط با DeepSeek: {str(e)}")
            st.error("لطفاً اتصال اینترنت و صحت کلید API را بررسی کنید.")

# فوتر
st.sidebar.markdown("---")
st.sidebar.caption("ChemiMaster AI v4.3 | 2025 - Powered by DeepSeek 🧪")
