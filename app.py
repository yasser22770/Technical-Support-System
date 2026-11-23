import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

# إعداد الصفحة
st.set_page_config(
    page_title="IT Helpdesk & Knowledge Base Lab",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تنسيق الواجهة العربية (RTL) مع الحفاظ على اتجاه الأكواد البرمجية (LTR)
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
    }
    pre, code {
        direction: ltr !important;
        text-align: left !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .sla-badge-ok {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .sla-badge-late {
        background-color: #f8d7da;
        color: #842029;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DB_PATH = "helpdesk_streamlit.db"
ADMIN_PIN = "1234"

SLA_HOURS = {
    "عاجل (Urgent - ساعتان)": 2,
    "مرتفع (High - 4 ساعات)": 4,
    "متوسط (Medium - 24 ساعة)": 24,
    "منخفض (Low - 72 ساعة)": 72,
}

CATEGORIES = [
    "Hardware - أعطال الأجهزة",
    "Software & OS - البرمجيات والأنظمة",
    "Networking - الشبكات والإنترنت",
    "Access & AD - الصلاحيات والحسابات",
]


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'جديدة',
            requester TEXT NOT NULL,
            mobile TEXT NOT NULL,
            assignee TEXT DEFAULT 'غير معيّن',
            attachment_name TEXT,
            attachment_content TEXT,
            created_at TEXT NOT NULL,
            sla_deadline TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS kb_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            steps TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ad_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            department TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'نشط',
            locked INTEGER NOT NULL DEFAULT 0,
            last_action TEXT NOT NULL
        )
    """)

    # بيانات أولية تلقائية للمعاينة
    if cur.execute("SELECT COUNT(*) FROM kb_articles").fetchone()[0] == 0:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        articles = [
            (
                "إصلاح بطء نظام Windows واستهلاك الذاكرة المرتفع",
                "Software & OS - البرمجيات والأنظمة",
                "تأخر استجابة التطبيقات وارتفاع استهلاك الذاكرة (RAM).",
                "1. افتح مدير المهام عبر الضغط على Ctrl + Shift + Esc.\n"
                "2. رتب العمليات حسب الذاكرة وأغلق البرامج غير المستخدمة.\n"
                "3. شغّل سكربت التشخيص المرفق مع خيار تنظيف الملفات المؤقتة (--clean).\n"
                "4. أعد تشغيل الجهاز للتحقق من استقرار الأداء.",
                now_str,
            ),
            (
                "استكشاف أعطال Wi-Fi وظهور علامة No Internet",
                "Networking - الشبكات والإنترنت",
                "اتصال الجهاز بالشبكة مع تعذر فتح المواقع أو الأنظمة الداخلية.",
                "1. فعّل وضع الطيران لمدة 10 ثوانٍ ثم أوقفه.\n"
                "2. افتح موجه الأوامر (CMD) ونفّذ: ipconfig /release ثم ipconfig /renew.\n"
                "3. نفّذ الأمر ipconfig /flushdns لتحديث ذاكرة DNS.\n"
                "4. في حال استمرار العطل، أرفق تقرير diagnostics.py داخل تذكرة جديدة.",
                now_str,
            ),
            (
                "فك قفل حساب الموظف في Active Directory وإعادة تعيين كلمة المرور",
                "Access & AD - الصلاحيات والحسابات",
                "ظهور رسالة Account Locked Out عند محاولة تسجيل الدخول.",
                "1. تحقق من هوية الموظف ورقم الجوال المسجل.\n"
                "2. افتح وحدة Active Directory Users and Computers أو تبويب محاكي AD.\n"
                "3. نفّذ إجراء فك القفل (Unlock Account) وأعد تعيين كلمة المرور.\n"
                "4. اطلب من الموظف تغيير كلمة المرور فور تسجيل الدخول.",
                now_str,
            ),
            (
                "حل مشكلة توقف الطابعة الشبكية وتعليق المستندات",
                "Hardware - أعطال الأجهزة",
                "بقاء المستندات في قائمة الانتظار بحالة Printing أو Error.",
                "1. افتح نافذة الخدمات (services.msc) وأوقف خدمة Print Spooler.\n"
                "2. امسح الملفات العالقة داخل المسار C:\\Windows\\System32\\spool\\PRINTERS.\n"
                "3. أعد تشغيل خدمة Print Spooler وأرسل صفحة اختبار.",
                now_str,
            ),
        ]
        cur.executemany(
            "INSERT INTO kb_articles (title, category, symptoms, steps, created_at) VALUES (?, ?, ?, ?, ?)",
            articles,
        )

    if cur.execute("SELECT COUNT(*) FROM ad_users").fetchone()[0] == 0:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        users = [
            ("sara.ali", "سارة علي", "الموارد البشرية", "نشط", 1, f"تم قفل الحساب بسبب محاولات خاطئة ({now_str})"),
            ("ahmed.hassan", "أحمد حسن", "المالية", "نشط", 0, f"إنشاء الحساب وتعيين المجلد المشترك ({now_str})"),
            ("it.agent", "خالد المنصور", "تقنية المعلومات", "نشط", 0, f"صلاحيات الدعم الفني ({now_str})"),
            ("omar.samir", "عمر سمير", "المبيعات", "معطّل", 0, f"إيقاف مؤقت لحين استلام العهدة ({now_str})"),
        ]
        cur.executemany(
            "INSERT INTO ad_users (username, full_name, department, status, locked, last_action) VALUES (?, ?, ?, ?, ?, ?)",
            users,
        )

    if cur.execute("SELECT COUNT(*) FROM tickets").fetchone()[0] == 0:
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M")
        sample_tickets = [
            (
                "قفل حساب الموظفة سارة علي وعدم القدرة على الدخول للنظام",
                "تظهر رسالة Account Locked Out على جهاز WIN10-HR02 منذ الصباح.",
                "Access & AD - الصلاحيات والحسابات",
                "مرتفع (High - 4 ساعات)",
                "قيد المعالجة",
                "سارة علي",
                "0501234567",
                "خالد المنصور",
                None,
                None,
                now_str,
                (now_dt + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"),
            ),
            (
                "انقطاع الاتصال بالشبكة الداخلية في قسم المالية",
                "الجهاز يحصل على IP يبدأ بـ 169.254 ولا يصل إلى خادم DHCP.",
                "Networking - الشبكات والإنترنت",
                "عاجل (Urgent - ساعتان)",
                "جديدة",
                "أحمد حسن",
                "0559876543",
                "غير معيّن",
                None,
                None,
                now_str,
                (now_dt + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            ),
        ]
        cur.executemany(
            """INSERT INTO tickets
               (title, description, category, priority, status, requester, mobile, assignee, attachment_name, attachment_content, created_at, sla_deadline)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            sample_tickets,
        )

    conn.commit()
    conn.close()


init_db()

# ================= الشريط الجانبي (تبديل الدور للمعاينة) =================
with st.sidebar:
    st.title("🛠️ IT Helpdesk Lab")
    st.caption("نظام إدارة التذاكر وقاعدة المعرفة ومحاكي AD")
    st.divider()

    role_mode = st.radio(
        "وضع الاستخدام:",
        ["بوابة الموظف (إرسال تذكرة وبحث)", "لوحة فني الدعم والإدارة (IT Support)"],
    )

    is_admin = False
    if role_mode == "لوحة فني الدعم والإدارة (IT Support)":
        pin_input = st.text_input("رمز دخول فني الدعم (PIN)", type="password", placeholder="أدخل الرمز")
        if pin_input == ADMIN_PIN:
            is_admin = True
            st.success("تم تفعيل صلاحيات فني الدعم")
        else:
            st.info(f"للمعاينة والتقييم، استخدم رمز الدخول: `{ADMIN_PIN}`")

    st.divider()
    st.markdown("**أداة التشخيص السريع للعميل**")
    if os.path.exists("diagnostics.py"):
        with open("diagnostics.py", "r", encoding="utf-8") as f:
            diag_code = f.read()
        st.download_button(
            label="📥 تحميل سكربت diagnostics.py",
            data=diag_code,
            file_name="diagnostics.py",
            mime="text/x-python",
            use_container_width=True,
        )

# ================= تحميل الإحصائيات =================
conn = get_conn()
tickets_df = pd.read_sql_query("SELECT * FROM tickets ORDER BY id DESC", conn)
kb_df = pd.read_sql_query("SELECT * FROM kb_articles ORDER BY id DESC", conn)
ad_df = pd.read_sql_query("SELECT * FROM ad_users ORDER BY id ASC", conn)
conn.close()

# مؤشرات الأداء العلوية
c1, c2, c3, c4 = st.columns(4)
c1.metric("إجمالي التذاكر", len(tickets_df))
c2.metric("التذاكر المفتوحة", int((tickets_df["status"] != "مغلقة").sum()))
c3.metric("تذاكر عاجلة مفتوحة", int(((tickets_df["priority"].str.contains("عاجل")) & (tickets_df["status"] != "مغلقة")).sum()))
c4.metric("أدلة المعرفة / حسابات مقفلة", f"{len(kb_df)} دليل / {int((ad_df['locked'] == 1).sum())} مقفل")

st.divider()

# ================= التبويبات الرئيسية =================
tab_tickets, tab_new, tab_kb, tab_ad = st.tabs(
    [
        "📋 التذاكر والمتابعة",
        "➕ فتح تذكرة جديدة",
        "📚 قاعدة المعرفة (SOPs)",
        "🖥️ محاكي Active Directory",
    ]
)

# ---------------------------------------------------------
# 1. تبويب التذاكر والمتابعة
# ---------------------------------------------------------
with tab_tickets:
    f1, f2 = st.columns(2)
    with f1:
        filter_cat = st.selectbox("تصفية حسب التصنيف", ["الكل"] + CATEGORIES)
    with f2:
        filter_status = st.selectbox("تصفية حسب الحالة", ["الكل", "جديدة", "قيد المعالجة", "مغلقة"])

    filtered_tickets = tickets_df.copy()
    if filter_cat != "الكل":
        filtered_tickets = filtered_tickets[filtered_tickets["category"] == filter_cat]
    if filter_status != "الكل":
        filtered_tickets = filtered_tickets[filtered_tickets["status"] == filter_status]

    if filtered_tickets.empty:
        st.info("لا توجد تذاكر مطابقة لخيارات التصفية الحالية.")
    else:
        display_cols = filtered_tickets[["id", "title", "category", "priority", "status", "requester", "mobile", "assignee", "sla_deadline"]].copy()
        display_cols.columns = ["رقم", "العنوان", "التصنيف", "الأولوية", "الحالة", "مقدم الطلب", "الجوال", "الفني المسؤول", "موعد SLA"]
        st.dataframe(display_cols, use_container_width=True, hide_index=True)

        st.subheader("🔍 تفاصيل التذكرة والإجراءات")
        selected_id = st.selectbox(
            "اختر رقم التذكرة لعرض تفاصيلها أو تحديثها:",
            filtered_tickets["id"].tolist(),
            format_func=lambda x: f"#{x} - {filtered_tickets[filtered_tickets['id'] == x]['title'].values[0]}",
        )

        ticket_row = filtered_tickets[filtered_tickets["id"] == selected_id].iloc[0]
        deadline_dt = datetime.strptime(ticket_row["sla_deadline"], "%Y-%m-%d %H:%M")
        is_overdue = (ticket_row["status"] != "مغلقة") and (datetime.now() > deadline_dt)

        col_info, col_manage = st.columns([2, 1])
        with col_info:
            st.markdown(f"### #{ticket_row['id']} — {ticket_row['title']}")
            st.caption(
                f"**مقدم الطلب:** {ticket_row['requester']} | **الجوال:** {ticket_row['mobile']} | "
                f"**التصنيف:** {ticket_row['category']} | **تاريخ الفتح:** {ticket_row['created_at']}"
            )
            if is_overdue:
                st.markdown(f"<span class='sla-badge-late'>⚠️ متجاوزة لوقت SLA ({ticket_row['sla_deadline']})</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span class='sla-badge-ok'>⏱️ موعد SLA المستهدف: {ticket_row['sla_deadline']}</span>", unsafe_allow_html=True)

            st.write("")
            st.info(ticket_row["description"])

            if ticket_row["attachment_name"]:
                with st.expander(f"📎 المرفق: {ticket_row['attachment_name']}"):
                    st.code(ticket_row["attachment_content"] or "ملف مرفق", language="text")

            # سجل الملاحظات والردود
            conn = get_conn()
            notes = conn.execute("SELECT * FROM ticket_notes WHERE ticket_id = ? ORDER BY id ASC", (int(selected_id),)).fetchall()
            conn.close()

            st.markdown("**سجل المتابعة والحلول:**")
            if not notes:
                st.caption("لا توجد ملاحظات مسجلة بعد.")
            for n in notes:
                st.markdown(f"- **{n['author']}** *({n['created_at']})*: {n['note']}")

            with st.form(f"note_form_{selected_id}"):
                note_author = st.text_input("الاسم", value="خالد المنصور (فني دعم)" if is_admin else ticket_row["requester"])
                note_text = st.text_area("إضافة تحديث أو خطوة حل", height=80)
                if st.form_submit_button("إرسال التحديث"):
                    if note_text.strip():
                        conn = get_conn()
                        conn.execute(
                            "INSERT INTO ticket_notes (ticket_id, author, note, created_at) VALUES (?, ?, ?, ?)",
                            (int(selected_id), note_author.strip(), note_text.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")),
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

        with col_manage:
            if is_admin:
                st.markdown("#### ⚙️ تحديث حالة التذكرة")
                with st.form(f"update_ticket_{selected_id}"):
                    new_status = st.selectbox(
                        "الحالة",
                        ["جديدة", "قيد المعالجة", "مغلقة"],
                        index=["جديدة", "قيد المعالجة", "مغلقة"].index(ticket_row["status"]),
                    )
                    new_assignee = st.text_input("الفني المسؤول", value=ticket_row["assignee"])
                    if st.form_submit_button("حفظ التعديلات", use_container_width=True):
                        conn = get_conn()
                        conn.execute(
                            "UPDATE tickets SET status = ?, assignee = ? WHERE id = ?",
                            (new_status, new_assignee.strip() or "غير معيّن", int(selected_id)),
                        )
                        conn.commit()
                        conn.close()
                        st.success("تم تحديث التذكرة")
                        st.rerun()

                st.divider()
                st.markdown("#### 📚 تحويل الحل إلى دليل SOP")
                with st.form(f"promote_kb_{selected_id}"):
                    sop_title = st.text_input("عنوان المقال", value=f"دليل حل: {ticket_row['title']}")
                    sop_steps = st.text_area("خطوات الإصلاح المبسطة", placeholder="1. الخطوة الأولى...\n2. الخطوة الثانية...")
                    if st.form_submit_button("نشر في قاعدة المعرفة", use_container_width=True):
                        if sop_steps.strip():
                            conn = get_conn()
                            conn.execute(
                                "INSERT INTO kb_articles (title, category, symptoms, steps, created_at) VALUES (?, ?, ?, ?, ?)",
                                (
                                    sop_title.strip(),
                                    ticket_row["category"],
                                    ticket_row["description"],
                                    sop_steps.strip(),
                                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success("تم نشر المقال في قاعدة المعرفة!")
                            st.rerun()
            else:
                st.warning("قم بتفعيل **لوحة فني الدعم والإدارة** من القائمة الجانبية لتغيير حالة التذكرة أو نشر الحلول في قاعدة المعرفة.")

# ---------------------------------------------------------
# 2. تبويب فتح تذكرة جديدة (نموذج مبسط ومتجاوب)
# ---------------------------------------------------------
with tab_new:
    st.subheader("تسجيل بلاغ أو طلب دعم فني")
    with st.form("create_ticket_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            req_name = st.text_input("اسم الموظف *", placeholder="مثال: سارة علي")
            req_mobile = st.text_input("رقم الجوال للتواصل *", placeholder="مثال: 05XXXXXXXX")
        with col_b:
            t_category = st.selectbox("تصنيف المشكلة *", CATEGORIES)
            t_priority = st.selectbox("الأولوية (SLA) *", list(SLA_HOURS.keys()))

        t_title = st.text_input("عنوان المشكلة *", placeholder="وصف مختصر وواضح للعطل")
        t_desc = st.text_area("تفاصيل المشكلة ورسائل الخطأ *", height=120)
        uploaded_report = st.file_uploader(
            "إرفاق تقرير التشخيص (Helpdesk_Report_*.txt) أو سجل نصي (اختياري)",
            type=["txt", "log"],
        )

        submitted = st.form_submit_button("إرسال التذكرة", type="primary")
        if submitted:
            if not (req_name.strip() and req_mobile.strip() and t_title.strip() and t_desc.strip()):
                st.error("يرجى تعبئة جميع الحقول الأساسية المطلوبة (*).")
            else:
                att_name = None
                att_text = None
                if uploaded_report is not None:
                    att_name = uploaded_report.name
                    att_text = uploaded_report.read().decode("utf-8", errors="replace")

                now_dt = datetime.now()
                created_str = now_dt.strftime("%Y-%m-%d %H:%M")
                deadline_str = (now_dt + timedelta(hours=SLA_HOURS[t_priority])).strftime("%Y-%m-%d %H:%M")

                conn = get_conn()
                conn.execute(
                    """INSERT INTO tickets
                       (title, description, category, priority, status, requester, mobile, attachment_name, attachment_content, created_at, sla_deadline)
                       VALUES (?, ?, ?, ?, 'جديدة', ?, ?, ?, ?, ?, ?)""",
                    (
                        t_title.strip(),
                        t_desc.strip(),
                        t_category,
                        t_priority,
                        req_name.strip(),
                        req_mobile.strip(),
                        att_name,
                        att_text,
                        created_str,
                        deadline_str,
                    ),
                )
                conn.commit()
                conn.close()
                st.success(f"تم تسجيل التذكرة بنجاح! الموعد المستهدف للحل (SLA): {deadline_str}")
                st.rerun()

# ---------------------------------------------------------
# 3. تبويب قاعدة المعرفة (Knowledge Base & SOPs)
# ---------------------------------------------------------
with tab_kb:
    st.subheader("📚 أدلة الإصلاح الذاتي للموظفين وفنيي الدعم (SOPs)")
    s1, s2 = st.columns([2, 1])
    with s1:
        kb_search = st.text_input("ابحث في قاعدة المعرفة", placeholder="اكتب كلمة مفتاحية مثل: Wi-Fi، طابعة، بطء، قفل...")
    with s2:
        kb_cat_filter = st.selectbox("التصنيف", ["الكل"] + CATEGORIES, key="kb_cat")

    filtered_kb = kb_df.copy()
    if kb_cat_filter != "الكل":
        filtered_kb = filtered_kb[filtered_kb["category"] == kb_cat_filter]
    if kb_search.strip():
        q = kb_search.strip().lower()
        filtered_kb = filtered_kb[
            filtered_kb["title"].str.lower().str.contains(q)
            | filtered_kb["symptoms"].str.lower().str.contains(q)
            | filtered_kb["steps"].str.lower().str.contains(q)
        ]

    for _, art in filtered_kb.iterrows():
        with st.expander(f"📘 {art['title']}  —  [{art['category'].split(' - ')[0]}]"):
            st.markdown(f"**الأعراض:** {art['symptoms']}")
            st.markdown("**خطوات الحل:**")
            st.code(art["steps"], language="text")
            st.caption(f"تاريخ التحديث: {art['created_at']}")

    if is_admin:
        st.divider()
        st.markdown("#### ➕ إضافة دليل إصلاح جديد")
        with st.form("add_kb_form", clear_on_submit=True):
            k_title = st.text_input("عنوان الدليل")
            k_cat = st.selectbox("التصنيف", CATEGORIES, key="new_kb_cat")
            k_symp = st.text_input("الأعراض التي تظهر للمستخدم")
            k_steps = st.text_area("خطوات الإصلاح المرقمة", height=120)
            if st.form_submit_button("حفظ الدليل"):
                if k_title.strip() and k_symp.strip() and k_steps.strip():
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO kb_articles (title, category, symptoms, steps, created_at) VALUES (?, ?, ?, ?, ?)",
                        (k_title.strip(), k_cat, k_symp.strip(), k_steps.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")),
                    )
                    conn.commit()
                    conn.close()
                    st.success("تمت إضافة الدليل بنجاح.")
                    st.rerun()

# ---------------------------------------------------------
# 4. تبويب محاكي Active Directory
# ---------------------------------------------------------
with tab_ad:
    st.subheader("🖥️ محاكي إدارة حسابات المستخدمين (Active Directory Lab)")
    st.caption("محاكاة لمهام المستوى الأول (L1 Support): إنشاء الحسابات، فك القفل، وإعادة تعيين كلمات المرور على النطاق corp.local")

    ad_display = ad_df.copy()
    ad_display["username"] = ad_display["username"] + "@corp.local"
    ad_display["locked"] = ad_display["locked"].apply(lambda x: "🔴 مقفل (Locked)" if x == 1 else "🟢 سليم")
    ad_display.columns = ["ID", "اسم الدخول", "الاسم الكامل", "القسم", "الحالة", "حالة القفل", "آخر إجراء إداري"]
    st.dataframe(ad_display.drop(columns=["ID"]), use_container_width=True, hide_index=True)

    if is_admin:
        col_ad1, col_ad2 = st.columns(2)
        with col_ad1:
            st.markdown("#### 🔧 تنفيذ إجراء على حساب موجود")
            selected_user = st.selectbox(
                "اختر المستخدم:",
                ad_df["username"].tolist(),
                format_func=lambda u: f"{u}@corp.local ({ad_df[ad_df['username'] == u]['full_name'].values[0]})",
            )
            b1, b2, b3 = st.columns(3)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

            if b1.button("🔓 فك القفل", use_container_width=True):
                conn = get_conn()
                conn.execute(
                    "UPDATE ad_users SET locked = 0, last_action = ? WHERE username = ?",
                    (f"تم فك قفل الحساب ({now_str})", selected_user),
                )
                conn.commit()
                conn.close()
                st.rerun()

            if b2.button("🔑 إعادة تعيين كلمة المرور", use_container_width=True):
                conn = get_conn()
                conn.execute(
                    "UPDATE ad_users SET locked = 0, last_action = ? WHERE username = ?",
                    (f"إعادة تعيين كلمة المرور وإلزام التغيير ({now_str})", selected_user),
                )
                conn.commit()
                conn.close()
                st.rerun()

            if b3.button("⏯️ تفعيل / تعطيل", use_container_width=True):
                curr_st = ad_df[ad_df["username"] == selected_user]["status"].values[0]
                nxt_st = "معطّل" if curr_st == "نشط" else "نشط"
                conn = get_conn()
                conn.execute(
                    "UPDATE ad_users SET status = ?, last_action = ? WHERE username = ?",
                    (nxt_st, f"تغيير حالة الحساب إلى {nxt_st} ({now_str})", selected_user),
                )
                conn.commit()
                conn.close()
                st.rerun()

        with col_ad2:
            st.markdown("#### ➕ إنشاء حساب موظف جديد")
            with st.form("new_ad_user_form", clear_on_submit=True):
                new_u = st.text_input("اسم الدخول (Username)", placeholder="مثال: nora.salem")
                new_fn = st.text_input("الاسم الكامل", placeholder="مثال: نورة سالم")
                new_dep = st.text_input("القسم", placeholder="مثال: التسويق")
                if st.form_submit_button("إنشاء الحساب في النطاق", use_container_width=True):
                    if new_u.strip() and new_fn.strip() and new_dep.strip():
                        try:
                            conn = get_conn()
                            conn.execute(
                                "INSERT INTO ad_users (username, full_name, department, status, locked, last_action) VALUES (?, ?, ?, 'نشط', 0, ?)",
                                (
                                    new_u.strip().lower(),
                                    new_fn.strip(),
                                    new_dep.strip(),
                                    f"تم إنشاء الحساب وتعيين الصلاحيات ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
                                ),
                            )
                            conn.commit()
                            conn.close()
                            st.success(f"تم إنشاء الحساب {new_u.strip().lower()}@corp.local")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم مسجل مسبقاً.")
    else:
        st.info("فعّل **لوحة فني الدعم والإدارة** من القائمة الجانبية لتنفيذ إجراءات Active Directory.")
