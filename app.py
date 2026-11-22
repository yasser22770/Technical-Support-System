import random
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

MANAGER_PIN = "MGR-2026"

conn = sqlite3.connect("enterprise_helpdesk_repair_notify_v1.db", check_same_thread=False)
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
        approval_status TEXT,
        repair_status TEXT,
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


def normalize_stage(val):
    if val in ["Reception", "الاستقبال"]:
        return "Reception"
    if val in ["Maintenance", "الصيانة"]:
        return "Maintenance"
    if val in ["Billing", "الحساب"]:
        return "Billing"
    return "Reception"


def normalize_payment(val):
    if val in ["Paid", "مدفوع"]:
        return "Paid"
    return "Unpaid"


def normalize_approval(val):
    if val in ["Approved", "معتمد"]:
        return "Approved"
    if val in ["Rejected", "مرفوض"]:
        return "Rejected"
    return "Pending"


def normalize_repair(val):
    if val in ["In Progress", "بدأت الصيانة", "جارية"]:
        return "In Progress"
    if val in ["Completed", "تم الانتهاء", "منتهية"]:
        return "Completed"
    return "Pending"


def is_mobile_or_tablet(dtype_str):
    keywords = ["جوال", "آيباد", "لوحي", "Smartphone", "iPad", "Tablet"]
    return any(k in (dtype_str or "") for k in keywords)


DEVICE_BRANDS = {
    "ar": {
        "جوال (Smartphone)": [
            "Apple", "Samsung", "Huawei", "Xiaomi", "Honor",
            "Oppo", "Realme", "Google Pixel", "OnePlus", "Vivo", "Nokia", "أخرى"
        ],
        "آيباد / جهاز لوحي (iPad / Tablet)": [
            "Apple (iPad)", "Samsung (Galaxy Tab)", "Huawei (MatePad)",
            "Lenovo", "Xiaomi", "Microsoft (Surface)", "أخرى"
        ],
        "لابتوب (Laptop)": [
            "Apple (MacBook)", "Dell", "HP", "Lenovo", "Asus",
            "Acer", "MSI", "Microsoft (Surface)", "Huawei", "Toshiba", "أخرى"
        ],
        "كمبيوتر مكتبي (Desktop PC)": [
            "Dell", "HP", "Lenovo", "Apple (iMac / Mac Mini)",
            "Asus", "Acer", "MSI", "Gigabyte", "تجميع خاص (Custom PC)", "أخرى"
        ],
    },
    "en": {
        "Smartphone": [
            "Apple", "Samsung", "Huawei", "Xiaomi", "Honor",
            "Oppo", "Realme", "Google Pixel", "OnePlus", "Vivo", "Nokia", "Other"
        ],
        "iPad / Tablet": [
            "Apple (iPad)", "Samsung (Galaxy Tab)", "Huawei (MatePad)",
            "Lenovo", "Xiaomi", "Microsoft (Surface)", "Other"
        ],
        "Laptop": [
            "Apple (MacBook)", "Dell", "HP", "Lenovo", "Asus",
            "Acer", "MSI", "Microsoft (Surface)", "Huawei", "Toshiba", "Other"
        ],
        "Desktop PC": [
            "Dell", "HP", "Lenovo", "Apple (iMac / Mac Mini)",
            "Asus", "Acer", "MSI", "Gigabyte", "Custom PC", "Other"
        ],
    },
}


def load_demo_data():
    sample_tickets = [
        (
            "TK-40101", "ريما القحطاني", "سالم الدوسري", "0501122334", "SN-IP-77412",
            "جوال (Smartphone)", "Apple", "256 GB | iOS / iPadOS | 2 yrs",
            "Battery", "Battery health at 71%; genuine battery replacement needed.",
            "Medium", "Battery Replacement", "Approved", "Completed", "Billing", "Unpaid", "2026-11-18",
            "فهد المطيري", "250 SAR"
        ),
        (
            "TK-40102", "عمر الزهراني", "سالم الدوسري", "0559988776", "SN-HP-61904",
            "لابتوب (Laptop)", "HP", "8 GB | SATA SSD | 2 yrs",
            "Network/Wi-Fi, Driver/App", "Approved by customer; repair in progress.",
            "Normal", "Software & Preventive", "Approved", "In Progress", "Maintenance", "Unpaid", "2026-11-19",
            "فهد المطيري", "90 SAR"
        ),
        (
            "TK-40103", "لينا الشهري", "سالم الدوسري", "0544433221", "SN-LN-48290",
            "كمبيوتر مكتبي (Desktop PC)", "Lenovo", "8 GB | HDD تقليدي | 8 yrs",
            "HDD Clicking, Boot Failure", "Mechanical drive failure on an 8-year-old desktop; replacement advised.",
            "Urgent", "Device Replacement", "Pending", "Pending", "Maintenance", "Unpaid", "2026-11-20",
            "فهد المطيري", "3,200 SAR"
        ),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        sample_tickets
    )
    conn.commit()


TEXTS = {
    "ar": {
        "page_title": "نظام إدارة مركز الصيانة والدعم الفني",
        "dir": "rtl",
        "align": "right",
        "banner_title": "🏢 نظام إدارة مركز الصيانة والدعم الفني",
        "banner_sub": "الاستقبال ← الفحص ← اعتماد العميل ← بدء الصيانة ← إشعار الانتهاء ← الحساب",
        "nav_label": "انتقل بين الأقسام:",
        "depts": ["الاستقبال", "الصيانة", "متابعة العميل", "الحساب", "المدير", "نبذة عن الموقع"],
        "stage_lbl": {
            "Reception": "الاستقبال",
            "Maintenance": "الصيانة",
            "Billing": "الحساب",
        },
        "pay_lbl": {
            "Unpaid": "غير مدفوع",
            "Paid": "مدفوع",
        },
        "appr_lbl": {
            "Pending": "بانتظار رد العميل",
            "Approved": "معتمد من العميل",
            "Rejected": "مرفوض — استلام الجهاز",
        },
        "repair_lbl": {
            "Pending": "لم تبدأ بعد",
            "In Progress": "بدأت الصيانة",
            "Completed": "تم الانتهاء من الصيانة",
        },
        "active_ticket_bar": "**التذكرة النشطة:** `{tid}` | **العميل:** {cust} | **القسم:** `{stage}` | **الصيانة:** `{rep}`",
        "rec_title": "🛎️ قسم الاستقبال — تسجيل بيانات العميل وفتح التذكرة",
        "rec_caption": "تبدأ التذكرة برقم واحد ثابت وتنتقل للصيانة ثم اعتماد العميل ثم بدء وإتمام الصيانة ثم الحساب.",
        "new_tid_msg": "**رقم التذكرة المخصص:** `{tid}`",
        "cust_name": "اسم العميل",
        "rec_staff": "اسم موظف الاستقبال",
        "mobile": "رقم الجوال",
        "sn": "الرقم التسلسلي / IMEI",
        "dev_type": "نوع الجهاز",
        "brand": "الشركة المصنعة",
        "priority": "الأولوية",
        "priorities": ["عادية", "متوسطة", "عاجلة"],
        "rec_date": "تاريخ الاستقبال",
        "init_note": "وصف المشكلة من العميل عند الاستقبال:",
        "init_note_ph": "مثال: الشاشة مكسورة، البطارية تفرغ بسرعة، أو الجهاز بطيء...",
        "go_maint": "نقل التذكرة بنفس الرقم إلى قسم الصيانة بعد الحفظ",
        "save_rec_btn": "📥 حفظ التذكرة وتحويلها",
        "default_rec_note": "تم تسجيل الجهاز في الاستقبال بانتظار الفحص الفني الجاد.",
        "saved_rec_msg": "✅ تم حفظ التذكرة برقم `{tid}`.",
        "reg_tickets": "📋 التذاكر المسجلة",
        "no_tickets": "لا توجد تذاكر مسجلة بعد.",
        "load_demo": "✨ تعبئة بيانات تجريبية للاختبار",
        "maint_title": "🔧 قسم الصيانة — الفحص وتنفيذ الإصلاح وإشعار الانتهاء",
        "maint_caption": "تظهر هنا التذاكر المخصصة للصيانة فقط. أرسل العطل والتكلفة للعميل، وبعد اعتماده تبدأ الصيانة ثم أرسل إشعار الانتهاء.",
        "no_maint_tickets": "📭 لا توجد تذاكر مخصصة لقسم الصيانة حالياً.",
        "go_rec_btn": "🛎️ الذهاب لقسم الاستقبال",
        "pick_ticket_maint": "اختر التذكرة المخصصة للصيانة:",
        "fixed_tid": "**رقم التذكرة:** `{tid}` | **الاعتماد:** `{appr}` | **حالة الصيانة:** `{rep}`",
        "cust_info_line": "**العميل:** {cust} | **موظف الاستقبال:** {staff} | **رقم الجوال:** {phone}",
        "dev_info_line": "**الجهاز:** {dtype} — {brand} (`{sn}`)",
        "prev_notes": "**ملاحظات سابقة:** {notes}",
        "specs_sec": "#### 1️⃣ مواصفات الجهاز أثناء الفحص",
        "age_lbl": "عمر الجهاز (بالسنوات)",
        "ram_lbl": "الذاكرة (RAM)",
        "stor_lbl": "التخزين",
        "stor_opts_pc": ["HDD تقليدي", "SATA SSD", "NVMe M.2 SSD"],
        "cap_lbl_mob": "السعة التخزينية",
        "cap_opts_mob": ["64 GB", "128 GB", "256 GB", "512 GB", "1 TB"],
        "os_lbl_mob": "نظام التشغيل",
        "os_opts_mob": ["iOS / iPadOS", "Android", "HarmonyOS", "Windows"],
        "issues_sec": "#### 2️⃣ تحديد الأعطال الفعلية بدقة",
        "tabs": ["⚙️ العتاد والقطع", "💻 النظام والبرمجيات", "🌐 الشبكة والاتصال"],
        "c_slow": "بطء ملحوظ أو تجمد متكرر",
        "c_heat": "ارتفاع حرارة أو صوت مروحة مرتفع",
        "c_bsod": "شاشة زرقاء (BSOD) أو إعادة تشغيل",
        "c_noise": "أصوات طقطقة ميكانيكية من القرص الصلب",
        "m_screen": "كسر في الشاشة أو ضعف اللمس",
        "m_batt": "ضعف البطارية أو سرعة نفاد الشحن",
        "m_port": "عطل في منفذ الشحن أو السماعة",
        "m_cam": "مشكلة في الكاميرا أو الأزرار",
        "c_boot": "تعذر الإقلاع / تعليق على الشعار",
        "c_virus": "اشتباه برمجيات خبيثة أو إعلانات",
        "c_corrupt": "مشكلة في تحديث النظام أو تطبيق",
        "c_net": "انقطاع Wi-Fi أو ضعف الشبكة",
        "c_domain": "مشكلة شريحة الاتصال / البلوتوث / الشبكة",
        "cost_sec": "#### 3️⃣ التكلفة وتقرير الفحص الفني",
        "est_cost_lbl": "التكلفة التقديرية للإصلاح (ر.س)",
        "tech_lbl": "اسم فني الصيانة",
        "tech_notes_lbl": "تقرير العطل وسبب التكلفة للعميل:",
        "save_diag_btn": "📤 حفظ الفحص وإرسال العطل والتكلفة للعميل",
        "sent_to_cust_msg": "✅ تم حفظ الفحص وإرسال رسالة العطل والتكلفة للتذكرة `{tid}` إلى العميل.",
        "exec_sec": "#### 4️⃣ تنفيذ الصيانة وإشعار العميل عند الانتهاء",
        "await_appr_warn": "⏳ بانتظار اعتماد العميل للعطل والتكلفة قبل بدء العمل الفعلي.",
        "repair_started_info": "🛠️ العميل اعتمد التكلفة — الصيانة جارية الآن على الجهاز.",
        "finish_note_lbl": "رسالة إشعار الانتهاء للعميل:",
        "default_finish_note": "تم الانتهاء من صيانة جهازك بنجاح وهو جاهز.",
        "finish_repair_btn": "🔔 إنهاء الصيانة وإرسال إشعار للعميل",
        "move_bill_after_finish": "نقل التذكرة إلى قسم الحساب بعد إشعار الانتهاء",
        "finished_notify_msg": "🔔 تم إنهاء الصيانة للتذكرة `{tid}` وإرسال إشعار للعميل بنجاح.",
        "portal_title": "📱 بوابة متابعة العميل — الإشعارات والاعتماد",
        "portal_caption": "أدخل اسمك ورقم الجوال المسجل لمتابعة حالة جهازك، اعتماد أو رفض التكلفة، واستلام إشعارات الصيانة.",
        "portal_name_lbl": "اسم العميل",
        "portal_phone_lbl": "رقم الجوال",
        "portal_login_btn": "🔍 عرض طلباتي",
        "portal_logout_btn": "🚪 خروج من حساب العميل",
        "portal_not_found": "❌ لم يتم العثور على تذكرة مطابقة للاسم ورقم الجوال المدخلين.",
        "portal_pick_ticket": "اختر التذكرة:",
        "msg_box_title": "📩 تفاصيل الجهاز وحالة الصيانة",
        "msg_issue_lbl": "**العطل المحدد:** {issues}",
        "msg_dec_lbl": "**الإجراء المقترح:** {decision}",
        "msg_specs_lbl": "**المواصفات المفحوصة:** {specs}",
        "msg_cost_lbl": "**التكلفة المحددة:** `{cost}`",
        "msg_tech_lbl": "**ملاحظات الفني:** {notes}",
        "approve_btn": "✅ اعتماد العطل والتكلفة وبدء الصيانة",
        "reject_btn": "❌ رفض التكلفة — سأحضر لاستلام جهازي",
        "approved_start_msg": "✅ تم اعتماد التكلفة! بدأت الصيانة الآن على التذكرة `{tid}` وسيصلك إشعار فور الانتهاء.",
        "rejected_done": "🛑 تم تسجيل رفض التكلفة للتذكرة `{tid}`. يمكنك التوجه لمركز الصيانة لاستلام جهازك.",
        "notify_completed_banner": "🔔 **إشعار جديد:** تم الانتهاء من صيانة جهازك للتذكرة `{tid}`! {notes}",
        "notify_in_progress_banner": "🛠️ **إشعار الصيانة:** تم اعتماد طلبك وبدأت الصيانة على التذكرة `{tid}`.",
        "bill_title": "💳 قسم الحساب — الفواتير واعتماد الدفع",
        "bill_caption": "تظهر هنا التذاكر المحوّلة إلى قسم الحساب فقط.",
        "no_bill_tickets": "📭 لا توجد فواتير محوّلة إلى قسم الحساب حالياً.",
        "m_in_bill": "فواتير في الحساب",
        "m_paid": "فواتير مدفوعة",
        "m_unpaid": "فواتير غير مدفوعة",
        "filter_pay_lbl": "فلترة فواتير الحساب حسب حالة الدفع:",
        "pay_filter_opts": ["الكل", "غير مدفوع", "مدفوع"],
        "bill_table_title": "#### 📄 فواتير قسم الحساب",
        "no_matching_bills": "لا توجد فواتير في قسم الحساب تطابق حالة الدفع المحددة.",
        "bill_mgmt": "#### 🧾 اعتماد / تحديث فاتورة التذكرة",
        "pick_ticket_bill": "اختر الفاتورة المخصصة للحساب:",
        "final_cost": "مبلغ الفاتورة (ر.س)",
        "pay_status": "حالة الدفع",
        "pay_opts": ["غير مدفوع", "مدفوع"],
        "save_bill_btn": "💾 حفظ الفاتورة وتحديث حالة الدفع",
        "dl_invoice": "📥 تحميل الفاتورة (.txt)",
        "dl_csv_bill": "📊 تصدير فواتير الحساب (.csv)",
        "mgr_title": "🔐 قسم المدير — دخول محمي برقم خاص",
        "mgr_warn": "هذا القسم مخصص للمدير ولا يُفتح إلا برقم الدخول الخاص. يمكن لمسؤول التوظيف الاطلاع على الرقم في تبويب «نبذة عن الموقع».",
        "pin_lbl": "أدخل رقم الدخول الخاص بالمدير:",
        "pin_ph": "مثال: MGR-2026",
        "unlock_btn": "🔓 دخول إلى لوحة المدير",
        "pin_ok": "✅ تم التحقق من رقم الدخول بنجاح.",
        "pin_err": "❌ رقم الدخول غير صحيح. راجع «نبذة عن الموقع» لمعرفة رقم الدخول المخصص للتجربة.",
        "lock_btn": "🔒 قفل / خروج من قسم المدير",
        "mgr_caption": "الإشراف العام، الإحصاءات، متابعة حالة الصيانة والاعتماد، البحث والفلترة، وحذف أو مسح السجلات.",
        "m_total": "إجمالي التذاكر",
        "m_urgent": "تذاكر عاجلة",
        "m_work": "في الصيانة / الحساب",
        "m_paid_mgr": "مدفوع",
        "rep_sn": "🔁 **أجهزة ذات تذاكر متكررة:** ",
        "rep_times": "مرات",
        "chart_stage": "#### 📈 توزيع التذاكر حسب القسم",
        "chart_dec": "#### 📈 توزيع التذاكر حسب القرار",
        "search_lbl": "🔎 بحث برقم التذكرة أو اسم العميل أو موظف الاستقبال أو رقم الجوال أو S/N",
        "filt_dept": "فلترة بالقسم",
        "filt_pay": "فلترة بالدفع",
        "all_opt": "الكل",
        "pick_del": "اختر تذكرة للإدارة / الحذف:",
        "del_btn": "🗑️ حذف التذكرة المحددة",
        "del_msg": "تم حذف التذكرة `{tid}`.",
        "dl_csv_mgr": "📊 تصدير السجل الكامل (.csv)",
        "add_demo": "✨ إضافة بيانات تجريبية",
        "clear_all": "🗑️ مسح جميع التذاكر",
        "about_title": "📌 نبذة عن الموقع",
        "about_desc": (
            "نظام ويب متكامل لإدارة الصيانة والدعم الفني برقم تذكرة واحد ثابت: "
            "الاستقبال ← الفحص ← اعتماد العميل ← بدء الصيانة ← إشعار الانتهاء للعميل ← الحساب، "
            "مع بوابة متابعة للعميل بالاسم والجوال وقسم مدير محمي."
        ),
        "mgr_creds_title": "#### 🔑 بيانات دخول قسم المدير (لمسؤولي التوظيف والمستعرضين)",
        "mgr_pin_line": "**رقم الدخول الخاص بالمدير:** `{pin}`",
        "mgr_pin_hint": "انتقل إلى تبويب «المدير» وأدخل الرقم أعلاه لتجربة لوحة الإدارة والإحصاءات.",
        "feats_title": "#### ✨ أبرز مزايا النظام:",
        "feats": [
            "- **بدء الصيانة بعد الاعتماد:** بمجرد اعتماد العميل تبدأ الصيانة على الجهاز فوراً.",
            "- **إشعار عند الانتهاء:** عند إنهاء الصيانة يظهر إشعار للعميل في بوابته بأن الجهاز جاهز.",
            "- **عزل الأقسام والتقارير:** كل قسم يرى ما يخصه، مع حفظ SQLite وتصدير .txt و.csv.",
        ],
    },
    "en": {
        "page_title": "IT Helpdesk & Maintenance System",
        "dir": "ltr",
        "align": "left",
        "banner_title": "🏢 IT Helpdesk & Maintenance System",
        "banner_sub": "Reception → Inspection → Customer Approval → Repair Starts → Completion Notice → Billing",
        "nav_label": "Navigate departments:",
        "depts": ["Reception", "Maintenance", "Customer Portal", "Billing", "Manager", "About"],
        "stage_lbl": {
            "Reception": "Reception",
            "Maintenance": "Maintenance",
            "Billing": "Billing",
        },
        "pay_lbl": {
            "Unpaid": "Unpaid",
            "Paid": "Paid",
        },
        "appr_lbl": {
            "Pending": "Awaiting Customer",
            "Approved": "Customer Approved",
            "Rejected": "Rejected — Pickup Ready",
        },
        "repair_lbl": {
            "Pending": "Not Started",
            "In Progress": "Repair In Progress",
            "Completed": "Repair Completed",
        },
        "active_ticket_bar": "**Active Ticket:** `{tid}` | **Customer:** {cust} | **Stage:** `{stage}` | **Repair:** `{rep}`",
        "rec_title": "🛎️ Reception — Customer Registration & Ticket Creation",
        "rec_caption": "Starts a single ticket ID across Maintenance, Customer Approval, Repair Execution, and Billing.",
        "new_tid_msg": "**Ticket ID:** `{tid}`",
        "cust_name": "Customer Name",
        "rec_staff": "Receptionist Name",
        "mobile": "Mobile Number",
        "sn": "Serial Number / IMEI",
        "dev_type": "Device Type",
        "brand": "Manufacturer / Brand",
        "priority": "Priority",
        "priorities": ["Normal", "Medium", "Urgent"],
        "rec_date": "Reception Date",
        "init_note": "Customer issue description at reception:",
        "init_note_ph": "Example: Cracked screen, fast battery drain, or slow performance...",
        "go_maint": "Send ticket with the same ID to Maintenance after saving",
        "save_rec_btn": "📥 Save Ticket & Forward",
        "default_rec_note": "Registered at reception pending serious technical inspection.",
        "saved_rec_msg": "✅ Ticket `{tid}` saved.",
        "reg_tickets": "📋 Registered Tickets",
        "no_tickets": "No tickets registered yet.",
        "load_demo": "✨ Load Demo Data",
        "maint_title": "🔧 Maintenance — Inspection, Repair Execution & Completion Notice",
        "maint_caption": "Only Maintenance tickets appear here. Send fault & cost for approval; once approved, repair starts and notifies customer when done.",
        "no_maint_tickets": "📭 No tickets assigned to Maintenance right now.",
        "go_rec_btn": "🛎️ Go to Reception",
        "pick_ticket_maint": "Select Maintenance ticket to inspect:",
        "fixed_tid": "**Ticket ID:** `{tid}` | **Approval:** `{appr}` | **Repair Status:** `{rep}`",
        "cust_info_line": "**Customer:** {cust} | **Receptionist:** {staff} | **Mobile:** {phone}",
        "dev_info_line": "**Device:** {dtype} — {brand} (`{sn}`)",
        "prev_notes": "**Previous Notes:** {notes}",
        "specs_sec": "#### 1️⃣ Device Specifications",
        "age_lbl": "Device Age (Years)",
        "ram_lbl": "RAM",
        "stor_lbl": "Storage",
        "stor_opts_pc": ["HDD", "SATA SSD", "NVMe M.2 SSD"],
        "cap_lbl_mob": "Storage Capacity",
        "cap_opts_mob": ["64 GB", "128 GB", "256 GB", "512 GB", "1 TB"],
        "os_lbl_mob": "Operating System",
        "os_opts_mob": ["iOS / iPadOS", "Android", "HarmonyOS", "Windows"],
        "issues_sec": "#### 2️⃣ Select Verified Faults",
        "tabs": ["⚙️ Hardware & Parts", "💻 OS & Software", "🌐 Network & Connectivity"],
        "c_slow": "Noticeable slowness or frequent freezing",
        "c_heat": "Overheating or loud fan noise",
        "c_bsod": "Blue screen (BSOD) or random restarts",
        "c_noise": "Mechanical clicking noise from drive",
        "m_screen": "Cracked screen or unresponsive touch",
        "m_batt": "Degraded battery or fast drain",
        "m_port": "Charging port or speaker fault",
        "m_cam": "Camera or physical button fault",
        "c_boot": "Boot failure / stuck on logo",
        "c_virus": "Suspected malware or pop-up ads",
        "c_corrupt": "OS update or app issue",
        "c_net": "Wi-Fi drops or weak signal",
        "c_domain": "Cellular SIM / Bluetooth / Network issue",
        "cost_sec": "#### 3️⃣ Repair Cost & Technician Findings",
        "est_cost_lbl": "Estimated Repair Cost (SAR)",
        "tech_lbl": "Technician Name",
        "tech_notes_lbl": "Fault Report & Cost Explanation for Customer:",
        "save_diag_btn": "📤 Save Inspection & Send Fault/Cost to Customer",
        "sent_to_cust_msg": "✅ Inspection saved and fault/cost message sent for ticket `{tid}`.",
        "exec_sec": "#### 4️⃣ Repair Execution & Completion Notification",
        "await_appr_warn": "⏳ Waiting for customer approval of fault & cost before starting repair.",
        "repair_started_info": "🛠️ Customer approved the cost — repair is in progress.",
        "finish_note_lbl": "Completion notification message for customer:",
        "default_finish_note": "Your device repair is completed and ready.",
        "finish_repair_btn": "🔔 Complete Repair & Notify Customer",
        "move_bill_after_finish": "Forward ticket to Billing after sending completion notice",
        "finished_notify_msg": "🔔 Repair completed for ticket `{tid}` and customer notified.",
        "portal_title": "📱 Customer Portal — Notifications & Approval",
        "portal_caption": "Sign in with your name and mobile number to approve or reject repair cost and receive repair notifications.",
        "portal_name_lbl": "Customer Name",
        "portal_phone_lbl": "Mobile Number",
        "portal_login_btn": "🔍 View My Tickets",
        "portal_logout_btn": "🚪 Sign Out",
        "portal_not_found": "❌ No ticket found matching that name and mobile number.",
        "portal_pick_ticket": "Select ticket:",
        "msg_box_title": "📩 Device Details & Repair Status",
        "msg_issue_lbl": "**Identified Fault:** {issues}",
        "msg_dec_lbl": "**Recommended Action:** {decision}",
        "msg_specs_lbl": "**Inspected Specs:** {specs}",
        "msg_cost_lbl": "**Quoted Cost:** `{cost}`",
        "msg_tech_lbl": "**Technician Notes:** {notes}",
        "approve_btn": "✅ Approve Fault & Cost — Start Repair",
        "reject_btn": "❌ Reject Cost — I Will Pick Up My Device",
        "approved_start_msg": "✅ Approved! Repair has started on ticket `{tid}` and you will be notified once finished.",
        "rejected_done": "🛑 Rejected for ticket `{tid}`. Please visit the service center to pick up your device.",
        "notify_completed_banner": "🔔 **Completion Notification:** Repair is finished for ticket `{tid}`! {notes}",
        "notify_in_progress_banner": "🛠️ **Repair Update:** Your request is approved and repair is in progress on ticket `{tid}`.",
        "bill_title": "💳 Billing — Invoices & Payment Status",
        "bill_caption": "Only tickets transferred to Billing appear here.",
        "no_bill_tickets": "📭 No invoices assigned to Billing right now.",
        "m_in_bill": "Billing Invoices",
        "m_paid": "Paid Invoices",
        "m_unpaid": "Unpaid Invoices",
        "filter_pay_lbl": "Filter Billing Invoices by Payment:",
        "pay_filter_opts": ["All", "Unpaid", "Paid"],
        "bill_table_title": "#### 📄 Billing Invoices",
        "no_matching_bills": "No Billing invoices match the selected payment status.",
        "bill_mgmt": "#### 🧾 Ticket Invoice & Payment",
        "pick_ticket_bill": "Select Billing invoice:",
        "final_cost": "Invoice Amount (SAR)",
        "pay_status": "Payment Status",
        "pay_opts": ["Unpaid", "Paid"],
        "save_bill_btn": "💾 Save Invoice & Payment",
        "dl_invoice": "📥 Download Invoice (.txt)",
        "dl_csv_bill": "📊 Export Billing Invoices (.csv)",
        "mgr_title": "🔐 Manager — PIN Protected Access",
        "mgr_warn": "Restricted to Manager access. Recruiters can view the demo PIN under the «About» tab.",
        "pin_lbl": "Enter Manager Access PIN:",
        "pin_ph": "Example: MGR-2026",
        "unlock_btn": "🔓 Unlock Manager View",
        "pin_ok": "✅ PIN verified successfully.",
        "pin_err": "❌ Invalid PIN. Check «About» for the demo access PIN.",
        "lock_btn": "🔒 Lock / Exit Manager View",
        "mgr_caption": "Oversight, analytics, repair/approval status, search/filtering, and deleting or clearing records.",
        "m_total": "Total Tickets",
        "m_urgent": "Urgent Tickets",
        "m_work": "Maintenance / Billing",
        "m_paid_mgr": "Paid",
        "rep_sn": "🔁 **Repeated Devices:** ",
        "rep_times": "times",
        "chart_stage": "#### 📈 Tickets by Stage",
        "chart_dec": "#### 📈 Tickets by Decision",
        "search_lbl": "🔎 Search by Ticket ID, Customer, Receptionist, Mobile, or S/N",
        "filt_dept": "Filter by Stage",
        "filt_pay": "Filter by Payment",
        "all_opt": "All",
        "pick_del": "Select ticket to manage / delete:",
        "del_btn": "🗑️ Delete Selected Ticket",
        "del_msg": "Deleted ticket `{tid}`.",
        "dl_csv_mgr": "📊 Export Full Log (.csv)",
        "add_demo": "✨ Add Demo Data",
        "clear_all": "🗑️ Clear All Tickets",
        "about_title": "📌 About This App",
        "about_desc": (
            "A bilingual helpdesk & maintenance web app with a single ticket ID across "
            "Reception → Inspection → Customer Approval → Repair Starts → Completion Notification → Billing, "
            "plus a customer portal by name & mobile and a PIN-protected Manager view."
        ),
        "mgr_creds_title": "#### 🔑 Manager Access Credentials (For Recruiters & Reviewers)",
        "mgr_pin_line": "**Manager Access PIN:** `{pin}`",
        "mgr_pin_hint": "Switch to the «Manager» tab and enter the PIN above to test the admin dashboard.",
        "feats_title": "#### ✨ Key Features:",
        "feats": [
            "- **Repair Starts on Approval:** Once the customer approves, repair status moves to In Progress.",
            "- **Completion Notification:** Finishing repair sends a clear completion notice to the customer portal.",
            "- **Scoped Queues & Exports:** Each department sees only relevant tickets, with SQLite and .txt / .csv exports.",
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

if "customer_auth" not in st.session_state:
    st.session_state.customer_auth = None

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
if not df_all.empty:
    df_all["stage_code"] = df_all["stage"].map(normalize_stage)
    df_all["pay_code"] = df_all["payment_status"].map(normalize_payment)
    df_all["appr_code"] = df_all["approval_status"].map(normalize_approval)
    df_all["rep_code"] = df_all["repair_status"].map(normalize_repair)
    df_all["stage_disp"] = df_all["stage_code"].map(t["stage_lbl"])
    df_all["pay_disp"] = df_all["pay_code"].map(t["pay_lbl"])
    df_all["appr_disp"] = df_all["appr_code"].map(t["appr_lbl"])
    df_all["rep_disp"] = df_all["rep_code"].map(t["repair_lbl"])

if st.session_state.current_ticket_id and not df_all.empty:
    match_cur = df_all[df_all["ticket_id"] == st.session_state.current_ticket_id]
    if not match_cur.empty:
        cur_row = match_cur.iloc[0]
        st.info(
            t["active_ticket_bar"].format(
                tid=cur_row["ticket_id"],
                cust=cur_row["customer_name"],
                stage=cur_row["stage_disp"],
                rep=cur_row["rep_disp"],
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

    lang_brands_map = DEVICE_BRANDS[st.session_state.lang]
    device_type_options = list(lang_brands_map.keys())

    c_ty, c_br = st.columns(2)
    with c_ty:
        device_type = st.selectbox(t["dev_type"], device_type_options)
    with c_br:
        matching_brands = lang_brands_map[device_type]
        brand = st.selectbox(t["brand"], matching_brands)

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
            INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            "Pending",
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
        if st.session_state.lang == "ar":
            disp_df = df_all.rename(columns={
                "ticket_id": "رقم التذكرة",
                "customer_name": "اسم العميل",
                "reception_staff": "موظف الاستقبال",
                "customer_phone": "رقم الجوال",
                "device_type": "نوع الجهاز",
                "stage_disp": "القسم",
                "rep_disp": "حالة الصيانة",
            })
            st.dataframe(
                disp_df[["رقم التذكرة", "اسم العميل", "موظف الاستقبال", "رقم الجوال", "نوع الجهاز", "القسم", "حالة الصيانة"]],
                use_container_width=True,
            )
        else:
            disp_df = df_all.rename(columns={
                "ticket_id": "Ticket ID",
                "customer_name": "Customer",
                "reception_staff": "Receptionist",
                "customer_phone": "Mobile",
                "device_type": "Device",
                "stage_disp": "Stage",
                "rep_disp": "Repair Status",
            })
            st.dataframe(
                disp_df[["Ticket ID", "Customer", "Receptionist", "Mobile", "Device", "Stage", "Repair Status"]],
                use_container_width=True,
            )

# ==========================================
# 1. الصيانة / Maintenance (تذاكر الصيانة فقط)
# ==========================================
elif dept_idx == 1:
    st.subheader(t["maint_title"])
    st.caption(t["maint_caption"])

    maint_df = df_all[df_all["stage_code"] == "Maintenance"].copy() if not df_all.empty else pd.DataFrame()

    if maint_df.empty:
        st.info(t["no_maint_tickets"])
        c_b1, c_b2 = st.columns(2)
        if df_all.empty and c_b1.button(t["load_demo"]):
            load_demo_data()
            st.rerun()
        if c_b2.button(t["go_rec_btn"]):
            st.session_state.active_dept_idx = 0
            st.rerun()
    else:
        ticket_ids = maint_df["ticket_id"].tolist()
        default_idx = 0
        if st.session_state.current_ticket_id in ticket_ids:
            default_idx = ticket_ids.index(st.session_state.current_ticket_id)

        def fmt_maint(tid):
            r = maint_df[maint_df["ticket_id"] == tid].iloc[0]
            return f"{r['ticket_id']} | {r['customer_name']} ({r['rep_disp']})"

        chosen_id = st.selectbox(t["pick_ticket_maint"], ticket_ids, index=default_idx, format_func=fmt_maint)
        st.session_state.current_ticket_id = chosen_id
        row = maint_df(maint_df["ticket_id"] ==
