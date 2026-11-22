import random
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

MANAGER_PIN = "MGR-2026"

conn = sqlite3.connect("enterprise_helpdesk_bilingual_v1.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        customer_name TEXT,
        reception_staff TEXT,
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
""")
conn.commit()


def generate_unique_ticket_id():
    while True:
        tid = f"TK-{random.randint(10000, 99999)}"
        cursor.execute("SELECT 1 FROM tickets WHERE ticket_id = ?", (tid,))
        if not cursor.fetchone():
            return tid


def load_demo_data():
    sample_tickets = [
        (
            "TK-40101", "ريما القحطاني", "سالم الدوسري", "0501122334", "SN-DL-77412",
            "Laptop", "Dell", "4 GB | HDD | 4 yrs",
            "Slow/Freeze", "HDD causes noticeable slowness; SSD upgrade recommended.",
            "Medium", "SSD Upgrade", "Billing", "Unpaid", "2026-11-18",
            "فهد المطيري", "280 SAR"
        ),
        (
            "TK-40102", "عمر الزهراني", "سالم الدوسري", "0559988776", "SN-HP-61904",
            "Desktop", "HP", "8 GB | SATA SSD | 2 yrs",
            "Network/Wi-Fi, Driver/App", "Updated network driver and reset connection.",
            "Normal", "Software & Preventive", "Maintenance", "Unpaid", "2026-11-19",
            "فهد المطيري", "80 SAR"
        ),
        (
            "TK-40103", "لينا الشهري", "سالم الدوسري", "0544433221", "SN-LN-48290",
            "Laptop", "Lenovo", "8 GB | HDD | 8 yrs",
            "HDD Clicking, Boot Failure", "Mechanical drive issue with aging hardware; replacement is practical.",
            "Urgent", "Device Replacement", "Reception", "Unpaid", "2026-11-20",
            "فهد المطيري", "3,200 SAR"
        ),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        sample_tickets
    )
    conn.commit()


TEXTS = {
    "ar": {
        "page_title": "نظام إدارة مركز الصيانة والدعم الفني",
        "dir": "rtl",
        "align": "right",
        "banner_title": "🏢 نظام إدارة الصيانة والدعم الفني",
        "banner_sub": "تتبع موحد برقم تذكرة واحد من الاستقبال إلى الصيانة ثم الحساب",
        "lang_label": "اللغة / Language",
        "nav_label": "انتقل بين الأقسام:",
        "depts": ["الاستقبال", "الصيانة", "الحساب", "المدير", "نبذة عن الموقع"],
        "stage_map": {
            "Reception": "الاستقبال",
            "Maintenance": "الصيانة",
            "Billing": "الحساب",
            "الاستقبال": "الاستقبال",
            "الصيانة": "الصيانة",
            "الحساب": "الحساب",
        },
        "active_ticket_bar": "**التذكرة النشطة:** `{tid}` | **العميل:** {cust} | **القسم الحالي:** `{stage}`",
        "rec_title": "🛎️ قسم الاستقبال — تسجيل بيانات العميل",
        "rec_caption": "يتم إنشاء رقم تذكرة واحد ثابت يرافق العميل في الصيانة والحساب.",
        "new_tid_msg": "**رقم التذكرة المخصص لهذه العملية:** `{tid}`",
        "cust_name": "اسم العميل",
        "rec_staff": "اسم موظف الاستقبال",
        "mobile": "رقم الجوال",
        "sn": "الرقم التسلسلي للجهاز (S/N)",
        "dev_type": "نوع الجهاز",
        "dev_types": ["حاسب محمول (Laptop)", "حاسب مكتبي (Desktop)", "محطة عمل (Workstation)"],
        "brand": "الشركة المصنعة",
        "brands": ["Dell", "HP", "Lenovo", "Apple", "Asus", "أخرى"],
        "priority": "الأولوية",
        "priorities": ["عادية", "متوسطة", "عاجلة"],
        "rec_date": "تاريخ الاستقبال",
        "init_note": "وصف المشكلة من العميل عند الاستقبال:",
        "init_note_ph": "مثال: الجهاز بطيء عند فتح البرامج أو يحتاج فحصاً عاماً...",
        "go_maint": "نقل التذكرة بنفس الرقم إلى قسم الصيانة بعد الحفظ",
        "save_rec_btn": "📥 حفظ التذكرة وتحويلها",
        "default_rec_note": "تم تسجيل الجهاز في الاستقبال بانتظار الفحص الفني.",
        "saved_rec_msg": "✅ تم حفظ التذكرة برقم `{tid}`.",
        "reg_tickets": "📋 التذاكر المسجلة",
        "no_tickets": "لا توجد تذاكر مسجلة بعد.",
        "load_demo": "✨ تعبئة بيانات تجريبية للاختبار",
        "maint_title": "🔧 قسم الصيانة — الفحص والتشخيص الفني",
        "maint_caption": "فحص الجهاز وتحديد الأعطال مع الاحتفاظ بنفس رقم التذكرة ونقلها للحساب.",
        "no_maint_tickets": "📭 لا توجد تذاكر متاحة حالياً.",
        "go_rec_btn": "🛎️ الذهاب لقسم الاستقبال",
        "pick_ticket_maint": "اختر التذكرة للفحص:",
        "fixed_tid": "**رقم التذكرة الثابت:** `{tid}` | **المرحلة الحالية:** `{stage}`",
        "cust_info_line": "**العميل:** {cust} | **موظف الاستقبال:** {staff} | **رقم الجوال:** {phone}",
        "dev_info_line": "**الجهاز:** {dtype} — {brand} (`{sn}`)",
        "prev_notes": "**ملاحظات سابقة:** {notes}",
        "specs_sec": "#### 1️⃣ مواصفات الجهاز أثناء الفحص",
        "age_lbl": "عمر الجهاز (بالسنوات)",
        "ram_lbl": "الذاكرة (RAM)",
        "stor_lbl": "التخزين",
        "stor_opts": ["HDD تقليدي", "SATA SSD", "NVMe M.2 SSD"],
        "issues_sec": "#### 2️⃣ تحديد الأعطال",
        "tabs": ["⚙️ العتاد", "💻 النظام", "🌐 الشبكة"],
        "c_slow": "بطء ملحوظ أو تجمد متكرر",
        "c_heat": "ارتفاع حرارة أو صوت مروحة مرتفع",
        "c_bsod": "شاشة زرقاء (BSOD) أو إعادة تشغيل",
        "c_noise": "أصوات طقطقة ميكانيكية من القرص الصلب",
        "c_boot": "تعذر الإقلاع أو تلف ملفات النظام",
        "c_virus": "اشتباه برمجيات خبيثة أو إعلانات",
        "c_corrupt": "مشكلة في تعريف أو برنامج معين",
        "c_net": "انقطاع Wi-Fi أو ضعف الاتصال",
        "c_domain": "مشكلة دخول الشبكة المحلية / النطاق",
        "tech_lbl": "اسم فني الصيانة",
        "tech_notes_lbl": "تقرير وملاحظات فني الصيانة:",
        "send_bill": "نقل التذكرة بنفس الرقم إلى قسم الحساب بعد الحفظ",
        "save_diag_btn": "🛠️ حفظ التشخيص ونقل التذكرة",
        "saved_diag_msg": "✅ تم حفظ التشخيص للتذكرة `{tid}`.",
        "bill_title": "💳 قسم الحساب — الفواتير واعتماد الدفع",
        "bill_caption": "استكمال معالجة التذكرة بنفس رقمها واعتماد المبلغ وحالة الدفع.",
        "no_bill_tickets": "📭 لا توجد تذاكر مسجلة في الحساب حالياً.",
        "m_total": "إجمالي التذاكر",
        "m_in_bill": "في قسم الحساب",
        "m_paid": "مدفوع",
        "m_unpaid": "غير مدفوع",
        "filter_stage": "تصفية حسب القسم / المرحلة:",
        "all_opt": "الكل",
        "bill_mgmt": "#### 🧾 إدارة فاتورة التذكرة",
        "pick_ticket_bill": "اختر التذكرة:",
        "final_cost": "المبلغ النهائي (ر.س)",
        "pay_status": "حالة الدفع",
        "pay_opts": ["غير مدفوع", "مدفوع"],
        "move_stage": "إبقاء أو نقل التذكرة بنفس رقمها إلى:",
        "save_bill_btn": "💾 حفظ الفاتورة وتحديث التذكرة",
        "dl_invoice": "📥 تحميل الفاتورة / التقرير (.txt)",
        "dl_csv_bill": "📊 تصدير سجل الحسابات (.csv)",
        "mgr_title": "🔐 قسم المدير — دخول محمي برقم خاص",
        "mgr_warn": "هذا القسم مخصص للمدير ولا يُفتح إلا برقم الدخول الخاص. يمكن لمسؤول التوظيف الاطلاع على الرقم في تبويب «نبذة عن الموقع».",
        "pin_lbl": "أدخل رقم الدخول الخاص بالمدير:",
        "pin_ph": "مثال: MGR-2026",
        "unlock_btn": "🔓 دخول إلى لوحة المدير",
        "pin_ok": "✅ تم التحقق من رقم الدخول بنجاح.",
        "pin_err": "❌ رقم الدخول غير صحيح. راجع «نبذة عن الموقع» لمعرفة رقم الدخول المخصص للتجربة.",
        "lock_btn": "🔒 قفل / خروج من قسم المدير",
        "mgr_caption": "عرض الإحصاءات، رصد تكرار الأجهزة، البحث والتصفية، وحذف أو مسح السجلات.",
        "m_urgent": "تذاكر عاجلة",
        "m_work": "في الصيانة / الحساب",
        "rep_sn": "🔁 **أجهزة ذات تذاكر متكررة:** ",
        "rep_times": "مرات",
        "chart_stage": "#### 📈 توزيع التذاكر حسب القسم",
        "chart_dec": "#### 📈 توزيع التذاكر حسب القرار",
        "search_lbl": "🔎 بحث برقم التذكرة أو اسم العميل أو موظف الاستقبال أو رقم الجوال أو S/N",
        "filt_dept": "تصفية بالقسم",
        "filt_pay": "تصفية بالدفع",
        "pick_del": "اختر تذكرة للإدارة / الحذف:",
        "del_btn": "🗑️ حذف التذكرة المحددة",
        "del_msg": "تم حذف التذكرة `{tid}`.",
        "dl_csv_mgr": "📊 تصدير السجل الكامل (.csv)",
        "add_demo": "✨ إضافة بيانات تجريبية",
        "clear_all": "🗑️ مسح جميع التذاكر",
        "about_title": "📌 نبذة عن الموقع",
        "about_desc": (
            "نظام ويب متكامل لإدارة أعمال الدعم الفني وصيانة الحاسب الآلي برقم تذكرة واحد ثابت عبر المراحل: "
            "الاستقبال <- الصيانة <- الحساب، مع إشراف إداري في قسم المدير "
            "ومنطق تشخيص واقعي وعادل يحدد التوصية المناسبة (صيانة، ترقية، أو استبدال) دون تضخيم الأعطال البسيطة."
        ),
        "mgr_creds_title": "#### 🔑 بيانات دخول قسم المدير (لمسؤولي التوظيف والمستعرضين)",
        "mgr_pin_line": "**رقم الدخول الخاص بالمدير:** `{pin}`",
        "mgr_pin_hint": "انتقل إلى تبويب «المدير» وأدخل الرقم أعلاه لتجربة لوحة الإدارة والإحصاءات.",
        "feats_title": "#### ✨ أبرز مزايا النظام:",
        "feats": [
            "- **رقم تذكرة موحد:** تنتقل التذكرة بنفس الرقم بين الاستقبال والصيانة والحساب.",
            "- **تشخيص تقني عادل:** يعتمد على نوع العطل الفعلي وعمر الجهاز ومواصفاته.",
            "- **إدارة وتقارير:** حفظ في قاعدة بيانات SQLite، رصد تكرار الأعطال، وتصدير .txt و.csv.",
        ],
    },
    "en": {
        "page_title": "IT Helpdesk & Maintenance System",
        "dir": "ltr",
        "align": "left",
        "banner_title": "🏢 IT Helpdesk & Maintenance System",
        "banner_sub": "Single-ticket workflow from Reception to Maintenance and Billing",
        "lang_label": "اللغة / Language",
        "nav_label": "Navigate departments:",
        "depts": ["Reception", "Maintenance", "Billing", "Manager", "About"],
        "stage_map": {
            "الاستقبال": "Reception",
            "الصيانة": "Maintenance",
            "الحساب": "Billing",
            "Reception": "Reception",
            "Maintenance": "Maintenance",
            "Billing": "Billing",
        },
        "active_ticket_bar": "**Active Ticket:** `{tid}` | **Customer:** {cust} | **Current Dept:** `{stage}`",
        "rec_title": "🛎️ Reception — Customer Registration",
        "rec_caption": "A single ticket ID is generated and carried across Maintenance and Billing.",
        "new_tid_msg": "**Ticket ID for this entry:** `{tid}`",
        "cust_name": "Customer Name",
        "rec_staff": "Receptionist Name",
        "mobile": "Mobile Number",
        "sn": "Device Serial Number (S/N)",
        "dev_type": "Device Type",
        "dev_types": ["Laptop", "Desktop", "Workstation"],
        "brand": "Brand",
        "brands": ["Dell", "HP", "Lenovo", "Apple", "Asus", "Other"],
        "priority": "Priority",
        "priorities": ["Normal", "Medium", "Urgent"],
        "rec_date": "Reception Date",
        "init_note": "Customer issue description at reception:",
        "init_note_ph": "Example: System slows down when opening apps or needs checkup...",
        "go_maint": "Send ticket with the same ID to Maintenance after saving",
        "save_rec_btn": "📥 Save Ticket & Forward",
        "default_rec_note": "Registered at reception pending technical inspection.",
        "saved_rec_msg": "✅ Ticket `{tid}` saved.",
        "reg_tickets": "📋 Registered Tickets",
        "no_tickets": "No tickets registered yet.",
        "load_demo": "✨ Load Demo Data",
        "maint_title": "🔧 Maintenance — Inspection & Diagnostics",
        "maint_caption": "Inspect hardware/issues while keeping the same ticket ID and forward to Billing.",
        "no_maint_tickets": "📭 No tickets available right now.",
        "go_rec_btn": "🛎️ Go to Reception",
        "pick_ticket_maint": "Select ticket to inspect:",
        "fixed_tid": "**Ticket ID:** `{tid}` | **Current Stage:** `{stage}`",
        "cust_info_line": "**Customer:** {cust} | **Receptionist:** {staff} | **Mobile:** {phone}",
        "dev_info_line": "**Device:** {dtype} — {brand} (`{sn}`)",
        "prev_notes": "**Previous Notes:** {notes}",
        "specs_sec": "#### 1️⃣ Device Specifications",
        "age_lbl": "Device Age (Years)",
        "ram_lbl": "RAM",
        "stor_lbl": "Storage",
        "stor_opts": ["HDD", "SATA SSD", "NVMe M.2 SSD"],
        "issues_sec": "#### 2️⃣ Select Issues",
        "tabs": ["⚙️ Hardware", "💻 System", "🌐 Network"],
        "c_slow": "Noticeable slowness or frequent freezing",
        "c_heat": "Overheating or loud fan noise",
        "c_bsod": "Blue screen (BSOD) or random restarts",
        "c_noise": "Mechanical clicking noise from drive",
        "c_boot": "Boot failure or corrupted OS files",
        "c_virus": "Suspected malware or pop-up ads",
        "c_corrupt": "Driver or application issue",
        "c_net": "Wi-Fi drops or weak signal",
        "c_domain": "LAN / Domain login issue",
        "tech_lbl": "Technician Name",
        "tech_notes_lbl": "Technician Report & Notes:",
        "send_bill": "Send ticket with the same ID to Billing after saving",
        "save_diag_btn": "🛠️ Save Diagnostics & Forward",
        "saved_diag_msg": "✅ Diagnostics saved for ticket `{tid}`.",
        "bill_title": "💳 Billing — Invoices & Payment",
        "bill_caption": "Manage ticket billing with the same ID, cost, and payment status.",
        "no_bill_tickets": "📭 No tickets in billing yet.",
        "m_total": "Total Tickets",
        "m_in_bill": "In Billing",
        "m_paid": "Paid",
        "m_unpaid": "Unpaid",
        "filter_stage": "Filter by stage:",
        "all_opt": "All",
        "bill_mgmt": "#### 🧾 Ticket Invoice Management",
        "pick_ticket_bill": "Select ticket:",
        "final_cost": "Final Amount (SAR)",
        "pay_status": "Payment Status",
        "pay_opts": ["Unpaid", "Paid"],
        "move_stage": "Keep or move ticket with same ID to:",
        "save_bill_btn": "💾 Save Invoice & Update Stage",
        "dl_invoice": "📥 Download Invoice / Report (.txt)",
        "dl_csv_bill": "📊 Export Billing Log (.csv)",
        "mgr_title": "🔐 Manager — PIN Protected Access",
        "mgr_warn": "Restricted to Manager access. Recruiters can view the demo PIN under the «About» tab.",
        "pin_lbl": "Enter Manager Access PIN:",
        "pin_ph": "Example: MGR-2026",
        "unlock_btn": "🔓 Unlock Manager View",
        "pin_ok": "✅ PIN verified successfully.",
        "pin_err": "❌ Invalid PIN. Check «About» for the demo access PIN.",
        "lock_btn": "🔒 Lock / Exit Manager View",
        "mgr_caption": "View metrics, repeated devices, search/filter, and delete or clear records.",
        "m_urgent": "Urgent Tickets",
        "m_work": "Maintenance / Billing",
        "rep_sn": "🔁 **Repeated Devices:** ",
        "rep_times": "times",
        "chart_stage": "#### 📈 Tickets by Stage",
        "chart_dec": "#### 📈 Tickets by Decision",
        "search_lbl": "🔎 Search by Ticket ID, Customer, Receptionist, Mobile, or S/N",
        "filt_dept": "Filter by Stage",
        "filt_pay": "Filter by Payment",
        "pick_del": "Select ticket to manage / delete:",
        "del_btn": "🗑️ Delete Selected Ticket",
        "del_msg": "Deleted ticket `{tid}`.",
        "dl_csv_mgr": "📊 Export Full Log (.csv)",
        "add_demo": "✨ Add Demo Data",
        "clear_all": "🗑️ Clear All Tickets",
        "about_title": "📌 About This App",
        "about_desc": (
            "A bilingual IT helpdesk and maintenance web app tracking a single ticket ID across "
            "Reception -> Maintenance -> Billing, with a PIN-protected Manager view and fair "
            "diagnostics (maintenance, upgrade, or replacement) without inflating minor issues."
        ),
        "mgr_creds_title": "#### 🔑 Manager Access Credentials (For Recruiters & Reviewers)",
        "mgr_pin_line": "**Manager Access PIN:** `{pin}`",
        "mgr_pin_hint": "Switch to the «Manager» tab and enter the PIN above to test the admin dashboard.",
        "feats_title": "#### ✨ Key Features:",
        "feats": [
            "- **Unified Ticket ID:** Follows the same ticket across Reception, Maintenance, and Billing.",
            "- **Fair Diagnostics:** Evaluates actual issues, device age, and specs without exaggeration.",
            "- **SQLite & Exports:** Persistent storage, repeat-device alerts, and .txt / .csv exports.",
        ],
    },
}

if "lang" not in st.session_state:
    st.session_state.lang = "ar"

if "active_dept_idx" not in st.session_state:
    st.session_state.active_dept_idx = 0

if "draft_ticket_id" not in st.session_state:
    st.session_state.draft_ticket_id = generate_unique_ticket_id()

if "current_ticket_id" not in st.session_state:
    st.session_state.current_ticket_id = None

if "manager_unlocked" not in st.session_state:
    st.session_state.manager_unlocked = False

lang_choice = st.radio(
    "اللغة / Language",
    ["العربية", "English"],
    index=0 if st.session_state.lang == "ar" else 1,
    horizontal=True,
)
st.session_state.lang = "ar" if lang_choice == "العربية" else "en"
t = TEXTS[st.session_state.lang]

st.set_page_config(
    page_title=t["page_title"],
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

border_prop = "border-right: 5px solid #22d3ee;" if t["dir"] == "rtl" else "border-left: 5px solid #22d3ee;"

st.markdown(
    f"""
    <style>
    .stApp {{
        direction: {t["dir"]};
        text-align: {t["align"]};
        background: linear-gradient(180deg, #f4f7fb 0%, #eef3f9 100%);
    }}
    .app-banner {{
        background: linear-gradient(135deg, #0f294a 0%, #164e63 100%);
        color: #ffffff;
        padding: 18px 20px;
        border-radius: 14px;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(15, 41, 74, 0.14);
        {border_prop}
    }}
    .app-banner h2 {{
        margin: 0 0 6px 0;
        color: #ffffff !important;
        font-size: 22px;
    }}
    .app-banner p {{
        margin: 0;
        color: #cffafe;
        font-size: 14px;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #0e7490 0%, #1d4ed8 100%);
        color: #ffffff;
        border: none;
        font-weight: 600;
        box-shadow: 0 3px 10px rgba(14, 116, 144, 0.25);
    }}
    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #155e75 0%, #1e40af 100%);
        color: #ffffff;
    }}
    .stButton > button {{
        width: 100%;
        min-height: 46px;
        font-size: 15px;
        border-radius: 10px;
        background-color: #ffffff;
        color: #0f294a;
        border: 1px solid #cbd5e1;
    }}
    div[data-testid="stMetric"] {{
        background-color: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: 0 2px 6px rgba(15, 41, 74, 0.05);
    }}
    div[data-testid="stMetricValue"] {{
        font-size: 19px;
        color: #0f294a;
    }}
    div[data-testid="stMetricLabel"] {{
        color: #475569;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="app-banner">
        <h2>{t["banner_title"]}</h2>
        <p>{t["banner_sub"]}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_dept_label = st.radio(
    t["nav_label"],
    t["depts"],
    index=st.session_state.active_dept_idx,
    horizontal=True,
)
dept_idx = t["depts"].index(selected_dept_label)
st.session_state.active_dept_idx = dept_idx

df_all = pd.read_sql_query("SELECT * FROM tickets", conn)

if st.session_state.current_ticket_id and not df_all.empty:
    match_cur = df_all[df_all["ticket_id"] == st.session_state.current_ticket_id]
    if not match_cur.empty:
        cur_row = match_cur.iloc[0]
        disp_stage = t["stage_map"].get(cur_row["stage"], cur_row["stage"])
        st.info(
            t["active_ticket_bar"].format(
                tid=cur_row["ticket_id"],
                cust=cur_row["customer_name"],
                stage=disp_stage,
            )
        )

st.markdown("---")

# ==========================================
# 0. الاستقبال / Reception
# ==========================================
if dept_idx == 0:
    st.subheader(t["rec_title"])
    st.caption(t["rec_caption"])

    active_new_id = st.session_state.draft_ticket_id
    st.success(t["new_tid_msg"].format(tid=active_new_id))

    customer_name = st.text_input(t["cust_name"], "ريما القحطاني")
    reception_staff = st.text_input(t["rec_staff"], "سالم الدوسري")

    c_ph, c_sn = st.columns(2)
    with c_ph:
        customer_phone = st.text_input(t["mobile"], "0501234567")
    with c_sn:
        device_sn = st.text_input(t["sn"], "SN-77412908").strip()

    c_ty, c_br = st.columns(2)
    with c_ty:
        device_type = st.selectbox(t["dev_type"], t["dev_types"])
    with c_br:
        brand = st.selectbox(t["brand"], t["brands"])

    c_pr, c_dt = st.columns(2)
    with c_pr:
        priority_level = st.selectbox(t["priority"], t["priorities"])
    with c_dt:
        ticket_date = st.date_input(t["rec_date"], datetime.now())

    initial_note = st.text_area(t["init_note"], placeholder=t["init_note_ph"])
    go_to_maint = st.checkbox(t["go_maint"], value=True)

    if st.button(t["save_rec_btn"], type="primary"):
        next_stage = "Maintenance" if go_to_maint else "Reception"
        notes_val = initial_note.strip() if initial_note.strip() else t["default_rec_note"]

        cursor.execute("""
            INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            active_new_id,
            customer_name.strip(),
            reception_staff.strip(),
            customer_phone.strip(),
            device_sn,
            device_type,
            brand,
            "Pending inspection",
            "Pending diagnostics",
            notes_val,
            priority_level,
            "Pending",
            next_stage,
            "Unpaid",
            str(ticket_date),
            "فهد المطيري",
            "0 SAR",
        ))
        conn.commit()

        st.session_state.current_ticket_id = active_new_id
        st.session_state.draft_ticket_id = generate_unique_ticket_id()

        if go_to_maint:
            st.session_state.active_dept_idx = 1
            st.rerun()
        else:
            st.success(t["saved_rec_msg"].format(tid=active_new_id))
            st.rerun()

    st.markdown("---")
    st.markdown(f"#### {t['reg_tickets']}")
    if df_all.empty:
        st.info(t["no_tickets"])
        if st.button(t["load_demo"]):
            load_demo_data()
            st.rerun()
    else:
        view_rec = df_all.copy()
        view_rec["stage_show"] = view_rec["stage"].map(lambda s: t["stage_map"].get(s, s))
        if st.session_state.lang == "ar":
            disp_df = view_rec.rename(columns={
                "ticket_id": "رقم التذكرة",
                "customer_name": "اسم العميل",
                "reception_staff": "موظف الاستقبال",
                "customer_phone": "رقم الجوال",
                "device_sn": "الرقم التسلسلي",
                "stage_show": "القسم الحالي",
                "priority": "الأولوية",
                "ticket_date": "التاريخ",
            })
            st.dataframe(
                disp_df[["رقم التذكرة", "اسم العميل", "موظف الاستقبال", "رقم الجوال", "الرقم التسلسلي", "القسم الحالي", "الأولوية", "التاريخ"]],
                use_container_width=True,
            )
        else:
            disp_df = view_rec.rename(columns={
                "ticket_id": "Ticket ID",
                "customer_name": "Customer",
                "reception_staff": "Receptionist",
                "customer_phone": "Mobile",
                "device_sn": "Serial",
                "stage_show": "Stage",
                "priority": "Priority",
                "ticket_date": "Date",
            })
            st.dataframe(
                disp_df[["Ticket ID", "Customer", "Receptionist", "Mobile", "Serial", "Stage", "Priority", "Date"]],
                use_container_width=True,
            )

# ==========================================
# 1. الصيانة / Maintenance
# ==========================================
elif dept_idx == 1:
    st.subheader(t["maint_title"])
    st.caption(t["maint_caption"])

    if df_all.empty:
        st.info(t["no_maint_tickets"])
        c_b1, c_b2 = st.columns(2)
        if c_b1.button(t["load_demo"]):
            load_demo_data()
            st.rerun()
        if c_b2.button(t["go_rec_btn"]):
            st.session_state.active_dept_idx = 0
            st.rerun()
    else:
        ticket_ids = df_all["ticket_id"].tolist()
        default_idx = 0
        if st.session_state.current_ticket_id in ticket_ids:
            default_idx = ticket_ids.index(st.session_state.current_ticket_id)

        def fmt_maint(tid):
            r = df_all[df_all["ticket_id"] == tid].iloc[0]
            st_lbl = t["stage_map"].get(r["stage"], r["stage"])
            return f"{r['ticket_id']} | {r['customer_name']} ({st_lbl})"

        chosen_id = st.selectbox(t["pick_ticket_maint"], ticket_ids, index=default_idx, format_func=fmt_maint)
        st.session_state.current_ticket_id = chosen_id
        row = df_all[df_all["ticket_id"] == chosen_id].iloc[0]
        cur_st_lbl = t["stage_map"].get(row["stage"], row["stage"])

        with st.container(border=True):
            st.write(t["fixed_tid"].format(tid=row["ticket_id"], stage=cur_st_lbl))
            st.write(
                t["cust_info_line"].format(
                    cust=row["customer_name"],
                    staff=row["reception_staff"],
                    phone=row["customer_phone"],
                )
            )
            st.write(t["dev_info_line"].format(dtype=row["device_type"], brand=row["brand"], sn=row["device_sn"]))
            st.info(t["prev_notes"].format(notes=row["tech_notes"]))

        st.markdown(t["specs_sec"])
        device_age = st.slider(t["age_lbl"], 0, 15, 3)
        c_r, c_s = st.columns(2)
        with c_r:
            ram = st.selectbox(t["ram_lbl"], ["4 GB", "8 GB", "16 GB", "32 GB", "64 GB"], index=1)
        with c_s:
            storage = st.selectbox(t["stor_lbl"], t["stor_opts"])

        st.markdown(t["issues_sec"])
        tab1, tab2, tab3 = st.tabs(t["tabs"])
        with tab1:
            c_slow = st.checkbox(t["c_slow"])
            c_heat = st.checkbox(t["c_heat"])
            c_bsod = st.checkbox(t["c_bsod"])
            c_noise = st.checkbox(t["c_noise"])
        with tab2:
            c_boot = st.checkbox(t["c_boot"])
            c_virus = st.checkbox(t["c_virus"])
            c_corrupt = st.checkbox(t["c_corrupt"])
        with tab3:
            c_net = st.checkbox(t["c_net"])
            c_domain = st.checkbox(t["c_domain"])

        tech_person = st.text_input(t["tech_lbl"], value=row["technician_name"] if row["technician_name"] else "فهد المطيري")
        tech_notes = st.text_area(t["tech_notes_lbl"], value=row["tech_notes"])
        send_to_billing = st.checkbox(t["send_bill"], value=True)

        if st.button(t["save_diag_btn"], type="primary"):
            selected_issues = []
            if c_slow:
                selected_issues.append("Slow/Freeze")
            if c_heat:
                selected_issues.append("Heat/Fan")
            if c_bsod:
                selected_issues.append("BSOD")
            if c_noise:
                selected_issues.append("HDD Clicking")
            if c_boot:
                selected_issues.append("Boot Failure")
            if c_virus:
                selected_issues.append("Malware")
            if c_corrupt:
                selected_issues.append("Driver/App")
            if c_net:
                selected_issues.append("Network/Wi-Fi")
            if c_domain:
                selected_issues.append("Domain/LAN")

            issues_text = ", ".join(selected_issues) if selected_issues else "No specific issues"
            specs_text = f"{ram} | {storage} | {device_age} yrs"

            decision = "Software & Preventive"
            cost_val = "90 SAR"

            if c_noise or (device_age >= 8 and c_boot):
                decision = "Device Replacement"
                cost_val = "3,200 SAR"
            elif "HDD" in storage and (c_slow or c_boot):
                decision = "SSD Upgrade"
                cost_val = "280 SAR"
            elif "4 GB" in ram and c_slow:
                decision = "RAM Upgrade"
                cost_val = "180 SAR"
            elif c_heat:
                decision = "Thermal & Mechanical Service"
                cost_val = "120 SAR"

            new_stage = "Billing" if send_to_billing else "Maintenance"

            cursor.execute("""
                UPDATE tickets
                SET specs_summary = ?, issues_summary = ?, tech_notes = ?,
                    decision = ?, stage = ?, technician_name = ?, cost_est = ?
                WHERE ticket_id = ?
            """, (
                specs_text,
                issues_text,
                tech_notes.strip(),
                decision,
                new_stage,
                tech_person.strip(),
                cost_val,
                chosen_id,
            ))
            conn.commit()
            st.session_state.current_ticket_id = chosen_id

            if send_to_billing:
                st.session_state.active_dept_idx = 2
                st.rerun()
            else:
                st.success(t["saved_diag_msg"].format(tid=chosen_id))
                st.rerun()

# ==========================================
# 2. الحساب / Billing
# ==========================================
elif dept_idx == 2:
    st.subheader(t["bill_title"])
    st.caption(t["bill_caption"])

    if df_all.empty:
        st.info(t["no_bill_tickets"])
        if st.button(t["load_demo"], type="primary"):
            load_demo_data()
            st.rerun()
    else:
        m1, m2 = st.columns(2)
        m1.metric(t["m_total"], len(df_all))
        m2.metric(t["m_in_bill"], len(df_all[df_all["stage"].isin(["Billing", "الحساب"])]))

        m3, m4 = st.columns(2)
        m3.metric(t["m_paid"], len(df_all[df_all["payment_status"].isin(["Paid", "مدفوع"])]))
        m4.metric(t["m_unpaid"], len(df_all[df_all["payment_status"].isin(["Unpaid", "غير مدفوع"])]))

        stage_filter_opts = [t["all_opt"], t["depts"][0], t["depts"][1], t["depts"][2]]
        stage_filter = st.selectbox(t["filter_stage"], stage_filter_opts)

        view_df = df_all.copy()
        view_df["stage_show"] = view_df["stage"].map(lambda s: t["stage_map"].get(s, s))
        if stage_filter != t["all_opt"]:
            view_df = view_df[view_df["stage_show"] == stage_filter]

        if st.session_state.lang == "ar":
            disp_bill = view_df.rename(columns={
                "ticket_id": "رقم التذكرة",
                "customer_name": "اسم العميل",
                "reception_staff": "موظف الاستقبال",
                "decision": "التشخيص",
                "cost_est": "المبلغ",
                "payment_status": "حالة الدفع",
                "stage_show": "القسم الحالي",
            })
            st.dataframe(
                disp_bill[["رقم التذكرة", "اسم العميل", "موظف الاستقبال", "التشخيص", "المبلغ", "حالة الدفع", "القسم الحالي"]],
                use_container_width=True,
            )
        else:
            disp_bill = view_df.rename(columns={
                "ticket_id": "Ticket ID",
                "customer_name": "Customer",
                "reception_staff": "Receptionist",
                "decision": "Decision",
                "cost_est": "Amount",
                "payment_status": "Payment",
                "stage_show": "Stage",
            })
            st.dataframe(
                disp_bill[["Ticket ID", "Customer", "Receptionist", "Decision", "Amount", "Payment", "Stage"]],
                use_container_width=True,
            )

        st.markdown(t["bill_mgmt"])
        bill_ids = df_all["ticket_id"].tolist()
        bill_default = 0
        if st.session_state.current_ticket_id in bill_ids:
            bill_default = bill_ids.index(st.session_state.current_ticket_id)

        def fmt_bill(tid):
            r = df_all[df_all["ticket_id"] == tid].iloc[0]
            st_lbl = t["stage_map"].get(r["stage"], r["stage"])
            return f"{r['ticket_id']} | {r['customer_name']} ({st_lbl})"

        bill_id = st.selectbox(t["pick_ticket_bill"], bill_ids, index=bill_default, format_func=fmt_bill)
        st.session_state.current_ticket_id = bill_id
        brow = df_all[df_all["ticket_id"] == bill_id].iloc[0]
        cur_bst = t["stage_map"].get(brow["stage"], brow["stage"])

        with st.container(border=True):
            st.write(t["fixed_tid"].format(tid=brow["ticket_id"], stage=cur_bst))
            st.write(
                t["cust_info_line"].format(
                    cust=brow["customer_name"],
                    staff=brow["reception_staff"],
                    phone=brow["customer_phone"],
                )
            )
            st.write(t["dev_info_line"].format(dtype=brow["device_type"], brand=brow["brand"], sn=brow["device_sn"]))
            st.write(f"**{brow['decision']}** | `{brow['cost_est']}` | `{brow['payment_status']}`")

        c_cost, c_pay = st.columns(2)
        with c_cost:
            new_cost = st.text_input(t["final_cost"], value=brow["cost_est"])
        with c_pay:
            pay_opts = t["pay_opts"]
            pay_idx = 1 if brow["payment_status"] in ["Paid", "مدفوع"] else 0
            new_pay = st.selectbox(t["pay_status"], pay_opts, index=pay_idx)

        stage_choices_lbl = [t["depts"][2], t["depts"][1], t["depts"][0]]
        stage_default_idx = 0
        if cur_bst in stage_choices_lbl:
            stage_default_idx = stage_choices_lbl.index(cur_bst)

        move_stage_lbl = st.selectbox(t["move_stage"], stage_choices_lbl, index=stage_default_idx)
        stage_to_db = {
            t["depts"][0]: "Reception",
            t["depts"][1]: "Maintenance",
            t["depts"][2]: "Billing",
        }[move_stage_lbl]

        if st.button(t["save_bill_btn"], type="primary"):
            cursor.execute("""
                UPDATE tickets
                SET cost_est = ?, payment_status = ?, stage = ?
                WHERE ticket_id = ?
            """, (new_cost.strip(), new_pay, stage_to_db, bill_id))
            conn.commit()
            st.session_state.current_ticket_id = bill_id
            if stage_to_db == "Reception":
                st.session_state.active_dept_idx = 0
            elif stage_to_db == "Maintenance":
                st.session_state.active_dept_idx = 1
            st.rerun()

        invoice_lines = [
            "=== Service Invoice & Report ===",
            f"Ticket ID: {brow['ticket_id']}",
            f"Date: {brow['ticket_date']}",
            f"Customer: {brow['customer_name']}",
            f"Receptionist: {brow['reception_staff']}",
            f"Mobile: {brow['customer_phone']}",
            f"Device: {brow['device_type']} - {brow['brand']} ({brow['device_sn']})",
            f"Decision: {brow['decision']}",
            f"Amount: {new_cost}",
            f"Payment: {new_pay}",
            f"Stage: {move_stage_lbl}",
            f"Notes: {brow['tech_notes']}",
        ]
        st.download_button(
            label=t["dl_invoice"],
            data="\n".join(invoice_lines),
            file_name=f"Invoice_{brow['ticket_id']}.txt",
            mime="text/plain",
        )

        csv_bytes = view_df.drop(columns=["stage_show"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label=t["dl_csv_bill"],
            data=csv_bytes,
            file_name="billing_tickets.csv",
            mime="text/csv",
        )

# ==========================================
# 3. المدير / Manager (PIN Protected)
# ==========================================
elif dept_idx == 3:
    st.subheader(t["mgr_title"])

    if not st.session_state.manager_unlocked:
        st.warning(t["mgr_warn"])
        entered_pin = st.text_input(t["pin_lbl"], type="password", placeholder=t["pin_ph"])
        if st.button(t["unlock_btn"], type="primary"):
            if entered_pin.strip() == MANAGER_PIN:
                st.session_state.manager_unlocked = True
                st.success(t["pin_ok"])
                st.rerun()
            else:
                st.error(t["pin_err"])
    else:
        if st.button(t["lock_btn"]):
            st.session_state.manager_unlocked = False
            st.rerun()

        st.markdown("---")
        st.caption(t["mgr_caption"])

        if df_all.empty:
            st.info(t["no_tickets"])
            if st.button(t["load_demo"], type="primary"):
                load_demo_data()
                st.rerun()
        else:
            m1, m2 = st.columns(2)
            m1.metric(t["m_total"], len(df_all))
            m2.metric(t["m_urgent"], len(df_all[df_all["priority"].isin(["Urgent", "عاجلة"])]))

            m3, m4 = st.columns(2)
            m3.metric(t["m_work"], len(df_all[df_all["stage"].isin(["Maintenance", "Billing", "الصيانة", "الحساب"])]))
            m4.metric(t["m_paid"], len(df_all[df_all["payment_status"].isin(["Paid", "مدفوع"])]))

            repeated_sn = df_all["device_sn"].value_counts()
            repeated_sn = repeated_sn[repeated_sn > 1]
            if not repeated_sn.empty:
                items_txt = ", ".join([f"{sn} ({cnt} {t['rep_times']})" for sn, cnt in repeated_sn.items()])
                st.warning(t["rep_sn"] + items_txt)

            mgr_view = df_all.copy()
            mgr_view["stage_show"] = mgr_view["stage"].map(lambda s: t["stage_map"].get(s, s))

            st.markdown(t["chart_stage"])
            st.bar_chart(mgr_view["stage_show"].value_counts())

            st.markdown(t["chart_dec"])
            st.bar_chart(mgr_view["decision"].value_counts())

            search_q = st.text_input(t["search_lbl"])
            f1, f2 = st.columns(2)
            mgr_stage = f1.selectbox(t["filt_dept"], [t["all_opt"]] + sorted(mgr_view["stage_show"].unique().tolist()))
            mgr_pay = f2.selectbox(t["filt_pay"], [t["all_opt"]] + sorted(mgr_view["payment_status"].unique().tolist()))

            mgr_df = mgr_view.copy()
            if search_q:
                mask = (
                    mgr_df["ticket_id"].str.contains(search_q, case=False, na=False)
                    | mgr_df["customer_name"].str.contains(search_q, case=False, na=False)
                    | mgr_df["reception_staff"].str.contains(search_q, case=False, na=False)
                    | mgr_df["customer_phone"].str.contains(search_q, case=False, na=False)
                    | mgr_df["device_sn"].str.contains(search_q, case=False, na=False)
                )
                mgr_df = mgr_df[mask]
            if mgr_stage != t["all_opt"]:
                mgr_df = mgr_df[mgr_df["stage_show"] == mgr_stage]
            if mgr_pay != t["all_opt"]:
                mgr_df = mgr_df[mgr_df["payment_status"] == mgr_pay]

            st.dataframe(mgr_df.drop(columns=["stage_show"], errors="ignore"), use_container_width=True)

            mgr_labels = [f"{r['ticket_id']} | {r['customer_name']}" for _, r in df_all.iterrows()]
            del_choice = st.selectbox(t["pick_del"], mgr_labels)
            del_id = del_choice.split(" | ")[0].strip()

            if st.button(t["del_btn"]):
                cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (del_id,))
                conn.commit()
                st.warning(t["del_msg"].format(tid=del_id))
                st.rerun()

            csv_mgr = mgr_df.drop(columns=["stage_show"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label=t["dl_csv_mgr"],
                data=csv_mgr,
                file_name="manager_tickets_report.csv",
                mime="text/csv",
            )

            if st.button(t["add_demo"]):
                load_demo_data()
                st.rerun()

            if st.button(t["clear_all"]):
                cursor.execute("DELETE FROM tickets")
                conn.commit()
                st.rerun()

# ==========================================
# 4. نبذة عن الموقع / About
# ==========================================
else:
    st.subheader(t["about_title"])
    st.write(t["about_desc"])

    with st.container(border=True):
        st.markdown(t["mgr_creds_title"])
        st.write(t["mgr_pin_line"].format(pin=MANAGER_PIN))
        st.caption(t["mgr_pin_hint"])

    st.markdown(t["feats_title"])
    for item in t["feats"]:
        st.markdown(item)
