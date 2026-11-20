import streamlit as st
from datetime import datetime
import random
import sqlite3
import pandas as pd

# رمز الدخول الخاص بقسم المدير
MANAGER_PIN = "MGR-2026"

# 1. إعداد قاعدة البيانات المحلية (SQLite)
conn = sqlite3.connect('enterprise_helpdesk_dept_field_v2.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        customer_name TEXT,
        customer_dept TEXT,
        customer_phone TEXT,
        device_sn TEXT,
        device_type TEXT,
        brand TEXT,
        specs_summary TEXT,
        issues_summary TEXT,
        tech_notes TEXT,
        priority TEXT,
        decision TEXT,
        stage TEXT,
        payment_status TEXT,
        ticket_date TEXT,
        technician_name TEXT,
        cost_est TEXT
    )
''')
conn.commit()


def generate_unique_ticket_id():
    while True:
        tid = f"TK-{random.randint(10000, 99999)}"
        cursor.execute("SELECT 1 FROM tickets WHERE ticket_id = ?", (tid,))
        if not cursor.fetchone():
            return tid


def format_customer_display(name, dept):
    name_clean = (name or "").strip()
    dept_clean = (dept or "").strip()
    if name_clean and dept_clean:
        return f"{name_clean} - {dept_clean}"
    return name_clean or dept_clean or "غير محدد"


def load_demo_data():
    sample_tickets = [
        (
            "TK-40101", "ريما القحطاني", "قسم الحسابات", "0501122334", "SN-DL-77412",
            "حاسب محمول (Laptop)", "Dell", "4 GB | HDD تقليدي | عمر 4 سنة",
            "بطء/تجمد", "القرص التقليدي يسبب بطئاً ملحوظاً، يُنصح بالترقية إلى SSD فقط.",
            "متوسطة", "ترقية عتاد (SSD)", "قسم الحساب", "غير مدفوع", "2026-11-18",
            "فهد المطيري", "280 ر.س"
        ),
        (
            "TK-40102", "عمر الزهراني", "شؤون الموظفين", "0559988776", "SN-HP-61904",
            "حاسب مكتبي (Desktop)", "HP", "8 GB | SATA SSD | عمر 2 سنة",
            "شبكة/Wi-Fi، تعريف/برنامج", "تم تحديث تعريف كرت الشبكة وإعادة ضبط الاتصال.",
            "عادية", "صيانة برمجية ووقائية", "قسم الصيانة", "غير مدفوع", "2026-11-19",
            "فهد المطيري", "80 ر.س"
        ),
        (
            "TK-40103", "لينا الشهري", "العمليات اللوجستية", "0544433221", "SN-LN-48290",
            "حاسب محمول (Laptop)", "Lenovo", "8 GB | HDD تقليدي | عمر 8 سنة",
            "طقطقة قرص صلب، تعذر الإقلاع", "تلف ميكانيكي في القرص مع تقادم العتاد؛ الاستبدال أنسب عملياً.",
            "عاجلة", "استبدال الجهاز", "قسم الاستقبال", "غير مدفوع", "2026-11-20",
            "فهد المطيري", "3,200 ر.س"
        ),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        sample_tickets
    )
    conn.commit()


# 2. إعدادات الصفحة المتجاوبة مع الجوال (Mobile-Friendly RTL)
st.set_page_config(
    page_title="نظام إدارة مركز الصيانة والدعم الفني",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 3. تنسيق الهوية اللونية (أزرق داكن/نيلي + فيروزي عصري)
st.markdown(
    """
    <style>
    .stApp {
        direction: rtl;
        text-align: right;
        background: linear-gradient(180deg, #f4f7fb 0%, #eef3f9 100%);
    }
    .app-banner {
        background: linear-gradient(135deg, #0f294a 0%, #164e63 100%);
        color: #ffffff;
        padding: 18px 20px;
        border-radius: 14px;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(15, 41, 74, 0.14);
        border-right: 5px solid #22d3ee;
    }
    .app-banner h2 {
        margin: 0 0 6px 0;
        color: #ffffff !important;
        font-size: 22px;
    }
    .app-banner p {
        margin: 0;
        color: #cffafe;
        font-size: 14px;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0e7490 0%, #1d4ed8 100%);
        color: #ffffff;
        border: none;
        font-weight: 600;
        box-shadow: 0 3px 10px rgba(14, 116, 144, 0.25);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #155e75 0%, #1e40af 100%);
        color: #ffffff;
    }
    .stButton > button {
        width: 100%;
        min-height: 46px;
        font-size: 15px;
        border-radius: 10px;
        background-color: #ffffff;
        color: #0f294a;
        border: 1px solid #cbd5e1;
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: 0 2px 6px rgba(15, 41, 74, 0.05);
    }
    div[data-testid="stMetricValue"] {
        font-size: 19px;
        color: #0f294a;
    }
    div[data-testid="stMetricLabel"] {
        color: #475569;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "active_dept" not in st.session_state:
    st.session_state.active_dept = "قسم الاستقبال"

if "draft_ticket_id" not in st.session_state:
    st.session_state.draft_ticket_id = generate_unique_ticket_id()

if "current_ticket_id" not in st.session_state:
    st.session_state.current_ticket_id = None

if "manager_unlocked" not in st.session_state:
    st.session_state.manager_unlocked = False

st.markdown(
    """
    <div class="app-banner">
        <h2>🏢 نظام إدارة الصيانة والدعم الفني</h2>
        <p>تتبع موحد برقم تذكرة واحد من الاستقبال إلى الصيانة ثم الحساب</p>
    </div>
    """,
    unsafe_allow_html=True
)

dept_options = ["قسم الاستقبال", "قسم الصيانة", "قسم الحساب", "قسم المدير", "نبذة عن الموقع"]
selected_dept = st.radio(
    "انتقل بين الأقسام:",
    dept_options,
    index=dept_options.index(st.session_state.active_dept),
    horizontal=True
)
st.session_state.active_dept = selected_dept

df_all = pd.read_sql_query("SELECT * FROM tickets", conn)
if not df_all.empty:
    df_all["customer_display"] = df_all.apply(
        lambda r: format_customer_display(r["customer_name"], r["customer_dept"]), axis=1
    )

# شريط يوضح التذكرة النشطة الحالية ورقمها الثابت أثناء الانتقال
if st.session_state.current_ticket_id and not df_all.empty:
    match_cur = df_all[df_all["ticket_id"] == st.session_state.current_ticket_id]
    if not match_cur.empty:
        cur_row = match_cur.iloc[0]
        st.info(
            f"**التذكرة النشطة:** `{cur_row['ticket_id']}` | "
            f"**العميل:** {cur_row['customer_display']} | "
            f"**القسم الحالي:** `{cur_row['stage']}`"
        )

st.markdown("---")

# ==========================================
# 1. قسم الاستقبال
# ==========================================
if selected_dept == "قسم الاستقبال":
    st.subheader("🛎️ قسم الاستقبال — تسجيل بيانات العميل")
    st.caption("يتم إنشاء رقم تذكرة واحد ثابت يرافق العميل في الصيانة والحساب.")

    active_new_id = st.session_state.draft_ticket_id
    st.success(f"**رقم التذكرة المخصص لهذه العملية:** `{active_new_id}`")

    # اسم العميل وبجانبه القسم في صف واحد
    c_nm, c_dp = st.columns(2)
    with c_nm:
        customer_name = st.text_input("اسم العميل", "ريما القحطاني")
    with c_dp:
        customer_dept = st.text_input("القسم", "قسم الحسابات")

    c_ph, c_sn = st.columns(2)
    with c_ph:
        customer_phone = st.text_input("رقم الجوال / التحويلة", "0501234567")
    with c_sn:
        device_sn = st.text_input("الرقم التسلسلي للجهاز (S/N)", "SN-77412908").strip()

    c_ty, c_br = st.columns(2)
    with c_ty:
        device_type = st.selectbox("نوع الجهاز", ["حاسب محمول (Laptop)", "حاسب مكتبي (Desktop)", "محطة عمل (Workstation)"])
    with c_br:
        brand = st.selectbox("الشركة المصنعة", ["Dell", "HP", "Lenovo", "Apple", "Asus", "أخرى"])

    c_pr, c_dt = st.columns(2)
    with c_pr:
        priority_level = st.selectbox("الأولوية", ["عادية", "متوسطة", "عاجلة"])
    with c_dt:
        ticket_date = st.date_input("تاريخ الاستقبال", datetime.now())

    initial_note = st.text_area(
        "وصف المشكلة من العميل عند الاستقبال:",
        placeholder="مثال: الجهاز بطيء عند فتح البرامج أو يحتاج فحصاً عاماً..."
    )

    go_to_maint = st.checkbox("نقل التذكرة بنفس الرقم إلى قسم الصيانة بعد الحفظ", value=True)

    if st.button("📥 حفظ التذكرة وتحويلها", type="primary"):
        next_stage = "قسم الصيانة" if go_to_maint else "قسم الاستقبال"
        notes_val = initial_note.strip() if initial_note.strip() else "تم تسجيل الجهاز في الاستقبال بانتظار الفحص الفني."

        cursor.execute('''
            INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            active_new_id, customer_name.strip(), customer_dept.strip(), customer_phone,
            device_sn, device_type, brand, "بانتظار فحص المواصفات", "بانتظار تحديد الأعطال",
            notes_val, priority_level, "بانتظار التشخيص", next_stage, "غير مدفوع",
            str(ticket_date), "فهد المطيري", "0 ر.س"
        ))
        conn.commit()

        st.session_state.current_ticket_id = active_new_id
        st.session_state.draft_ticket_id = generate_unique_ticket_id()

        if go_to_maint:
            st.session_state.active_dept = "قسم الصيانة"
            st.rerun()
        else:
            st.success(f"✅ تم حفظ التذكرة برقم `{active_new_id}`.")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 التذاكر المسجلة")
    if df_all.empty:
        st.info("لا توجد تذاكر مسجلة بعد.")
        if st.button("✨ تعبئة بيانات تجريبية للاختبار"):
            load_demo_data()
            st.rerun()
    else:
        disp_df = df_all.rename(columns={
            "ticket_id": "رقم التذكرة",
            "customer_display": "العميل والقسم",
            "device_sn": "الرقم التسلسلي",
            "stage": "القسم الحالي",
            "priority": "الأولوية",
            "ticket_date": "التاريخ"
        })
        st.dataframe(
            disp_df[["رقم التذكرة", "العميل والقسم", "الرقم التسلسلي", "القسم الحالي", "الأولوية", "التاريخ"]],
            use_container_width=True
        )

# ==========================================
# 2. قسم الصيانة
# ==========================================
elif selected_dept == "قسم الصيانة":
    st.subheader("🔧 قسم الصيانة — الفحص والتشخيص الفني")
    st.caption("فحص الجهاز وتحديد الأعطال مع الاحتفاظ بنفس رقم التذكرة ونقلها للحساب.")

    if df_all.empty:
        st.info("📭 لا توجد تذاكر متاحة حالياً.")
        c_b1, c_b2 = st.columns(2)
        if c_b1.button("✨ تعبئة بيانات تجريبية"):
            load_demo_data()
            st.rerun()
        if c_b2.button("🛎️ الذهاب لقسم الاستقبال"):
            st.session_state.active_dept = "قسم الاستقبال"
            st.rerun()
    else:
        ticket_ids = df_all["ticket_id"].tolist()
        default_idx = 0
        if st.session_state.current_ticket_id in ticket_ids:
            default_idx = ticket_ids.index(st.session_state.current_ticket_id)

        def fmt_maint(tid):
            r = df_all[df_all["ticket_id"] == tid].iloc[0]
            return f"{r['ticket_id']} | {r['customer_display']} ({r['stage']})"

        chosen_id = st.selectbox("اختر التذكرة للفحص:", ticket_ids, index=default_idx, format_func=fmt_maint)
        st.session_state.current_ticket_id = chosen_id
        row = df_all[df_all["ticket_id"] == chosen_id].iloc[0]

        with st.container(border=True):
            st.write(f"**رقم التذكرة الثابت:** `{row['ticket_id']}` | **المرحلة الحالية:** `{row['stage']}`")
            st.write(f"**العميل:** {row['customer_name']} | **القسم:** {row['customer_dept']} | **الجوال:** {row['customer_phone']}")
            st.write(f"**الجهاز:** {row['device_type']} — {row['brand']} (`{row['device_sn']}`)")
            st.info(f"**ملاحظات سابقة:** {row['tech_notes']}")

        st.markdown("#### 1️⃣ مواصفات الجهاز أثناء الفحص")
        device_age = st.slider("عمر الجهاز (بالسنوات)", 0, 15, 3)
        c_r, c_s = st.columns(2)
        with c_r:
            ram = st.selectbox("الذاكرة (RAM)", ["4 GB", "8 GB", "16 GB", "32 GB", "64 GB"], index=1)
        with c_s:
            storage = st.selectbox("التخزين", ["
