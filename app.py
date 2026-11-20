import streamlit as st
from datetime import datetime
import random
import sqlite3
import pandas as pd

# رمز الدخول الخاص بقسم المدير
MANAGER_PIN = "MGR-2026"

# 1. إعداد قاعدة البيانات المحلية (SQLite)
conn = sqlite3.connect('enterprise_helpdesk_single_ticket_v1.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        customer_name TEXT,
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


def load_demo_data():
    sample_tickets = [
        (
            "TK-40101", "ريما القحطاني - قسم الحسابات", "0501122334", "SN-DL-77412",
            "حاسب محمول (Laptop)", "Dell", "4 GB | HDD تقليدي | عمر 4 سنة",
            "بطء/تجمد", "القرص التقليدي يسبب بطئاً ملحوظاً، يُنصح بالترقية إلى SSD فقط.",
            "متوسطة", "ترقية عتاد (SSD)", "قسم الحساب", "غير مدفوع", "2026-11-18",
            "فهد المطيري", "280 ر.س"
        ),
        (
            "TK-40102", "عمر الزهراني - شؤون الموظفين", "0559988776", "SN-HP-61904",
            "حاسب مكتبي (Desktop)", "HP", "8 GB | SATA SSD | عمر 2 سنة",
            "شبكة/Wi-Fi، تعريف/برنامج", "تم تحديث تعريف كرت الشبكة وإعادة ضبط الاتصال.",
            "عادية", "صيانة برمجية ووقائية", "قسم الصيانة", "غير مدفوع", "2026-11-19",
            "فهد المطيري", "80 ر.س"
        ),
        (
            "TK-40103", "لينا الشهري - العمليات اللوجستية", "0544433221", "SN-LN-48290",
            "حاسب محمول (Laptop)", "Lenovo", "8 GB | HDD تقليدي | عمر 8 سنة",
            "طقطقة قرص صلب، تعذر الإقلاع", "تلف ميكانيكي في القرص مع تقادم العتاد؛ الاستبدال أنسب عملياً.",
            "عاجلة", "استبدال الجهاز", "قسم الاستقبال", "غير مدفوع", "2026-11-20",
            "فهد المطيري", "3,200 ر.س"
        ),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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

# شريط يوضح التذكرة النشطة الحالية ورقمها الثابت أثناء الانتقال
if st.session_state.current_ticket_id:
    match_cur = df_all[df_all["ticket_id"] == st.session_state.current_ticket_id]
    if not match_cur.empty:
        cur_row = match_cur.iloc[0]
        st.info(
            f"**التذكرة النشطة:** `{cur_row['ticket_id']}` | "
            f"**العميل:** {cur_row['customer_name']} | "
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

    customer_name = st.text_input("اسم العميل / القسم", "ريما القحطاني - قسم الحسابات")
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
            INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            active_new_id, customer_name, customer_phone, device_sn, device_type,
            brand, "بانتظار فحص المواصفات", "بانتظار تحديد الأعطال", notes_val,
            priority_level, "بانتظار التشخيص", next_stage, "غير مدفوع",
            str(ticket_date), "فهد المطيري", "0 ر.س"
        ))
        conn.commit()

        # تثبيت رقم التذكرة الحالية وتجهيز رقم جديد لعميل لاحق فقط
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
        st.dataframe(
            df_all[["ticket_id", "customer_name", "device_sn", "stage", "priority", "ticket_date"]],
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
            return f"{r['ticket_id']} | {r['customer_name']} ({r['stage']})"

        chosen_id = st.selectbox("اختر التذكرة للفحص:", ticket_ids, index=default_idx, format_func=fmt_maint)
        st.session_state.current_ticket_id = chosen_id
        row = df_all[df_all["ticket_id"] == chosen_id].iloc[0]

        with st.container(border=True):
            st.write(f"**رقم التذكرة الثابت:** `{row['ticket_id']}` | **المرحلة الحالية:** `{row['stage']}`")
            st.write(f"**العميل:** {row['customer_name']} | **الجوال:** {row['customer_phone']}")
            st.write(f"**الجهاز:** {row['device_type']} — {row['brand']} (`{row['device_sn']}`)")
            st.info(f"**ملاحظات سابقة:** {row['tech_notes']}")

        st.markdown("#### 1️⃣ مواصفات الجهاز أثناء الفحص")
        device_age = st.slider("عمر الجهاز (بالسنوات)", 0, 15, 3)
        c_r, c_s = st.columns(2)
        with c_r:
            ram = st.selectbox("الذاكرة (RAM)", ["4 GB", "8 GB", "16 GB", "32 GB", "64 GB"], index=1)
        with c_s:
            storage = st.selectbox("التخزين", ["HDD تقليدي", "SATA SSD", "NVMe M.2 SSD"])

        st.markdown("#### 2️⃣ تحديد الأعطال")
        tab1, tab2, tab3 = st.tabs(["⚙️ العتاد", "💻 النظام", "🌐 الشبكة"])
        with tab1:
            c_slow = st.checkbox("بطء ملحوظ أو تجمد متكرر")
            c_heat = st.checkbox("ارتفاع حرارة أو صوت مروحة مرتفع")
            c_bsod = st.checkbox("شاشة زرقاء (BSOD) أو إعادة تشغيل")
            c_noise = st.checkbox("أصوات طقطقة ميكانيكية من القرص الصلب")
        with tab2:
            c_boot = st.checkbox("تعذر الإقلاع أو تلف ملفات النظام")
            c_virus = st.checkbox("اشتباه برمجيات خبيثة أو إعلانات")
            c_corrupt = st.checkbox("مشكلة في تعريف أو برنامج معين")
        with tab3:
            c_net = st.checkbox("انقطاع Wi-Fi أو ضعف الاتصال")
            c_domain = st.checkbox("مشكلة دخول الشبكة المحلية / النطاق")

        tech_person = st.text_input("اسم فني الصيانة", value=row["technician_name"] if row["technician_name"] else "فهد المطيري")
        tech_notes = st.text_area("تقرير وملاحظات فني الصيانة:", value=row["tech_notes"])
        send_to_billing = st.checkbox("نقل التذكرة بنفس الرقم إلى قسم الحساب بعد الحفظ", value=True)

        if st.button("🛠️ حفظ التشخيص ونقل التذكرة", type="primary"):
            selected_issues = []
            if c_slow: selected_issues.append("بطء/تجمد")
            if c_heat: selected_issues.append("حرارة/مروحة")
            if c_bsod: selected_issues.append("شاشة زرقاء")
            if c_noise: selected_issues.append("طقطقة قرص صلب")
            if c_boot: selected_issues.append("تعذر الإقلاع")
            if c_virus: selected_issues.append("برمجيات خبيثة")
            if c_corrupt: selected_issues.append("تعريف/برنامج")
            if c_net: selected_issues.append("شبكة/Wi-Fi")
            if c_domain: selected_issues.append("النطاق المحلي")

            issues_text = "، ".join(selected_issues) if selected_issues else "لا توجد أعطال محددة"
            specs_text = f"{ram} | {storage} | عمر {device_age} سنة"

            # منطق تشخيص واقعي وعادل بدون نسب تلف مبالغ فيها
            decision = "صيانة برمجية ووقائية"
            cost_val = "90 ر.س"

            if c_noise or (device_age >= 8 and c_boot):
                decision = "استبدال الجهاز"
                cost_val = "3,200 ر.س"
            elif storage == "HDD تقليدي" and (c_slow or c_boot):
                decision = "ترقية عتاد (SSD)"
                cost_val = "280 ر.س"
            elif "4 GB" in ram and c_slow:
                decision = "ترقية عتاد (RAM)"
                cost_val = "180 ر.س"
            elif c_heat:
                decision = "صيانة ميكانيكية وتنظيف حراري"
                cost_val = "120 ر.س"

            new_stage = "قسم الحساب" if send_to_billing else "قسم الصيانة"

            cursor.execute('''
                UPDATE tickets
                SET specs_summary = ?, issues_summary = ?, tech_notes = ?,
                    decision = ?, stage = ?, technician_name = ?, cost_est = ?
                WHERE ticket_id = ?
            ''', (
                specs_text, issues_text, tech_notes.strip(),
                decision, new_stage, tech_person.strip(), cost_val, chosen_id
            ))
            conn.commit()
            st.session_state.current_ticket_id = chosen_id

            if send_to_billing:
                st.session_state.active_dept = "قسم الحساب"
                st.rerun()
            else:
                st.success(f"✅ تم حفظ التشخيص للتذكرة `{chosen_id}`.")
                st.rerun()

# ==========================================
# 3. قسم الحساب
# ==========================================
elif selected_dept == "قسم الحساب":
    st.subheader("💳 قسم الحساب — الفواتير واعتماد الدفع")
    st.caption("استكمال معالجة التذكرة بنفس رقمها واعتماد المبلغ وحالة الدفع.")

    if df_all.empty:
        st.info("📭 لا توجد تذاكر مسجلة في الحساب حالياً.")
        if st.button("✨ تعبئة بيانات تجريبية للاختبار", type="primary"):
            load_demo_data()
            st.rerun()
    else:
        m1, m2 = st.columns(2)
        m1.metric("إجمالي التذاكر", len(df_all))
        m2.metric("في قسم الحساب", len(df_all[df_all["stage"] == "قسم الحساب"]))

        m3, m4 = st.columns(2)
        m3.metric("مدفوع", len(df_all[df_all["payment_status"] == "مدفوع"]))
        m4.metric("غير مدفوع", len(df_all[df_all["payment_status"] == "غير مدفوع"]))

        stage_filter = st.selectbox("تصفية حسب القسم / المرحلة:", ["الكل", "قسم الاستقبال", "قسم الصيانة", "قسم الحساب"])
        view_df = df_all if stage_filter == "الكل" else df_all[df_all["stage"] == stage_filter]

        st.dataframe(
            view_df[["ticket_id", "customer_name", "decision", "cost_est", "payment_status", "stage"]],
            use_container_width=True
        )

        st.markdown("#### 🧾 إدارة فاتورة التذكرة")
        bill_ids = df_all["ticket_id"].tolist()
        bill_default = 0
        if st.session_state.current_ticket_id in bill_ids:
            bill_default = bill_ids.index(st.session_state.current_ticket_id)

        def fmt_bill(tid):
            r = df_all[df_all["ticket_id"] == tid].iloc[0]
            return f"{r['ticket_id']} | {r['customer_name']} ({r['stage']})"

        bill_id = st.selectbox("اختر التذكرة:", bill_ids, index=bill_default, format_func=fmt_bill)
        st.session_state.current_ticket_id = bill_id
        brow = df_all[df_all["ticket_id"] == bill_id].iloc[0]

        with st.container(border=True):
            st.write(f"**رقم التذكرة الثابت:** `{brow['ticket_id']}` | **القسم الحالي:** `{brow['stage']}`")
            st.write(f"**العميل:** {brow['customer_name']} | **الجوال:** {brow['customer_phone']}")
            st.write(f"**الجهاز:** {brow['device_type']} — {brow['brand']} (`{brow['device_sn']}`)")
            st.write(f"**التشخيص / القرار:** {brow['decision']}")
            st.write(f"**المبلغ المعتمد:** `{brow['cost_est']}` | **حالة الدفع:** `{brow['payment_status']}`")

        c_cost, c_pay = st.columns(2)
        with c_cost:
            new_cost = st.text_input("المبلغ النهائي (ر.س)", value=brow["cost_est"])
        with c_pay:
            pay_opts = ["غير مدفوع", "مدفوع"]
            new_pay = st.selectbox("حالة الدفع", pay_opts, index=pay_opts.index(brow["payment_status"]) if brow["payment_status"] in pay_opts else 0)

        move_stage = st.selectbox(
            "إبقاء أو نقل التذكرة بنفس رقمها إلى:",
            ["قسم الحساب", "قسم الصيانة", "قسم الاستقبال"],
            index=["قسم الحساب", "قسم الصيانة", "قسم الاستقبال"].index(brow["stage"]) if brow["stage"] in ["قسم الحساب", "قسم الصيانة", "قسم الاستقبال"] else 0
        )

        if st.button("💾 حفظ الفاتورة وتحديث التذكرة", type="primary"):
            cursor.execute('''
                UPDATE tickets
                SET cost_est = ?, payment_status = ?, stage = ?
                WHERE ticket_id = ?
            ''', (new_cost.strip(), new_pay, move_stage, bill_id))
            conn.commit()
            st.session_state.current_ticket_id = bill_id
            if move_stage != "قسم الحساب":
                st.session_state.active_dept = move_stage
            st.rerun()

        invoice_txt = (
            f"=== فاتورة وتقرير خدمة الصيانة ===\n"
            f"رقم التذكرة: {brow['ticket_id']}\n"
            f"التاريخ: {brow['ticket_date']}\n"
            f"العميل: {brow['customer_name']} ({brow['customer_phone']})\n"
            f"الجهاز: {brow['device_type']} - {brow['brand']} ({brow['device_sn']})\n"
            f"التشخيص: {brow['decision']}\n"
            f"المبلغ: {new_cost}\n"
            f"حالة الدفع: {new_pay}\n"
            f"القسم: {move_stage}\n"
            f"ملاحظات: {brow['tech_notes']}\n"
        )

        st.download_button(
            label="📥 تحميل الفاتورة / التقرير (.txt)",
            data=invoice_txt,
            file_name=f"Invoice_{brow['ticket_id']}.txt",
            mime="text/plain"
        )

        csv_bytes = view_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📊 تصدير سجل الحسابات (.csv)",
            data=csv_bytes,
            file_name="billing_tickets.csv",
            mime="text/csv"
        )

# ==========================================
# 4. قسم المدير (محمي برقم دخول خاص)
# ==========================================
elif selected_dept == "قسم المدير":
    st.subheader("🔐 قسم المدير — دخول محمي برقم خاص")

    if not st.session_state.manager_unlocked:
        st.warning("هذا القسم مخصص للمدير ولا يُفتح إلا برقم الدخول الخاص. (يمكن لمسؤول التوظيف الاطلاع على الرقم في تبويب «نبذة عن الموقع»).")
        entered_pin = st.text_input("أدخل رقم الدخول الخاص بالمدير:", type="password", placeholder="مثال: MGR-2026")
        if st.button("🔓 دخول إلى لوحة المدير", type="primary"):
            if entered_pin.strip() == MANAGER_PIN:
                st.session_state.manager_unlocked = True
                st.success("✅ تم التحقق من رقم الدخول بنجاح.")
                st.rerun()
            else:
                st.error("❌ رقم الدخول غير صحيح. راجع «نبذة عن الموقع» لمعرفة رقم الدخول المخصص للتجربة.")
    else:
        if st.button("🔒 قفل / خروج من قسم المدير"):
            st.session_state.manager_unlocked = False
            st.rerun()

        st.markdown("---")
        st.caption("عرض الإحصاءات، رصد تكرار الأجهزة، البحث والتصفية، وحذف أو مسح السجلات.")

        if df_all.empty:
            st.info("📭 لا توجد تذاكر مسجلة حالياً.")
            if st.button("✨ تعبئة بيانات تجريبية جاهزة للاستعراض", type="primary"):
                load_demo_data()
                st.rerun()
        else:
            m1, m2 = st.columns(2)
            m1.metric("إجمالي التذاكر", len(df_all))
            m2.metric("تذاكر عاجلة", len(df_all[df_all["priority"] == "عاجلة"]))

            m3, m4 = st.columns(2)
            m3.metric("في الصيانة / الحساب", len(df_all[df_all["stage"].isin(["قسم الصيانة", "قسم الحساب"])]))
            m4.metric("مدفوع", len(df_all[df_all["payment_status"] == "مدفوع"]))

            repeated_sn = df_all["device_sn"].value_counts()
            repeated_sn = repeated_sn[repeated_sn > 1]
            if not repeated_sn.empty:
                st.warning("🔁 **أجهزة ذات تذاكر متكررة:** " + "، ".join([f"{sn} ({cnt} مرات)" for sn, cnt in repeated_sn.items()]))

            st.markdown("#### 📈 توزيع التذاكر حسب القسم")
            st.bar_chart(df_all["stage"].value_counts())

            st.markdown("#### 📈 توزيع التذاكر حسب القرار")
            st.bar_chart(df_all["decision"].value_counts())

            search_q = st.text_input("🔎 بحث برقم التذكرة أو اسم العميل أو الرقم التسلسلي")
            f1, f2 = st.columns(2)
            mgr_stage = f1.selectbox("تصفية بالقسم", ["الكل"] + sorted(df_all["stage"].unique().tolist()))
            mgr_pay = f2.selectbox("تصفية بالدفع", ["الكل"] + sorted(df_all["payment_status"].unique().tolist()))

            mgr_df = df_all.copy()
            if search_q:
                mask = (
                    mgr_df["ticket_id"].str.contains(search_q, case=False, na=False) |
                    mgr_df["customer_name"].str.contains(search_q, case=False, na=False) |
                    mgr_df["device_sn"].str.contains(search_q, case=False, na=False)
                )
                mgr_df = mgr_df[mask]
            if mgr_stage != "الكل":
                mgr_df = mgr_df[mgr_df["stage"] == mgr_stage]
            if mgr_pay != "الكل":
                mgr_df = mgr_df[mgr_df["payment_status"] == mgr_pay]

            st.dataframe(mgr_df, use_container_width=True)

            mgr_labels = [f"{r['ticket_id']} | {r['customer_name']}" for _, r in df_all.iterrows()]
            del_choice = st.selectbox("اختر تذكرة للإدارة / الحذف:", mgr_labels)
            del_id = del_choice.split(" | ")[0].strip()

            if st.button("🗑️ حذف التذكرة المحددة"):
                cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (del_id,))
                conn.commit()
                st.warning(f"تم حذف التذكرة `{del_id}`.")
                st.rerun()

            csv_mgr = mgr_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📊 تصدير السجل الكامل (.csv)",
                data=csv_mgr,
                file_name="manager_tickets_report.csv",
                mime="text/csv"
            )

            if st.button("✨ إضافة بيانات تجريبية"):
                load_demo_data()
                st.rerun()

            if st.button("🗑️ مسح جميع التذاكر"):
                cursor.execute("DELETE FROM tickets")
                conn.commit()
                st.rerun()

# ==========================================
# 5. نبذة عن الموقع (شاملة رقم دخول المدير للتجربة)
# ==========================================
else:
    st.subheader("📌 نبذة عن الموقع")
    st.write(
        "نظام ويب متكامل لإدارة أعمال الدعم الفني وصيانة الحاسب الآلي برقم تذكرة واحد ثابت عبر المراحل: "
        "**الاستقبال $\leftarrow$ الصيانة $\leftarrow$ الحساب**، مع إشراف إداري في **قسم المدير** "
        "ومنطق تشخيص واقعي وعادل يحدد التوصية المناسبة (صيانة، ترقية، أو استبدال) دون تضخيم الأعطال البسيطة."
    )

    with st.container(border=True):
        st.markdown("#### 🔑 بيانات دخول قسم المدير (لمسؤولي التوظيف والمستعرضين)")
        st.write(f"**رقم الدخول الخاص بالمدير:** `{MANAGER_PIN}`")
        st.caption("انتقل إلى تبويب «قسم المدير» وأدخل الرقم أعلاه لتجربة لوحة الإدارة والإحصاءات.")

    st.markdown("#### ✨ أبرز مزايا النظام:")
    st.markdown("- **رقم تذكرة موحد:** تنتقل التذكرة بنفس الرقم بين الاستقبال والصيانة والحساب.")
    st.markdown("- **تشخيص تقني عادل:** يعتمد على نوع العطل الفعلي وعمر الجهاز ومواصفاته.")
    st.markdown("- **إدارة وتقارير:** حفظ في قاعدة بيانات SQLite، رصد تكرار الأعطال، وتصدير `.txt` و`.csv`.")
