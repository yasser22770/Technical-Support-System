import streamlit as st
from datetime import datetime
import random
import sqlite3
import pandas as pd

# 1. إعداد قاعدة البيانات المحلية (SQLite)
conn = sqlite3.connect('enterprise_helpdesk_theme_v1.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id TEXT PRIMARY KEY,
        customer_name TEXT,
        device_sn TEXT,
        device_type TEXT,
        brand TEXT,
        specs_summary TEXT,
        issues_summary TEXT,
        tech_notes TEXT,
        priority TEXT,
        decision TEXT,
        status TEXT,
        ticket_date TEXT,
        technician_name TEXT,
        cost_est TEXT
    )
''')
conn.commit()

# دالة لإضافة بيانات تجريبية جاهزة للاستعراض
def load_demo_data():
    sample_tickets = [
        (
            "TK-10421", "أحمد العتيبي - قسم المحاسبة", "SN-DL-88210",
            "حاسب محمول (Laptop)", "Dell", "4 GB | HDD تقليدي | عمر 4 سنة",
            "بطء/تجمد", "القرص التقليدي يسبب بطئاً شديداً، يُنصح بالترقية إلى SSD فقط.",
            "متوسطة", "ترقية عتاد (SSD)", "قيد المعالجة", "2026-11-18",
            "ياسر الحازمي", "180 - 380 ر.س"
        ),
        (
            "TK-10422", "نورة السبيعي - الموارد البشرية", "SN-HP-55109",
            "حاسب مكتبي (Desktop)", "HP", "8 GB | SATA SSD | عمر 2 سنة",
            "شبكة/Wi-Fi، تعريف/برنامج", "تم تحديث تعريف كرت الشبكة وإعادة ضبط الاتصال.",
            "عادية", "صيانة برمجية ووقائية", "مكتملة", "2026-11-19",
            "ياسر الحازمي", "0 - 100 ر.س"
        ),
        (
            "TK-10423", "خالد الحربي - المستودعات", "SN-LN-33019",
            "حاسب محمول (Laptop)", "Lenovo", "8 GB | HDD تقليدي | عمر 8 سنة",
            "طقطقة قرص صلب، تعذر الإقلاع", "تلف ميكانيكي في القرص مع قدم العتاد؛ الاستبدال أوفر اقتصادياً.",
            "عاجلة", "استبدال الجهاز", "مفتوحة", "2026-11-20",
            "ياسر الحازمي", "2,500 - 4,800 ر.س"
        ),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        sample_tickets
    )
    conn.commit()

# 2. إعدادات الصفحة المتجاوبة مع الجوال (Mobile-Friendly RTL)
st.set_page_config(
    page_title="نظام الدعم الفني وتشخيص الأعطال",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 3. تنسيق الألوان والواجهة (هوية نيلية/فيروزية عصرية)
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
    /* الأزرار الأساسية بلون نيلي/فيروزي واضح */
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

# ترويسة التطبيق الملونة
st.markdown(
    """
    <div class="app-banner">
        <h2>🛠️ نظام الدعم الفني وتشخيص الأعطال</h2>
        <p>منصة ذكية وعادلة لتسجيل الأعطال وإصدار توصيات الصيانة والترقية أو الاستبدال</p>
    </div>
    """,
    unsafe_allow_html=True
)

user_role = st.radio(
    "اختر الواجهة:",
    ["فني صيانة", "مدير النظام", "نبذة عن المشروع"],
    horizontal=True
)
st.markdown("---")

# ==========================================
# الواجهة الأولى: فني الصيانة
# ==========================================
if user_role == "فني صيانة":
    st.subheader("🔧 تسجيل وفحص جهاز")
    ticket_id = f"TK-{random.randint(10000, 99999)}"
    st.info(f"**رقم التذكرة الحالية:** `{ticket_id}`")

    with st.expander("🎫 بيانات العميل والفني (اضغط للتعديل)", expanded=True):
        customer_name = st.text_input("اسم العميل / القسم", "سارة خالد - الموارد البشرية")
        device_sn = st.text_input("الرقم التسلسلي للجهاز (S/N)", "SN-99281044").strip()
        tech_person = st.text_input("اسم الفني المسؤول", "ياسر الحازمي")
        c_p, c_d = st.columns(2)
        with c_p:
            priority_level = st.selectbox("الأولوية", ["عادية", "متوسطة", "عاجلة"])
        with c_d:
            ticket_date = st.date_input("تاريخ الفحص", datetime.now())

    if device_sn:
        cursor.execute("SELECT COUNT(*), MAX(ticket_date) FROM tickets WHERE device_sn = ?", (device_sn,))
        prev_count, last_date = cursor.fetchone()
        if prev_count and prev_count > 0:
            st.warning(f"⚠️ تنبيه: الجهاز (`{device_sn}`) مسجل مسبقاً ({prev_count} مرة، آخر فحص: {last_date}).")

    st.markdown("#### 1️⃣ مواصفات الجهاز")
    c_t, c_b = st.columns(2)
    with c_t:
        device_type = st.selectbox("نوع الجهاز", ["حاسب محمول (Laptop)", "حاسب مكتبي (Desktop)", "محطة عمل (Workstation)"])
    with c_b:
        brand = st.selectbox("الشركة المصنعة", ["Dell", "HP", "Lenovo", "Apple", "Asus", "أخرى"])

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

    st.markdown("#### 3️⃣ ملاحظات الفني")
    tech_notes = st.text_area(
        "ملاحظات إضافية:",
        placeholder="مثال: الجهاز يعمل بشكل جيد بعد إغلاق البرامج الخلفية، ويُكتفى بترقية SSD..."
    )

    if st.button("🚀 تنفيذ التشخيص وحفظ التذكرة", type="primary"):
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
        notes_clean = tech_notes.strip() if tech_notes.strip() else "لا توجد ملاحظات إضافية"

        # منطق تشخيص واقعي وعادل بدون نسب تلف مبالغ فيها
        decision = "صيانة برمجية ووقائية"
        cost_estimate = "0 - 100 ر.س"
        time_estimate = "1 - 2 ساعة"

        if c_noise or (device_age >= 8 and c_boot):
            decision = "استبدال الجهاز"
            cost_estimate = "2,500 - 4,800 ر.س"
            time_estimate = "1 - 3 أيام"
        elif storage == "HDD تقليدي" and (c_slow or c_boot):
            decision = "ترقية عتاد (SSD)"
            cost_estimate = "180 - 380 ر.س"
            time_estimate = "2 - 3 ساعات"
        elif "4 GB" in ram and c_slow:
            decision = "ترقية عتاد (RAM)"
            cost_estimate = "120 - 250 ر.س"
            time_estimate = "1 - 2 ساعة"
        elif c_heat:
            decision = "صيانة ميكانيكية وتنظيف حراري"
            cost_estimate = "50 - 150 ر.س"
            time_estimate = "1 - 2 ساعة"

        cursor.execute('''
            INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticket_id, customer_name, device_sn, device_type, brand,
            specs_text, issues_text, notes_clean, priority_level, decision,
            "مفتوحة", str(ticket_date), tech_person, cost_estimate
        ))
        conn.commit()

        st.markdown("---")
        st.subheader(f"📋 نتيجة الفحص ({ticket_id})")
        r1, r2 = st.columns(2)
        r1.metric("القرار المقترح", decision)
        r2.metric("التكلفة التقديرية", cost_estimate)

        r3, r4 = st.columns(2)
        r3.metric("الوقت المتوقع", time_estimate)
        r4.metric("الأولوية", priority_level)

        if decision == "استبدال الجهاز":
            st.error("🚨 **التوصية:** يُفضل استبدال الجهاز نظراً لوجود عطل ميكانيكي حرج أو انتهاء عمره التشغيلي.")
        elif "ترقية" in decision:
            st.warning("⚠️ **التوصية:** ترقية القطع المحددة ستحسّن أداء الجهاز بتكلفة مناسبة.")
        else:
            st.success("✅ **التوصية:** الجهاز لا يحتاج لاستبدال؛ صيانة برمجية أو تنظيف وقائي كافٍ.")

        st.markdown("#### ✅ خطوات التنفيذ للفني:")
        recs = []
        if storage == "HDD تقليدي" and (c_slow or c_boot):
            recs.append("نسخ البيانات احتياطياً، تركيب قرص SSD، وتثبيت النظام.")
        if "4 GB" in ram and c_slow:
            recs.append("فحص التوافق ورفع الذاكرة العشوائية إلى 8GB أو 16GB.")
        if c_heat:
            recs.append("تنظيف المراوح ومسارات التهوية وتجديد المعجون الحراري.")
        if c_bsod or c_boot:
            recs.append("تشغيل SFC / DISM وفحص الذاكرة والقرص الصلب.")
        if c_virus:
            recs.append("فحص شامل لمكافحة الفيروسات وإزالة البرامج المشبوهة.")
        if c_corrupt:
            recs.append("إعادة تثبيت التعريف أو البرنامج المتضرر من المصدر الرسمي.")
        if c_net or c_domain:
            recs.append("إعادة ضبط إعدادات الشبكة وفحص إعدادات النطاق.")

        if not recs:
            recs.append("إجراء فحص وقائي دوري وتحديثات النظام الأساسية.")

        for step in recs:
            st.checkbox(step, value=False, key=f"chk_{ticket_id}_{step[:12]}")

        st.info(f"**ملاحظات الفني:** {notes_clean}")

        report_content = (
            f"رقم التذكرة: {ticket_id}\n"
            f"التاريخ: {ticket_date}\n"
            f"الأولوية: {priority_level}\n"
            f"العميل: {customer_name}\n"
            f"الفني: {tech_person}\n"
            f"الجهاز: {device_type} - {brand} ({device_sn})\n"
            f"المواصفات: {specs_text}\n"
            f"الأعطال: {issues_text}\n"
            f"القرار: {decision}\n"
            f"التكلفة التقديرية: {cost_estimate}\n"
            f"الوقت المتوقع: {time_estimate}\n"
            f"ملاحظات الفني: {notes_clean}\n\n"
            f"خطوات التنفيذ:\n" + "\n".join([f"- {x}" for x in recs])
        )

        st.download_button(
            label="📥 تحميل التقرير (.txt)",
            data=report_content,
            file_name=f"Ticket_{ticket_id}.txt",
            mime="text/plain"
        )
        st.success("✅ تم حفظ التذكرة بنجاح.")

# ==========================================
# الواجهة الثانية: مدير النظام
# ==========================================
elif user_role == "مدير النظام":
    st.subheader("📊 لوحة تحكم مدير النظام")

    df = pd.read_sql_query("SELECT * FROM tickets", conn)

    if df.empty:
        st.info("📭 لا توجد تذاكر مسجلة حالياً.")
        if st.button("✨ تعبئة بيانات تجريبية جاهزة للاستعراض", type="primary"):
            load_demo_data()
            st.rerun()
    else:
        m1, m2 = st.columns(2)
        m1.metric("إجمالي التذاكر", len(df))
        m2.metric("تذاكر مفتوحة", len(df[df["status"] == "مفتوحة"]))

        m3, m4 = st.columns(2)
        m3.metric("تذاكر مكتملة", len(df[df["status"] == "مكتملة"]))
        m4.metric("تذاكر عاجلة", len(df[df["priority"] == "عاجلة"]))

        repeated_sn = df["device_sn"].value_counts()
        repeated_sn = repeated_sn[repeated_sn > 1]
        if not repeated_sn.empty:
            st.warning("🔁 **أجهزة ذات تذاكر متكررة:** " + "، ".join([f"{sn} ({cnt} مرات)" for sn, cnt in repeated_sn.items()]))

        st.markdown("---")
        search_term = st.text_input("🔎 بحث برقم التذكرة أو العميل أو S/N")
        f1, f2 = st.columns(2)
        decision_filter = f1.selectbox("تصفية حسب القرار", ["الكل"] + sorted(df["decision"].unique().tolist()))
        status_filter = f2.selectbox("تصفية حسب الحالة", ["الكل"] + sorted(df["status"].unique().tolist()))

        filtered_df = df.copy()
        if search_term:
            mask = (
                filtered_df["ticket_id"].str.contains(search_term, case=False, na=False) |
                filtered_df["customer_name"].str.contains(search_term, case=False, na=False) |
                filtered_df["device_sn"].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]

        if decision_filter != "الكل":
            filtered_df = filtered_df[filtered_df["decision"] == decision_filter]

        if status_filter != "الكل":
            filtered_df = filtered_df[filtered_df["status"] == status_filter]

        st.markdown("#### 📋 سجل التذاكر")
        st.dataframe(filtered_df, use_container_width=True)

        st.markdown("#### 🔍 معاينة وتحديث تذكرة")
        selected_ticket = st.selectbox("اختر رقم التذكرة", df["ticket_id"].tolist())
        row = df[df["ticket_id"] == selected_ticket].iloc[0]

        with st.container(border=True):
            st.write(f"**العميل:** {row['customer_name']}")
            st.write(f"**الجهاز:** {row['device_type']} — {row['brand']} (`{row['device_sn']}`)")
            st.write(f"**المواصفات:** {row['specs_summary']}")
            st.write(f"**الأعطال:** {row['issues_summary']}")
            st.write(f"**القرار:** {row['decision']} | **التكلفة:** {row['cost_est']}")
            st.write(f"**الحالة:** {row['status']} | **الأولوية:** {row['priority']}")
            st.info(f"**ملاحظات الفني:** {row['tech_notes']}")

        u1, u2 = st.columns(2)
        new_status = u1.selectbox("الحالة الجديدة", ["مفتوحة", "قيد المعالجة", "مكتملة"])
        new_priority = u2.selectbox("الأولوية الجديدة", ["عادية", "متوسطة", "عاجلة"], index=["عادية", "متوسطة", "عاجلة"].index(row["priority"]))
        updated_notes = st.text_area("تحديث الملاحظات", value=row["tech_notes"])

        if st.button("💾 حفظ التعديلات", type="primary"):
            cursor.execute(
                "UPDATE tickets SET status = ?, priority = ?, tech_notes = ? WHERE ticket_id = ?",
                (new_status, new_priority, updated_notes.strip(), selected_ticket)
            )
            conn.commit()
            st.success(f"تم تحديث التذكرة {selected_ticket}.")
            st.rerun()

        if st.button("🗑️ حذف التذكرة المحددة"):
            cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (selected_ticket,))
            conn.commit()
            st.warning(f"تم حذف التذكرة {selected_ticket}.")
            st.rerun()

        st.markdown("---")
        csv_data = filtered_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📊 تصدير السجل بصيغة CSV",
            data=csv_data,
            file_name="helpdesk_tickets.csv",
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
# الواجهة الثالثة: نبذة عن المشروع
# ==========================================
else:
    st.subheader("📌 نبذة عن المشروع")
    st.write(
        "تطبيق ويب متجاوب مع الجوال والحاسب لتسجيل مواصفات الأجهزة وتشخيص أعطال العتاد والنظام والشبكات، "
        "وإصدار توصيات صيانة واقعية دون تضخيم الأعطال البسيطة."
    )
    st.markdown("- **واجهة مزدوجة:** لوحة لفني الصيانة ولوحة متابعة وإحصاءات لمدير النظام.")
    st.markdown("- **قاعدة بيانات SQLite:** لحفظ التذاكر وتحديث حالاتها ورصد تكرار الأعطال.")
    st.markdown("- **تقارير وتصدير:** تحميل تقرير فني لكل تذكرة `.txt` وتصدير السجل الكامل `.csv`.")
