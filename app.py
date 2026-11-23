import html
import json
import random
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

MANAGER_PIN = "MGR-2026"

TECH_OPTIONS = [
    "فهد المطيري",
    "خالد الشمري",
    "عبدالله الحربي",
    "مشاري العتيبي",
    "فني آخر (اكتب الاسم)",
]

conn = sqlite3.connect("enterprise_helpdesk_lena_fix_v1.db", check_same_thread=False)
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
        device_specs TEXT,
        customer_issue TEXT,
        repaired_text TEXT,
        tech_notes TEXT,
        priority TEXT,
        decision TEXT,
        stage TEXT,
        payment_status TEXT,
        payment_method TEXT,
        ticket_date TEXT,
        technician_name TEXT,
        cost_est TEXT,
        status_history TEXT
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


def is_mobile_or_tablet(dtype_str):
    keywords = ["جوال", "آيباد", "لوحي", "Smartphone", "iPad", "Tablet"]
    return any(k in (dtype_str or "") for k in keywords)


def append_history(existing_json, actor_stage, summary_text):
    try:
        items = json.loads(existing_json) if existing_json else []
        if not isinstance(items, list):
            items = []
    except Exception:
        items = []
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    items.append(f"[{stamp}] {actor_stage}: {summary_text}")
    return json.dumps(items, ensure_ascii=False)


def parse_history(raw_json):
    try:
        items = json.loads(raw_json) if raw_json else []
        return items if isinstance(items, list) else []
    except Exception:
        return []


def render_unified_document_card(
    row_dict,
    stage_label,
    is_rtl,
    mode="tracking",
    pay_label="",
    method_label="",
    final_amount="",
    is_paid=False,
):
    direction = "rtl" if is_rtl else "ltr"
    e = html.escape

    if mode == "billing":
        doc_title = "فاتورة الصيانة والدفع / Service Invoice"
        badge_bg = "#dcfce7" if is_paid else "#fef3c7"
        badge_fg = "#166534" if is_paid else "#92400e"
        badge_text = str(pay_label)
        third_cell = (
            f'<div><span style="color:#64748b;display:block;font-size:11px;">الفني / Technician</span>'
            f'<strong>{e(str(row_dict.get("technician_name", "-")))}</strong></div>'
        )
        work_section = (
            f'<div style="margin-bottom:12px;">'
            f'<div style="font-weight:700;color:#065f46;font-size:12.5px;margin-bottom:4px;">ما عمله الفني / Technician Work Done</div>'
            f'<div style="background:#ecfdf5;border-inline-start:4px solid #10b981;padding:9px 11px;border-radius:8px;font-size:13px;">'
            f'{e(str(row_dict.get("repaired_text", "-")))}</div>'
            f'</div>'
        )
        footer_html = (
            f'<div style="display:flex;justify-content:space-between;align-items:center;background:#0f294a;color:#ffffff;padding:12px 14px;border-radius:10px;gap:8px;flex-wrap:wrap;">'
            f'<div style="font-size:12px;">'
            f'<div>طريقة الدفع / Method: <strong>{e(str(method_label))}</strong></div>'
            f'<div style="color:#cffafe;margin-top:2px;">القسم / Stage: <strong>{e(str(stage_label))}</strong></div>'
            f'</div>'
            f'<div style="text-align:end;">'
            f'<div style="font-size:11px;color:#bae6fd;">الإجمالي / Total</div>'
            f'<div style="font-size:18px;font-weight:700;">{e(str(final_amount))}</div>'
            f'</div>'
            f'</div>'
        )
        card_height = 505
    else:
        doc_title = "فاتورة متابعة الجهاز / Tracking Receipt"
        badge_bg = "#e0f2fe"
        badge_fg = "#0369a1"
        badge_text = str(stage_label)
        third_cell = (
            f'<div><span style="color:#64748b;display:block;font-size:11px;">موظف الاستقبال / Staff</span>'
            f'<strong>{e(str(row_dict.get("reception_staff", "-")))}</strong></div>'
        )
        work_section = ""
        footer_html = (
            f'<div style="display:flex;justify-content:space-between;align-items:center;background:#0f294a;color:#ffffff;padding:12px 14px;border-radius:10px;gap:8px;flex-wrap:wrap;">'
            f'<div style="font-size:12px;">'
            f'<div>الأولوية / Priority: <strong>{e(str(row_dict.get("priority", "-")))}</strong></div>'
            f'<div style="color:#cffafe;margin-top:2px;">حالة المتابعة / Stage: <strong>{e(str(stage_label))}</strong></div>'
            f'</div>'
            f'<div style="text-align:end;font-size:12px;color:#bae6fd;">'
            f'متابعة الجهاز برقم التذكرة'
            f'</div>'
            f'</div>'
        )
        card_height = 420

    card_html = (
        f'<div dir="{direction}" style="font-family:Segoe UI,Tahoma,sans-serif;background:#ffffff;border:2px solid #0284c7;border-radius:14px;padding:18px;color:#0f294a;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #e2e8f0;padding-bottom:10px;margin-bottom:12px;gap:8px;flex-wrap:wrap;">'
        f'<div>'
        f'<div style="font-size:17px;font-weight:700;color:#0f294a;">{e(doc_title)}</div>'
        f'<div style="font-size:12px;color:#64748b;margin-top:2px;">رقم التذكرة: <strong>{e(str(row_dict.get("ticket_id", "-")))}</strong> | التاريخ: <strong>{e(str(row_dict.get("ticket_date", "-")))}</strong></div>'
        f'</div>'
        f'<span style="background:{badge_bg};color:{badge_fg};padding:5px 12px;border-radius:999px;font-weight:700;font-size:12px;">{e(badge_text)}</span>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:repeat(2,minmax(140px,1fr));gap:8px;background:#f8fafc;border:1px solid #e2e8f0;padding:10px;border-radius:10px;margin-bottom:12px;font-size:12.5px;">'
        f'<div><span style="color:#64748b;display:block;font-size:11px;">العميل / Customer</span><strong>{e(str(row_dict.get("customer_name", "-")))}</strong></div>'
        f'<div><span style="color:#64748b;display:block;font-size:11px;">الجوال / Mobile</span><strong>{e(str(row_dict.get("customer_phone", "-")))}</strong></div>'
        f'{third_cell}'
        f'<div><span style="color:#64748b;display:block;font-size:11px;">الجهاز / Device</span><strong>{e(str(row_dict.get("device_type", "-")))} - {e(str(row_dict.get("brand", "-")))}</strong></div>'
        f'<div><span style="color:#64748b;display:block;font-size:11px;">S/N / IMEI</span><strong>{e(str(row_dict.get("device_sn", "-")))}</strong></div>'
        f'<div><span style="color:#64748b;display:block;font-size:11px;">مواصفات الجهاز / Specs</span><strong>{e(str(row_dict.get("device_specs", "-")))}</strong></div>'
        f'</div>'
        f'<div style="margin-bottom:10px;">'
        f'<div style="font-weight:700;color:#92400e;font-size:12.5px;margin-bottom:4px;">مشكلة الجهاز / Reported Issue</div>'
        f'<div style="background:#fffbeb;border-inline-start:4px solid #f59e0b;padding:9px 11px;border-radius:8px;font-size:13px;">{e(str(row_dict.get("customer_issue", "-")))}</div>'
        f'</div>'
        f'{work_section}'
        f'{footer_html}'
        f'<div style="margin-top:12px;text-align:center;">'
        f'<button onclick="window.print()" style="background:#0e7490;color:#ffffff;border:none;padding:9px 20px;border-radius:8px;font-weight:700;cursor:pointer;font-size:13px;">طباعة / Print</button>'
        f'</div>'
        f'</div>'
    )
    components.html(card_html, height=card_height, scrolling=True)


def render_all_customers_single_invoice(df_src, is_rtl):
    direction = "rtl" if is_rtl else "ltr"
    e = html.escape
    today_str = datetime.now().strftime("%Y-%m-%d")

    if df_src.empty:
        body_items = (
            f'<div style="padding:14px;text-align:center;color:#64748b;font-size:13px;">'
            f'لا توجد بيانات عملاء مسجلة حالياً.'
            f'</div>'
        )
    else:
        blocks = []
        for idx, (_, r) in enumerate(df_src.iterrows(), start=1):
            blocks.append(
                f'<div style="border:1px solid #cbd5e1;background:#f8fafc;border-radius:10px;padding:11px 13px;margin-bottom:10px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:6px;border-bottom:1px solid #e2e8f0;padding-bottom:5px;">'
                f'<span style="font-weight:700;color:#0f294a;font-size:13px;">{idx}. العميل: {e(str(r.get("customer_name", "-")))} | تذكرة: {e(str(r.get("ticket_id", "-")))}</span>'
                f'<span style="background:#e0f2fe;color:#0369a1;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:700;">{e(str(r.get("stage_disp", "-")))}</span>'
                f'</div>'
                f'<div style="font-size:12px;color:#0f294a;line-height:1.65;">'
                f'<strong>الجوال:</strong> {e(str(r.get("customer_phone", "-")))} | '
                f'<strong>الاستقبال:</strong> {e(str(r.get("reception_staff", "-")))} | '
                f'<strong>الفني:</strong> {e(str(r.get("technician_name", "-")))}<br>'
                f'<strong>الجهاز:</strong> {e(str(r.get("device_type", "-")))} - {e(str(r.get("brand", "-")))} | '
                f'<strong>S/N:</strong> {e(str(r.get("device_sn", "-")))} | '
                f'<strong>المواصفات:</strong> {e(str(r.get("device_specs", "-")))}<br>'
                f'<strong>مشكلة الجهاز:</strong> {e(str(r.get("customer_issue", "-")))}<br>'
                f'<strong>ما عمله الفني:</strong> {e(str(r.get("repaired_text", "-")))}<br>'
                f'<strong>الدفع:</strong> {e(str(r.get("pay_disp", "-")))} ({e(str(r.get("payment_method", "-")))}) | '
                f'<strong>المبلغ:</strong> {e(str(r.get("cost_est", "-")))}'
                f'</div>'
                f'</div>'
            )
        body_items = "".join(blocks)

    card_html = (
        f'<div dir="{direction}" style="font-family:Segoe UI,Tahoma,sans-serif;background:#ffffff;border:2px solid #0284c7;border-radius:14px;padding:18px;color:#0f294a;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #e2e8f0;padding-bottom:10px;margin-bottom:12px;gap:8px;flex-wrap:wrap;">'
        f'<div>'
        f'<div style="font-size:17px;font-weight:700;color:#0f294a;">فاتورة الإدارة الموحدة لجميع العملاء / All Customers Invoice</div>'
        f'<div style="font-size:12px;color:#64748b;margin-top:2px;">التاريخ: <strong>{e(today_str)}</strong></div>'
        f'</div>'
        f'<span style="background:#e0f2fe;color:#0369a1;padding:5px 12px;border-radius:999px;font-weight:700;font-size:12px;">إجمالي العملاء: {len(df_src)}</span>'
        f'</div>'
        f'{body_items}'
        f'<div style="display:flex;justify-content:space-between;align-items:center;background:#0f294a;color:#ffffff;padding:12px 14px;border-radius:10px;margin-top:10px;font-size:12.5px;">'
        f'<span>القسم: <strong>الإدارة / Management</strong></span>'
        f'<span>عدد السجلات: <strong>{len(df_src)}</strong></span>'
        f'</div>'
        f'<div style="margin-top:12px;text-align:center;">'
        f'<button onclick="window.print()" style="background:#0e7490;color:#ffffff;border:none;padding:9px 20px;border-radius:8px;font-weight:700;cursor:pointer;font-size:13px;">طباعة / Print</button>'
        f'</div>'
        f'</div>'
    )
    dynamic_h = min(820, max(320, 220 + len(df_src) * 145))
    components.html(card_html, height=dynamic_h, scrolling=True)


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
            "جوال (Smartphone)", "Apple",
            "256 GB | iOS / iPadOS | 2 سنة",
            "البطارية تفرغ بسرعة خلال ساعتين وتنطفئ فجأة عند 25%.",
            "تم استبدال البطارية التالفة وفحص دورة الشحن بالكامل.",
            "تم اختبار الجهاز بعد الإصلاح وثبتت كفاءة الشحن.",
            "متوسطة", "إصلاح عطل / استبدال قطعة", "Billing", "Paid", "مدى (Mada)",
            "2026-11-18", "فهد المطيري", "250 SAR",
            append_history(
                append_history(
                    append_history("[]", "الاستقبال", "تم تسجيل الجهاز وإصدار فاتورة متابعة."),
                    "الصيانة",
                    "تم استبدال البطارية وتوثيق العمل الفني."
                ),
                "الحساب",
                "تم تأكيد الدفع عبر مدى وإصدار الفاتورة النهائية."
            )
        ),
        (
            "TK-40102", "عمر الزهراني", "سالم الدوسري", "0559988776", "SN-HP-61904",
            "لابتوب (Laptop)", "HP",
            "8 GB | SATA SSD | 2 سنة",
            "الجهاز يفصل الواي فاي باستمرار ويوجد بطء في فتح البرامج.",
            "لم يُسجل بعد",
            "جاري فحص تعريف الشبكة وصيانة النظام.",
            "عادية", "صيانة برمجية ونظام", "Maintenance", "Unpaid", "لم يُحدد بعد",
            "2026-11-19", "خالد الشمري", "90 SAR",
            append_history(
                append_history("[]", "الاستقبال", "تم تسجيل الجهاز وإصدار فاتورة متابعة."),
                "الصيانة",
                "الجهاز قيد الفحص الفني."
            )
        ),
        (
            "TK-40103", "لينا الشهري", "سالم الدوسري", "0544433221", "SN-LN-48290",
            "كمبيوتر مكتبي (Desktop PC)", "Lenovo",
            "8 GB | HDD تقليدي | 8 سنوات",
            "يصدر صوت طقطقة من الداخل ولا يقلع إلى النظام.",
            "لم يُسجل بعد",
            "تم فحص القرص الميكانيكي ويوصى باستبدال الجهاز.",
            "عاجلة", "توصية باستبدال الجهاز", "Maintenance", "Unpaid", "لم يُحدد بعد",
            "2026-11-20", "عبدالله الحربي", "3,200 SAR",
            append_history(
                append_history("[]", "الاستقبال", "تم تسجيل الجهاز وإصدار فاتورة متابعة."),
                "الصيانة",
                "تم تحويل التذكرة إلى قسم الصيانة للفحص."
            )
        ),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        sample_tickets
    )
    conn.commit()


TEXTS = {
    "ar": {
        "page_title": "نظام إدارة مركز الصيانة والدعم الفني",
        "dir": "rtl",
        "align": "right",
        "banner_title": "🏢 نظام إدارة مركز الصيانة والدعم الفني",
        "banner_sub": "مسار فاتورة وتذكرة موحد مع سجل تتبع من الاستقبال إلى الصيانة ثم الحساب",
        "nav_label": "الأقسام:",
        "depts": ["الاستقبال", "الصيانة", "الحساب", "المدير", "نبذة عن الموقع"],
        "stage_lbl": {
            "Reception": "الاستقبال",
            "Maintenance": "الصيانة",
            "Billing": "الحساب",
        },
        "stage_opts": ["الاستقبال", "الصيانة", "الحساب"],
        "pay_lbl": {
            "Unpaid": "غير مدفوع",
            "Paid": "مدفوع",
        },
        "pay_methods": ["نقدي (Cash)", "مدى (Mada)", "بطاقة ائتمان / Apple Pay", "تحويل بنكي"],
        "active_ticket_bar": "التذكرة النشطة: <strong>{tid}</strong> &nbsp;|&nbsp; العميل: <strong>{cust}</strong> &nbsp;|&nbsp; الجهاز: <strong>{dev}</strong> &nbsp;|&nbsp; القسم: <strong>{stage}</strong> &nbsp;|&nbsp; الدفع: <strong>{pay}</strong>",
        "rec_title": "🛎️ قسم الاستقبال — تسجيل العميل ومواصفات الجهاز وإصدار فاتورة المتابعة",
        "rec_caption": "يُصدر للعميل فاتورة متابعة بنفس البطاقة الجديدة الموحدة.",
        "new_tid_msg": "**رقم التذكرة والفاتورة المخصص:** `{tid}`",
        "cust_name": "اسم العميل",
        "rec_staff": "اسم موظف الاستقبال",
        "mobile": "رقم الجوال",
        "sn": "الرقم التسلسلي / IMEI",
        "dev_type": "نوع الجهاز",
        "brand": "الشركة المصنعة",
        "rec_specs_sec": "#### 📱 مواصفات الجهاز",
        "age_lbl": "عمر الجهاز (بالسنوات)",
        "ram_lbl": "الذاكرة (RAM)",
        "stor_lbl": "التخزين",
        "stor_opts_pc": ["HDD تقليدي", "SATA SSD", "NVMe M.2 SSD"],
        "cap_lbl_mob": "السعة التخزينية",
        "cap_opts_mob": ["64 GB", "128 GB", "256 GB", "512 GB", "1 TB"],
        "os_lbl_mob": "نظام التشغيل",
        "os_opts_mob": ["iOS / iPadOS", "Android", "HarmonyOS", "Windows"],
        "priority": "الأولوية",
        "priorities": ["عادية", "متوسطة", "عاجلة"],
        "rec_date": "تاريخ الاستقبال",
        "init_note": "وصف المشكلة من العميل عند الاستقبال:",
        "init_note_ph": "مثال: الشاشة مكسورة، البطارية تفرغ بسرعة، أو الجهاز بطيء...",
        "go_maint": "نقل التذكرة بنفس الرقم إلى قسم الصيانة بعد الحفظ",
        "assign_tech_lbl": "تعيين فني الصيانة عند النقل للصيانة:",
        "custom_tech_lbl": "اكتب اسم فني الصيانة:",
        "save_rec_btn": "📥 حفظ التذكرة وإصدار فاتورة المتابعة",
        "default_rec_note": "تم تسجيل الجهاز في الاستقبال بانتظار الصيانة.",
        "saved_rec_msg": "✅ تم حفظ التذكرة برقم `{tid}` وإصدار فاتورة المتابعة.",
        "show_track_card_btn": "🧾 عرض فاتورة المتابعة",
        "hide_track_card_btn": "✖️ إخفاء فاتورة المتابعة",
        "reg_tickets": "📋 التذاكر المسجلة وتتبع حالة الجهاز",
        "track_search": "بحث سريع برقم التذكرة أو اسم العميل أو الجوال:",
        "track_pick": "اختر تذكرة لعرض فاتورة المتابعة وسجل الحركات:",
        "timeline_title": "🕒 سجل تتبع حالة الجهاز (Audit Log)",
        "no_tickets": "لا توجد تذاكر مسجلة بعد.",
        "load_demo": "✨ تعبئة بيانات تجريبية للاختبار",
        "maint_title": "🔧 قسم الصيانة — كتابة ما عمله الفني",
        "maint_caption": "يعرض بيانات الجهاز ومشكلة العميل ويكتب الفني ما عمله بالتفصيل.",
        "no_maint_tickets": "📭 لا توجد تذاكر مخصصة لقسم الصيانة حالياً.",
        "go_rec_btn": "🛎️ الذهاب لقسم الاستقبال",
        "pick_ticket_maint": "اختر الجهاز / التذكرة الموجودة في الصيانة:",
        "fixed_tid": "**رقم التذكرة الثابت:** `{tid}` | **القسم الحالي:** `{stage}` | **الفني المسؤول:** `{tech}`",
        "cust_info_line": "**العميل:** {cust} | **موظف الاستقبال:** {staff} | **رقم الجوال:** {phone}",
        "dev_info_line": "**معلومات الجهاز:** {dtype} — {brand} (`{sn}`)",
        "specs_info_line": "**مواصفات الجهاز:** {specs}",
        "cust_issue_box": "**📝 مشكلة الجهاز عند الاستقبال:** {issue}",
        "repaired_box": "**✍️ ما عمله الفني مسجلاً:** {rep}",
        "prev_notes": "**ملاحظات فنية سابقة:** {notes}",
        "repair_write_sec": "#### 1️⃣ كتابة ما عمله الفني في الجهاز",
        "repaired_lbl": "اكتب ما عمله الفني بالتفصيل:",
        "repaired_ph": "مثال: تم فحص الدائرة وتغيير الشاشة وتنظيف المروحة واختبار التشغيل...",
        "repaired_empty_msg": "لم يُسجل عمل الفني بعد",
        "cost_sec": "#### 2️⃣ التكلفة وتقرير الفني",
        "decision_lbl": "الإجراء / التشخيص النهائي",
        "decision_opts": [
            "إصلاح عطل / استبدال قطعة",
            "صيانة برمجية ونظام",
            "صيانة وقائية وتنظيف",
            "توصية باستبدال الجهاز",
        ],
        "est_cost_lbl": "تكلفة الصيانة (ر.س)",
        "tech_lbl": "اسم فني الصيانة",
        "tech_notes_lbl": "ملاحظات إضافية لفني الصيانة:",
        "send_bill": "نقل التذكرة بنفس الرقم إلى قسم الحساب بعد الحفظ",
        "save_diag_btn": "🛠️ حفظ عمل الفني ونقل التذكرة",
        "saved_diag_msg": "✅ تم حفظ عمل الفني للتذكرة `{tid}`.",
        "bill_title": "💳 قسم الحساب — تأكيد الدفع وإصدار الفاتورة",
        "bill_caption": "يُعتمد الدفع وتُصدر فاتورة بنفس البطاقة الجديدة الموحدة عند ضغط زر الطباعة.",
        "no_bill_tickets": "📭 لا توجد فواتير محوّلة إلى قسم الحساب حالياً.",
        "m_in_bill": "فواتير في الحساب",
        "m_paid": "فواتير مدفوعة",
        "m_unpaid": "فواتير غير مدفوعة",
        "filter_pay_lbl": "فلترة فواتير الحساب حسب حالة الدفع:",
        "pay_filter_opts": ["الكل", "غير مدفوع", "مدفوع"],
        "bill_table_title": "#### 📄 فواتير قسم الحساب",
        "no_matching_bills": "لا توجد فواتير في قسم الحساب تطابق حالة الدفع المحددة.",
        "bill_mgmt": "#### 🧾 اعتماد الدفع وطباعة الفاتورة",
        "pick_ticket_bill": "اختر الفاتورة المخصصة للحساب:",
        "final_cost": "مبلغ الفاتورة (ر.س)",
        "pay_status": "حالة الدفع",
        "pay_opts": ["غير مدفوع", "مدفوع"],
        "pay_method_lbl": "طريقة الدفع",
        "move_stage": "إبقاء الفاتورة في الحساب أو إعادتها للصيانة:",
        "bill_stage_choices": ["الحساب", "الصيانة"],
        "save_bill_btn": "💾 حفظ حالة الدفع",
        "print_btn": "🖨️ طباعة الفاتورة",
        "hide_print_btn": "✖️ إخفاء الفاتورة",
        "mgr_title": "🔐 قسم المدير — جميع الصلاحيات والإدارة الكاملة",
        "mgr_warn": "هذا القسم مخصص للمدير ولا يُفتح إلا برقم الدخول الخاص. يمكن لمسؤول التوظيف الاطلاع على الرقم في تبويب «نبذة عن الموقع».",
        "pin_lbl": "أدخل رقم الدخول الخاص بالمدير:",
        "pin_ph": "مثال: MGR-2026",
        "unlock_btn": "🔓 دخول إلى لوحة المدير",
        "pin_ok": "✅ تم التحقق من رقم الدخول وتفعيل جميع الصلاحيات.",
        "pin_err": "❌ رقم الدخول غير صحيح. راجع «نبذة عن الموقع» لمعرفة رقم الدخول المخصص للتجربة.",
        "lock_btn": "🔒 قفل / خروج من قسم المدير",
        "mgr_caption": "صلاحيات كاملة: الفاتورة الموحدة، التعديل، التحويل بين الأقسام، إضافة تذكرة، البحث والفلترة، والحذف.",
        "m_total": "إجمالي التذاكر",
        "m_urgent": "تذاكر عاجلة",
        "m_work": "في الصيانة / الحساب",
        "m_paid_mgr": "مدفوع",
        "rep_sn": "🔁 **أجهزة ذات تذاكر متكررة:** ",
        "rep_times": "مرات",
        "chart_stage": "#### 📈 توزيع التذاكر حسب القسم",
        "chart_dec": "#### 📈 توزيع التذاكر حسب القرار",
        "mgr_all_inv_sec": "#### 🧾 فاتورة الإدارة الموحدة لكل العملاء (فاتورة واحدة)",
        "mgr_all_inv_show": "🧾 عرض فاتورة كل العملاء",
        "mgr_all_inv_hide": "✖️ إخفاء فاتورة كل العملاء",
        "mgr_add_sec": "#### ➕ إضافة تذكرة جديدة وتوجيهها لأي قسم مباشرة",
        "mgr_target_stage": "القسم المبدئي للتذكرة",
        "mgr_decision_lbl": "القرار / التشخيص",
        "mgr_cost_lbl": "المبلغ / التكلفة",
        "mgr_create_btn": "➕ إنشاء التذكرة في النظام",
        "mgr_created_msg": "✅ تم إنشاء التذكرة `{tid}` في قسم `{stage}`.",
        "mgr_edit_sec": "#### 🛠️ تعديل وتحكم كامل بأي تذكرة عبر الأقسام",
        "mgr_pick_edit": "اختر العميل / التذكرة المراد إدارتها أو تعديلها:",
        "mgr_stage_lbl": "تحويل التذكرة إلى القسم",
        "mgr_specs_lbl": "مواصفات الجهاز",
        "mgr_rep_lbl": "ما عمله الفني (كتابة)",
        "mgr_notes_lbl": "الملاحظات والتقرير الفني",
        "mgr_save_edit_btn": "💾 حفظ جميع التعديلات على التذكرة",
        "mgr_saved_edit_msg": "✅ تم حفظ جميع تعديلات التذكرة `{tid}` وتحديث قسمها إلى `{stage}`.",
        "mgr_preview_type": "نوع الفاتورة للمعاينة / الطباعة للإدارة:",
        "mgr_preview_opts": ["فاتورة صيانة ودفع", "فاتورة متابعة (بدون حساب)"],
        "mgr_show_card_btn": "🧾 عرض فاتورة التذكرة بالشكل الجديد",
        "mgr_hide_card_btn": "✖️ إخفاء فاتورة التذكرة",
        "search_lbl": "🔎 بحث برقم التذكرة أو اسم العميل أو موظف الاستقبال أو رقم الجوال أو S/N",
        "filt_dept": "فلترة بالقسم",
        "filt_pay": "فلترة بالدفع",
        "all_opt": "الكل",
        "pick_del": "اختر تذكرة للحذف:",
        "del_btn": "🗑️ حذف التذكرة المحددة",
        "del_msg": "تم حذف التذكرة `{tid}`.",
        "add_demo": "✨ إضافة بيانات تجريبية",
        "clear_all": "🗑️ مسح جميع التذاكر",
        "about_title": "📌 نبذة عن الموقع",
        "about_desc": (
            "نظام ويب متكامل لإدارة أعمال الدعم الفني وصيانة الجوالات والأجهزة اللوحية والحواسيب برقم تذكرة وفاتورة واحد ثابت: "
            "جميع الفواتير تعرض بنفس الشكل الجديد الموحّد مع فاتورة واحدة تجمع كل العملاء في قسم الإدارة."
        ),
        "mgr_creds_title": "#### 🔑 بيانات دخول قسم المدير (لمسؤولي التوظيف والمستعرضين)",
        "mgr_pin_line": "**رقم الدخول الخاص بالمدير:** `{pin}`",
        "mgr_pin_hint": "انتقل إلى تبويب «المدير» وأدخل الرقم أعلاه لتجربة الإدارة الكاملة وفاتورة كل العملاء.",
        "feats_title": "#### ✨ أبرز مزايا النظام:",
        "feats": [
            "- **صلاحيات إدارية كاملة:** تعديل، تحويل، إضافة، بحث، وحذف جميع التذاكر من مكان واحد.",
            "- **فاتورة واحدة لكل العملاء في الإدارة:** تجمع كافة العملاء في فاتورة واحدة قابلة للطباعة المباشرة.",
            "- **سجل تتبع زمني (Audit Log):** يوثّق خطوات التذكرة عبر الأقسام بوضوح احترافي لمسؤولي التوظيف.",
        ],
    },
    "en": {
        "page_title": "IT Helpdesk & Maintenance System",
        "dir": "ltr",
        "align": "left",
        "banner_title": "🏢 IT Helpdesk & Maintenance System",
        "banner_sub": "Unified ticket & invoice workflow with audit history from Reception to Maintenance and Billing",
        "nav_label": "Departments:",
        "depts": ["Reception", "Maintenance", "Billing", "Manager", "About"],
        "stage_lbl": {
            "Reception": "Reception",
            "Maintenance": "Maintenance",
            "Billing": "Billing",
        },
        "stage_opts": ["Reception", "Maintenance", "Billing"],
        "pay_lbl": {
            "Unpaid": "Unpaid",
            "Paid": "Paid",
        },
        "pay_methods": ["Cash", "Mada", "Credit Card / Apple Pay", "Bank Transfer"],
        "active_ticket_bar": "Active Ticket: <strong>{tid}</strong> &nbsp;|&nbsp; Customer: <strong>{cust}</strong> &nbsp;|&nbsp; Device: <strong>{dev}</strong> &nbsp;|&nbsp; Stage: <strong>{stage}</strong> &nbsp;|&nbsp; Payment: <strong>{pay}</strong>",
        "rec_title": "🛎️ Reception — Intake, Device Specs & Tracking Receipt",
        "rec_caption": "Shows a tracking receipt using the new unified card.",
        "new_tid_msg": "**Ticket & Invoice ID:** `{tid}`",
        "cust_name": "Customer Name",
        "rec_staff": "Receptionist Name",
        "mobile": "Mobile Number",
        "sn": "Serial Number / IMEI",
        "dev_type": "Device Type",
        "brand": "Manufacturer / Brand",
        "rec_specs_sec": "#### 📱 Device Specs",
        "age_lbl": "Device Age (Years)",
        "ram_lbl": "RAM",
        "stor_lbl": "Storage",
        "stor_opts_pc": ["HDD", "SATA SSD", "NVMe M.2 SSD"],
        "cap_lbl_mob": "Storage Capacity",
        "cap_opts_mob": ["64 GB", "128 GB", "256 GB", "512 GB", "1 TB"],
        "os_lbl_mob": "Operating System",
        "os_opts_mob": ["iOS / iPadOS", "Android", "HarmonyOS", "Windows"],
        "priority": "Priority",
        "priorities": ["Normal", "Medium", "Urgent"],
        "rec_date": "Reception Date",
        "init_note": "Reported device issue at reception:",
        "init_note_ph": "Example: Cracked screen, fast battery drain, or slow performance...",
        "go_maint": "Send ticket with the same ID to Maintenance after saving",
        "assign_tech_lbl": "Assign technician when routing to Maintenance:",
        "custom_tech_lbl": "Enter technician name:",
        "save_rec_btn": "📥 Save Ticket & Issue Tracking Receipt",
        "default_rec_note": "Registered at reception pending maintenance.",
        "saved_rec_msg": "✅ Ticket `{tid}` saved and tracking receipt generated.",
        "show_track_card_btn": "🧾 Show Tracking Receipt",
        "hide_track_card_btn": "✖️ Hide Tracking Receipt",
        "reg_tickets": "📋 Registered Tickets & Device Tracking",
        "track_search": "Quick search by Ticket ID, Customer, or Mobile:",
        "track_pick": "Select a ticket to view its tracking receipt and history:",
        "timeline_title": "🕒 Device Status Audit Log",
        "no_tickets": "No tickets registered yet.",
        "load_demo": "✨ Load Demo Data",
        "maint_title": "🔧 Maintenance — Technician Work Done",
        "maint_caption": "Displays device details and reported issue, and lets the technician write what work was done.",
        "no_maint_tickets": "📭 No tickets assigned to Maintenance right now.",
        "go_rec_btn": "🛎️ Go to Reception",
        "pick_ticket_maint": "Select Maintenance ticket / device:",
        "fixed_tid": "**Ticket ID:** `{tid}` | **Current Stage:** `{stage}` | **Technician:** `{tech}`",
        "cust_info_line": "**Customer:** {cust} | **Receptionist:** {staff} | **Mobile:** {phone}",
        "dev_info_line": "**Device Info:** {dtype} — {brand} (`{sn}`)",
        "specs_info_line": "**Device Specs:** {specs}",
        "cust_issue_box": "**📝 Reported Device Issue:** {issue}",
        "repaired_box": "**✍️ Technician Work Done:** {rep}",
        "prev_notes": "**Previous Technician Notes:** {notes}",
        "repair_write_sec": "#### 1️⃣ Write Technician Work Done",
        "repaired_lbl": "Write what the technician did on the device:",
        "repaired_ph": "Example: Replaced display assembly, cleaned thermal paste & fan, and verified boot...",
        "repaired_empty_msg": "No technician work logged yet",
        "cost_sec": "#### 2️⃣ Cost & Technician Notes",
        "decision_lbl": "Final Action / Diagnosis",
        "decision_opts": [
            "Part Replacement / Repair",
            "OS & Software Fix",
            "Preventive Maintenance & Cleaning",
            "Device Replacement Recommended",
        ],
        "est_cost_lbl": "Repair Cost (SAR)",
        "tech_lbl": "Technician Name",
        "tech_notes_lbl": "Additional Technician Notes:",
        "send_bill": "Send ticket with the same ID to Billing after saving",
        "save_diag_btn": "🛠️ Save Technician Work & Forward",
        "saved_diag_msg": "✅ Technician work saved for ticket `{tid}`.",
        "bill_title": "💳 Billing — Payment Confirmation & Print Invoice",
        "bill_caption": "Confirms payment and shows the invoice using the new unified card when clicking Print Invoice.",
        "no_bill_tickets": "📭 No invoices transferred to Billing right now.",
        "m_in_bill": "Billing Invoices",
        "m_paid": "Paid Invoices",
        "m_unpaid": "Unpaid Invoices",
        "filter_pay_lbl": "Filter Billing Invoices by Payment:",
        "pay_filter_opts": ["All", "Unpaid", "Paid"],
        "bill_table_title": "#### 📄 Billing Invoices",
        "no_matching_bills": "No Billing invoices match the selected payment status.",
        "bill_mgmt": "#### 🧾 Payment Confirmation & Invoice Print",
        "pick_ticket_bill": "Select Billing invoice:",
        "final_cost": "Invoice Amount (SAR)",
        "pay_status": "Payment Status",
        "pay_opts": ["Unpaid", "Paid"],
        "pay_method_lbl": "Payment Method",
        "move_stage": "Keep in Billing or return to Maintenance:",
        "bill_stage_choices": ["Billing", "Maintenance"],
        "save_bill_btn": "💾 Save Payment Status",
        "print_btn": "🖨️ Print Invoice",
        "hide_print_btn": "✖️ Hide Invoice",
        "mgr_title": "🔐 Manager — Full Permissions & Complete Management",
        "mgr_warn": "Restricted to Manager access. Recruiters can view the demo PIN under the «About» tab.",
        "pin_lbl": "Enter Manager Access PIN:",
        "pin_ph": "Example: MGR-2026",
        "unlock_btn": "🔓 Unlock Manager View",
        "pin_ok": "✅ PIN verified and all permissions enabled.",
        "pin_err": "❌ Invalid PIN. Check «About» for the demo access PIN.",
        "lock_btn": "🔒 Lock / Exit Manager View",
        "mgr_caption": "Full permissions: Unified invoice, edit, routing, create ticket, search & filter, and delete.",
        "m_total": "Total Tickets",
        "m_urgent": "Urgent Tickets",
        "m_work": "Maintenance / Billing",
        "m_paid_mgr": "Paid",
        "rep_sn": "🔁 **Repeated Devices:** ",
        "rep_times": "times",
        "chart_stage": "#### 📈 Tickets by Stage",
        "chart_dec": "#### 📈 Tickets by Decision",
        "mgr_all_inv_sec": "#### 🧾 Single Manager Invoice for All Customers",
        "mgr_all_inv_show": "🧾 Show All Customers Invoice",
        "mgr_all_inv_hide": "✖️ Hide All Customers Invoice",
        "mgr_add_sec": "#### ➕ Create New Ticket & Route to Any Department",
        "mgr_target_stage": "Initial Department",
        "mgr_decision_lbl": "Decision / Diagnosis",
        "mgr_cost_lbl": "Amount / Cost",
        "mgr_create_btn": "➕ Create Ticket in System",
        "mgr_created_msg": "✅ Created ticket `{tid}` in `{stage}`.",
        "mgr_edit_sec": "#### 🛠️ Full Edit & Routing Control for Any Ticket",
        "mgr_pick_edit": "Select customer / ticket to manage or edit:",
        "mgr_stage_lbl": "Route Ticket to Department",
        "mgr_specs_lbl": "Device Specs",
        "mgr_rep_lbl": "Technician Work Done (Written)",
        "mgr_notes_lbl": "Notes & Technical Report",
        "mgr_save_edit_btn": "💾 Save All Ticket Changes",
        "mgr_saved_edit_msg": "✅ Saved all updates for ticket `{tid}` and routed to `{stage}`.",
        "mgr_preview_type": "Invoice Type for Management Preview / Print:",
        "mgr_preview_opts": ["Service & Payment Invoice", "Tracking Receipt (No Billing)"],
        "mgr_show_card_btn": "🧾 Show Ticket Invoice in New Layout",
        "mgr_hide_card_btn": "✖️ Hide Ticket Invoice",
        "search_lbl": "🔎 Search by Ticket ID, Customer, Receptionist, Mobile, or S/N",
        "filt_dept": "Filter by Stage",
        "filt_pay": "Filter by Payment",
        "all_opt": "All",
        "pick_del": "Select ticket to delete:",
        "del_btn": "🗑️ Delete Selected Ticket",
        "del_msg": "Deleted ticket `{tid}`.",
        "add_demo": "✨ Add Demo Data",
        "clear_all": "🗑️ Clear All Tickets",
        "about_title": "📌 About This App",
        "about_desc": (
            "A bilingual helpdesk & maintenance web app for smartphones, tablets, laptops, and desktops "
            "with a single Ticket ID, unified card layout, and a single invoice for all customers in Manager."
        ),
        "mgr_creds_title": "#### 🔑 Manager Access Credentials (For Recruiters & Reviewers)",
        "mgr_pin_line": "**Manager Access PIN:** `{pin}`",
        "mgr_pin_hint": "Switch to the «Manager» tab and enter the PIN above to test full management and the all-customers invoice.",
        "feats_title": "#### ✨ Key Features:",
        "feats": [
            "- **Full Management Permissions:** Edit, route, create, filter, and delete tickets in one place.",
            "- **Single All-Customers Invoice in Manager:** Combines all customers into one printable invoice.",
            "- **Status Audit Log:** Tracks stage transitions across Reception, Maintenance, and Billing for technical reviewers.",
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

if "mgr_last_picked_tid" not in st.session_state:
    st.session_state.mgr_last_picked_tid = None

if "manager_unlocked" not in st.session_state:
    st.session_state.manager_unlocked = False

if "show_invoice_panel" not in st.session_state:
    st.session_state.show_invoice_panel = False

if "show_tracking_card" not in st.session_state:
    st.session_state.show_tracking_card = False

if "show_mgr_card" not in st.session_state:
    st.session_state.show_mgr_card = False

if "show_mgr_all_invoice" not in st.session_state:
    st.session_state.show_mgr_all_invoice = False

st.set_page_config(
    page_title=TEXTS[st.session_state.lang]["page_title"],
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

top_l, top_r = st.columns([3, 2])
with top_r:
    lang_choice = st.radio(
        "اللغة / Language",
        ["العربية", "English"],
        index=0 if st.session_state.lang == "ar" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
st.session_state.lang = "ar" if lang_choice == "العربية" else "en"
t = TEXTS[st.session_state.lang]

border_prop = "border-right: 5px solid #22d3ee;" if t["dir"] == "rtl" else "border-left: 5px solid #22d3ee;"

st.markdown(
    f"""
    <style>
    .stApp {{
        direction: {t["dir"]};
        text-align: {t["align"]};
        background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
        color: #0f294a;
    }}
    .block-container {{
        max-width: 820px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }}
    .app-banner {{
        background: linear-gradient(135deg, #0f294a 0%, #164e63 100%);
        color: #ffffff;
        padding: 20px 22px;
        border-radius: 16px;
        margin-bottom: 14px;
        box-shadow: 0 6px 18px rgba(15, 41, 74, 0.16);
        {border_prop}
    }}
    .app-banner h2 {{
        margin: 0 0 6px 0;
        color: #ffffff !important;
        font-size: 22px;
        font-weight: 700;
    }}
    .app-banner p {{
        margin: 0;
        color: #cffafe;
        font-size: 13.5px;
    }}
    .nav-card {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(15, 41, 74, 0.05);
    }}
    .active-strip {{
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 14px;
        font-size: 13.5px;
        color: #1e3a8a;
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
        min-height: 44px;
        font-size: 14.5px;
        border-radius: 10px;
        background-color: #ffffff;
        color: #0f294a;
        border: 1px solid #cbd5e1;
        transition: all 0.15s ease;
    }}
    .stButton > button:hover {{
        border-color: #0284c7;
        background-color: #f8fafc;
    }}
    div[data-testid="stMetric"] {{
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: 0 2px 6px rgba(15, 41, 74, 0.05);
    }}
    div[data-testid="stMetricValue"] {{
        font-size: 19px;
        font-weight: 700;
        color: #0f294a;
    }}
    div[data-testid="stMetricLabel"] {{
        color: #475569;
        font-size: 12.5px;
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

with st.container():
    st.markdown('<div class="nav-card">', unsafe_allow_html=True)
    selected_dept_label = st.radio(
        t["nav_label"],
        t["depts"],
        index=st.session_state.active_dept_idx,
        horizontal=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

dept_idx = t["depts"].index(selected_dept_label)
st.session_state.active_dept_idx = dept_idx

df_all = pd.read_sql_query("SELECT * FROM tickets", conn)
if not df_all.empty:
    df_all["stage_code"] = df_all["stage"].map(normalize_stage)
    df_all["pay_code"] = df_all["payment_status"].map(normalize_payment)
    df_all["stage_disp"] = df_all["stage_code"].map(t["stage_lbl"])
    df_all["pay_disp"] = df_all["pay_code"].map(t["pay_lbl"])

if st.session_state.current_ticket_id and not df_all.empty:
    match_cur = df_all[df_all["ticket_id"] == st.session_state.current_ticket_id]
    if not match_cur.empty:
        cur_row = match_cur.iloc[0]
        st.markdown(
            f"""
            <div class="active-strip">
                {t["active_ticket_bar"].format(
                    tid=html.escape(str(cur_row.get("ticket_id", "-"))),
                    cust=html.escape(str(cur_row.get("customer_name", "-"))),
                    dev=html.escape(f"{cur_row.get('device_type', '-')} - {cur_row.get('brand', '-')}"),
                    stage=html.escape(str(cur_row.get("stage_disp", "-"))),
                    pay=html.escape(str(cur_row.get("pay_disp", "-"))),
                )}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==========================================
# 0. الاستقبال / Reception
# ==========================================
if dept_idx == 0:
    st.subheader(t["rec_title"])
    st.caption(t["rec_caption"])

    active_new_id = st.session_state.draft_ticket_id
    st.success(t["new_tid_msg"].format(tid=active_new_id))

    with st.container(border=True):
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

        st.markdown(t["rec_specs_sec"])
        mobile_mode = is_mobile_or_tablet(device_type)
        device_age = st.slider(t["age_lbl"], 0, 15, 2)
        c_r, c_s = st.columns(2)
        if mobile_mode:
            with c_r:
                spec_a = st.selectbox(t["cap_lbl_mob"], t["cap_opts_mob"], index=2)
            with c_s:
                spec_b = st.selectbox(t["os_lbl_mob"], t["os_opts_mob"])
        else:
            with c_r:
                spec_a = st.selectbox(t["ram_lbl"], ["4 GB", "8 GB", "16 GB", "32 GB", "64 GB"], index=1)
            with c_s:
                spec_b = st.selectbox(t["stor_lbl"], t["stor_opts_pc"])

        c_pr, c_dt = st.columns(2)
        with c_pr:
            priority_level = st.selectbox(t["priority"], t["priorities"])
        with c_dt:
            ticket_date = st.date_input(t["rec_date"], datetime.now())

        initial_note = st.text_area(t["init_note"], placeholder=t["init_note_ph"])
        go_to_maint = st.checkbox(t["go_maint"], value=True)

        assigned_tech = "فهد المطيري"
        if go_to_maint:
            tech_choice = st.selectbox(t["assign_tech_lbl"], TECH_OPTIONS)
            if tech_choice == "فني آخر (اكتب الاسم)":
                assigned_tech = st.text_input(t["custom_tech_lbl"], value="فهد المطيري").strip() or "فهد المطيري"
            else:
                assigned_tech = tech_choice

        if st.button(t["save_rec_btn"], type="primary"):
            next_stage = "Maintenance" if go_to_maint else "Reception"
            issue_val = initial_note.strip() if initial_note.strip() else t["default_rec_note"]
            age_unit = "سنوات" if st.session_state.lang == "ar" and device_age != 1 else ("سنة" if st.session_state.lang == "ar" else "yrs")
            specs_val = f"{spec_a} | {spec_b} | {device_age} {age_unit}"
            init_hist = append_history(
                "[]",
                t["depts"][0],
                f"تم فتح التذكرة وإصدار فاتورة متابعة -> {t['stage_lbl'][next_stage]} (الفني: {assigned_tech})"
            )

            cursor.execute("""
                INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                active_new_id,
                customer_name.strip(),
                reception_staff.strip(),
                customer_phone.strip(),
                device_sn,
                device_type,
                brand,
                specs_val,
                issue_val,
                t["repaired_empty_msg"],
                "",
                priority_level,
                "Pending",
                next_stage,
                "Unpaid",
                "لم يُحدد بعد",
                str(ticket_date),
                assigned_tech,
                "0 SAR",
                init_hist,
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
        q_track = st.text_input(t["track_search"], key="track_q")
        track_df = df_all.copy()
        if q_track.strip():
            m = (
                track_df["ticket_id"].str.contains(q_track.strip(), case=False, na=False)
                | track_df["customer_name"].str.contains(q_track.strip(), case=False, na=False)
                | track_df["customer_phone"].str.contains(q_track.strip(), case=False, na=False)
            )
            track_df = track_df[m]

        if not track_df.empty:
            if st.session_state.lang == "ar":
                disp_df = track_df.rename(columns={
                    "ticket_id": "رقم التذكرة",
                    "customer_name": "اسم العميل",
                    "device_type": "نوع الجهاز",
                    "device_specs": "مواصفات الجهاز",
                    "customer_issue": "مشكلة الجهاز",
                    "stage_disp": "القسم الحالي",
                })
                st.dataframe(
                    disp_df[["رقم التذكرة", "اسم العميل", "نوع الجهاز", "مواصفات الجهاز", "مشكلة الجهاز", "القسم الحالي"]],
                    use_container_width=True,
                )
            else:
                disp_df = track_df.rename(columns={
                    "ticket_id": "Ticket ID",
                    "customer_name": "Customer",
                    "device_type": "Device",
                    "device_specs": "Device Specs",
                    "customer_issue": "Reported Issue",
                    "stage_disp": "Stage",
                })
                st.dataframe(
                    disp_df[["Ticket ID", "Customer", "Device", "Device Specs", "Reported Issue", "Stage"]],
                    use_container_width=True,
                )

            rec_ids = track_df["ticket_id"].tolist()
            rec_def = 0
            if st.session_state.current_ticket_id in rec_ids:
                rec_def = rec_ids.index(st.session_state.current_ticket_id)
            picked_rec_id = st.selectbox(t["track_pick"], rec_ids, index=rec_def)
            r_row = track_df[track_df["ticket_id"] == picked_rec_id].iloc[0].to_dict()
            r_row["stage_disp"] = track_df[track_df["ticket_id"] == picked_rec_id].iloc[0]["stage_disp"]

            tc1, tc2 = st.columns(2)
            with tc1:
                if st.button(t["show_track_card_btn"], type="primary", key="rec_show_card"):
                    st.session_state.show_tracking_card = True
                    st.rerun()
            with tc2:
                if st.session_state.show_tracking_card and st.button(t["hide_track_card_btn"], key="rec_hide_card"):
                    st.session_state.show_tracking_card = False
                    st.rerun()

            if st.session_state.show_tracking_card:
                render_unified_document_card(
                    r_row,
                    r_row["stage_disp"],
                    is_rtl=(st.session_state.lang == "ar"),
                    mode="tracking",
                )

            with st.container(border=True):
                st.markdown(f"**{t['timeline_title']}**")
                for h_item in parse_history(r_row.get("status_history", "[]")):
                    st.caption(f"• {h_item}")

# ==========================================
# 1. الصيانة / Maintenance
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
            return f"{r['ticket_id']} | {r['customer_name']} — {r['device_type']} ({r['brand']})"

        chosen_id = st.selectbox(t["pick_ticket_maint"], ticket_ids, index=default_idx, format_func=fmt_maint)
        st.session_state.current_ticket_id = chosen_id
        row = maint_df[maint_df["ticket_id"] == chosen_id].iloc[0]

        with st.container(border=True):
            st.write(
                t["fixed_tid"].format(
                    tid=row.get("ticket_id", "-"),
                    stage=row.get("stage_disp", "-"),
                    tech=row.get("technician_name", "فهد المطيري"),
                )
            )
            st.write(
                t["cust_info_line"].format(
                    cust=row.get("customer_name", "-"),
                    staff=row.get("reception_staff", "-"),
                    phone=row.get("customer_phone", "-"),
                )
            )
            st.write(
                t["dev_info_line"].format(
                    dtype=row.get("device_type", "-"),
                    brand=row.get("brand", "-"),
                    sn=row.get("device_sn", "-"),
                )
            )
            st.write(t["specs_info_line"].format(specs=row.get("device_specs", "-")))
            st.warning(t["cust_issue_box"].format(issue=row.get("customer_issue", "-")))
            st.success(t["repaired_box"].format(rep=row.get("repaired_text", "-")))
            if row.get("tech_notes"):
                st.info(t["prev_notes"].format(notes=row.get("tech_notes", "")))

        with st.container(border=True):
            st.markdown(t["repair_write_sec"])
            cur_rep = str(row.get("repaired_text", ""))
            default_rep_val = "" if cur_rep in ["لم يُسجل عمل الفني بعد", "No technician work logged yet"] else cur_rep
            repaired_input = st.text_area(t["repaired_lbl"], value=default_rep_val, placeholder=t["repaired_ph"], key=f"m_rep_{chosen_id}")

            st.markdown(t["cost_sec"])
            dec_idx = 0
            if row.get("decision") in t["decision_opts"]:
                dec_idx = t["decision_opts"].index(row.get("decision"))
            decision_val = st.selectbox(t["decision_lbl"], t["decision_opts"], index=dec_idx, key=f"m_dec_{chosen_id}")

            cur_cost = str(row.get("cost_est", ""))
            default_cost_val = "150 SAR" if (not cur_cost or cur_cost == "0 SAR") else cur_cost
            est_cost_input = st.text_input(t["est_cost_lbl"], value=default_cost_val, key=f"m_cost_{chosen_id}")
            tech_person = st.text_input(t["tech_lbl"], value=str(row.get("technician_name") or "فهد المطيري"), key=f"m_tech_{chosen_id}")
            tech_notes = st.text_area(t["tech_notes_lbl"], value=str(row.get("tech_notes") or ""), key=f"m_notes_{chosen_id}")
            send_to_billing = st.checkbox(t["send_bill"], value=True, key=f"m_bill_{chosen_id}")

            if st.button(t["save_diag_btn"], type="primary", key=f"m_save_{chosen_id}"):
                rep_final = repaired_input.strip() if repaired_input.strip() else t["repaired_empty_msg"]
                new_stage = "Billing" if send_to_billing else "Maintenance"
                upd_hist = append_history(
                    row.get("status_history", "[]"),
                    t["depts"][1],
                    f"الفني ({tech_person.strip()}): {rep_final[:45]} -> {t['stage_lbl'][new_stage]}"
                )

                cursor.execute("""
                    UPDATE tickets
                    SET repaired_text = ?, tech_notes = ?, decision = ?,
                        stage = ?, technician_name = ?, cost_est = ?, status_history = ?
                    WHERE ticket_id = ?
                """, (
                    rep_final,
                    tech_notes.strip(),
                    decision_val,
                    new_stage,
                    tech_person.strip(),
                    est_cost_input.strip(),
                    upd_hist,
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

    billing_pool = df_all[df_all["stage_code"] == "Billing"].copy() if not df_all.empty else pd.DataFrame()

    if billing_pool.empty:
        st.info(t["no_bill_tickets"])
        if df_all.empty and st.button(t["load_demo"], type="primary"):
            load_demo_data()
            st.rerun()
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric(t["m_in_bill"], len(billing_pool))
        m2.metric(t["m_paid"], len(billing_pool[billing_pool["pay_code"] == "Paid"]))
        m3.metric(t["m_unpaid"], len(billing_pool[billing_pool["pay_code"] == "Unpaid"]))

        pay_filter_sel = st.selectbox(t["filter_pay_lbl"], t["pay_filter_opts"])

        filtered_bill = billing_pool.copy()
        if pay_filter_sel == t["pay_filter_opts"][1]:
            filtered_bill = filtered_bill[filtered_bill["pay_code"] == "Unpaid"]
        elif pay_filter_sel == t["pay_filter_opts"][2]:
            filtered_bill = filtered_bill[filtered_bill["pay_code"] == "Paid"]

        st.markdown(t["bill_table_title"])
        if filtered_bill.empty:
            st.info(t["no_matching_bills"])
        else:
            if st.session_state.lang == "ar":
                disp_bill = filtered_bill.rename(columns={
                    "ticket_id": "رقم التذكرة",
                    "customer_name": "اسم العميل",
                    "customer_issue": "مشكلة الجهاز",
                    "repaired_text": "ما عمله الفني",
                    "cost_est": "المبلغ",
                    "pay_disp": "حالة الدفع",
                    "payment_method": "طريقة الدفع",
                })
                st.dataframe(
                    disp_bill[["رقم التذكرة", "اسم العميل", "مشكلة الجهاز", "ما عمله الفني", "المبلغ", "حالة الدفع", "طريقة الدفع"]],
                    use_container_width=True,
                )
            else:
                disp_bill = filtered_bill.rename(columns={
                    "ticket_id": "Ticket ID",
                    "customer_name": "Customer",
                    "customer_issue": "Reported Issue",
                    "repaired_text": "Technician Work",
                    "cost_est": "Amount",
                    "pay_disp": "Payment",
                    "payment_method": "Method",
                })
                st.dataframe(
                    disp_bill[["Ticket ID", "Customer", "Reported Issue", "Technician Work", "Amount", "Payment", "Method"]],
                    use_container_width=True,
                )

        bill_ids = billing_pool["ticket_id"].tolist()
        bill_default = 0
        if st.session_state.current_ticket_id in bill_ids:
            bill_default = bill_ids.index(st.session_state.current_ticket_id)

        st.markdown(t["bill_mgmt"])

        def fmt_bill(tid):
            r = billing_pool[billing_pool["ticket_id"] == tid].iloc[0]
            return f"{r['ticket_id']} | {r['customer_name']} ({r['pay_disp']})"

        with st.container(border=True):
            bill_id = st.selectbox(t["pick_ticket_bill"], bill_ids, index=bill_default, format_func=fmt_bill)
            st.session_state.current_ticket_id = bill_id
            brow = billing_pool[billing_pool["ticket_id"] == bill_id].iloc[0]

            c_cost, c_pay, c_meth = st.columns(3)
            with c_cost:
                new_cost = st.text_input(t["final_cost"], value=str(brow.get("cost_est") or "0 SAR"), key=f"b_cost_{bill_id}")
            with c_pay:
                pay_default_idx = 1 if brow.get("pay_code") == "Paid" else 0
                new_pay_lbl = st.selectbox(t["pay_status"], t["pay_opts"], index=pay_default_idx, key=f"b_pay_{bill_id}")
                new_pay_db = "Paid" if new_pay_lbl == t["pay_opts"][1] else "Unpaid"
            with c_meth:
                meth_idx = 0
                if brow.get("payment_method") in t["pay_methods"]:
                    meth_idx = t["pay_methods"].index(brow.get("payment_method"))
                new_method = st.selectbox(t["pay_method_lbl"], t["pay_methods"], index=meth_idx, key=f"b_meth_{bill_id}")

            move_stage_lbl = st.selectbox(t["move_stage"], t["bill_stage_choices"], index=0, key=f"b_stg_{bill_id}")
            stage_to_db = "Billing" if move_stage_lbl == t["bill_stage_choices"][0] else "Maintenance"

            if st.button(t["save_bill_btn"], type="primary", key=f"b_save_{bill_id}"):
                pay_hist = append_history(
                    brow.get("status_history", "[]"),
                    t["depts"][2],
                    f"حالة الدفع: {new_pay_lbl} ({new_method}) — المبلغ: {new_cost.strip()}"
                )
                cursor.execute("""
                    UPDATE tickets
                    SET cost_est = ?, payment_status = ?, payment_method = ?, stage = ?, status_history = ?
                    WHERE ticket_id = ?
                """, (new_cost.strip(), new_pay_db, new_method, stage_to_db, pay_hist, bill_id))
                conn.commit()
                st.session_state.current_ticket_id = bill_id
                if stage_to_db == "Maintenance":
                    st.session_state.active_dept_idx = 1
                st.rerun()

            b_act1, b_act2 = st.columns(2)
            with b_act1:
                if st.button(t["print_btn"], key="bill_show_card"):
                    st.session_state.show_invoice_panel = True
                    st.rerun()
            with b_act2:
                if st.session_state.show_invoice_panel and st.button(t["hide_print_btn"], key="bill_hide_card"):
                    st.session_state.show_invoice_panel = False
                    st.rerun()

        if st.session_state.show_invoice_panel:
            render_unified_document_card(
                brow.to_dict(),
                move_stage_lbl,
                is_rtl=(st.session_state.lang == "ar"),
                mode="billing",
                pay_label=new_pay_lbl,
                method_label=new_method,
                final_amount=new_cost.strip(),
                is_paid=(new_pay_db == "Paid"),
            )

# ==========================================
# 3. المدير / Manager
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
            m3.metric(t["m_work"], len(df_all[df_all["stage_code"].isin(["Maintenance", "Billing"])]))
            m4.metric(t["m_paid_mgr"], len(df_all[df_all["pay_code"] == "Paid"]))

            repeated_sn = df_all["device_sn"].value_counts()
            repeated_sn = repeated_sn[repeated_sn > 1]
            if not repeated_sn.empty:
                items_txt = ", ".join([f"{sn} ({cnt} {t['rep_times']})" for sn, cnt in repeated_sn.items()])
                st.warning(t["rep_sn"] + items_txt)

            c_ch1, c_ch2 = st.columns(2)
            with c_ch1:
                st.markdown(t["chart_stage"])
                st.bar_chart(df_all["stage_disp"].value_counts())
            with c_ch2:
                st.markdown(t["chart_dec"])
                st.bar_chart(df_all["decision"].value_counts())

            st.markdown("---")
            st.markdown(t["mgr_all_inv_sec"])
            with st.container(border=True):
                ac_b1, ac_b2 = st.columns(2)
                with ac_b1:
                    if st.button(t["mgr_all_inv_show"], type="primary", key="mgr_show_all_inv_btn"):
                        st.session_state.show_mgr_all_invoice = True
                        st.rerun()
                with ac_b2:
                    if st.session_state.show_mgr_all_invoice and st.button(t["mgr_all_inv_hide"], key="mgr_hide_all_inv_btn"):
                        st.session_state.show_mgr_all_invoice = False
                        st.rerun()

                if st.session_state.show_mgr_all_invoice:
                    render_all_customers_single_invoice(df_all, is_rtl=(st.session_state.lang == "ar"))

            st.markdown("---")
            st.markdown(t["mgr_edit_sec"])

            mgr_all_ids = df_all["ticket_id"].tolist()
            mgr_def_idx = 0
            if st.session_state.current_ticket_id in mgr_all_ids:
                mgr_def_idx = mgr_all_ids.index(st.session_state.current_ticket_id)

            def fmt_mgr_ticket(tid):
                r = df_all[df_all["ticket_id"] == tid].iloc[0]
                return f"{r['customer_name']} | {r['ticket_id']} — {r['stage_disp']} ({r['pay_disp']})"

            with st.container(border=True):
                edit_tid = st.selectbox(
                    t["mgr_pick_edit"],
                    mgr_all_ids,
                    index=mgr_def_idx,
                    format_func=fmt_mgr_ticket,
                    key="mgr_edit_selector",
                )

                if st.session_state.mgr_last_picked_tid != edit_tid:
                    st.session_state.mgr_last_picked_tid = edit_tid
                    st.session_state.current_ticket_id = edit_tid
                    st.session_state.show_mgr_card = False

                erow = df_all[df_all["ticket_id"] == edit_tid].iloc[0].to_dict()
                ek = edit_tid

                ec1, ec2 = st.columns(2)
                with ec1:
                    ed_cust = st.text_input(t["cust_name"], value=str(erow.get("customer_name") or ""), key=f"ed_cust_{ek}")
                    ed_phone = st.text_input(t["mobile"], value=str(erow.get("customer_phone") or ""), key=f"ed_phone_{ek}")
                    ed_sn = st.text_input(t["sn"], value=str(erow.get("device_sn") or ""), key=f"ed_sn_{ek}")
                with ec2:
                    ed_staff = st.text_input(t["rec_staff"], value=str(erow.get("reception_staff") or ""), key=f"ed_staff_{ek}")
                    ed_tech = st.text_input(t["tech_lbl"], value=str(erow.get("technician_name") or "فهد المطيري"), key=f"ed_tech_{ek}")
                    ed_prio = st.text_input(t["priority"], value=str(erow.get("priority") or "متوسطة"), key=f"ed_prio_{ek}")

                ec3, ec4, ec5 = st.columns(3)
                with ec3:
                    stage_idx_now = {"Reception": 0, "Maintenance": 1, "Billing": 2}.get(erow.get("stage_code", "Reception"), 0)
                    ed_stage_lbl = st.selectbox(t["mgr_stage_lbl"], t["stage_opts"], index=stage_idx_now, key=f"ed_stage_{ek}")
                    ed_stage_db = {
                        "الاستقبال": "Reception", "الصيانة": "Maintenance", "الحساب": "Billing",
                        "Reception": "Reception", "Maintenance": "Maintenance", "Billing": "Billing"
                    }[ed_stage_lbl]
                with ec4:
                    ed_cost = st.text_input(t["mgr_cost_lbl"], value=str(erow.get("cost_est") or "0 SAR"), key=f"ed_cost_{ek}")
                with ec5:
                    pay_idx_now = 1 if erow.get("pay_code") == "Paid" else 0
                    ed_pay_lbl = st.selectbox(t["pay_status"], t["pay_opts"], index=pay_idx_now, key=f"ed_pay_{ek}")
                    ed_pay_db = "Paid" if ed_pay_lbl == t["pay_opts"][1] else "Unpaid"

                ed_specs = st.text_input(t["mgr_specs_lbl"], value=str(erow.get("device_specs") or ""), key=f"ed_specs_{ek}")
                ed_issue = st.text_input(t["init_note"], value=str(erow.get("customer_issue") or ""), key=f"ed_issue_{ek}")
                ed_rep = st.text_input(t["mgr_rep_lbl"], value=str(erow.get("repaired_text") or ""), key=f"ed_rep_{ek}")
                ed_dec = st.text_input(t["mgr_decision_lbl"], value=str(erow.get("decision") or ""), key=f"ed_dec_{ek}")
                ed_notes = st.text_area(t["mgr_notes_lbl"], value=str(erow.get("tech_notes") or ""), key=f"ed_notes_{ek}")

                if st.button(t["mgr_save_edit_btn"], type="primary", key=f"mgr_save_edit_submit_{ek}"):
                    mgr_hist = append_history(
                        erow.get("status_history", "[]"),
                        t["depts"][3],
                        f"تعديل إداري -> القسم: {ed_stage_lbl} | الفني: {ed_tech.strip()} | الدفع: {ed_pay_lbl}"
                    )
                    cursor.execute("""
                        UPDATE tickets
                        SET customer_name = ?, reception_staff = ?, customer_phone = ?,
                            device_sn = ?, device_specs = ?, customer_issue = ?,
                            repaired_text = ?, priority = ?, decision = ?, stage = ?,
                            payment_status = ?, technician_name = ?, cost_est = ?,
                            tech_notes = ?, status_history = ?
                        WHERE ticket_id = ?
                    """, (
                        ed_cust.strip(),
                        ed_staff.strip(),
                        ed_phone.strip(),
                        ed_sn.strip(),
                        ed_specs.strip(),
                        ed_issue.strip(),
                        ed_rep.strip(),
                        ed_prio.strip(),
                        ed_dec.strip(),
                        ed_stage_db,
                        ed_pay_db,
                        ed_tech.strip(),
                        ed_cost.strip(),
                        ed_notes.strip(),
                        mgr_hist,
                        edit_tid,
                    ))
                    conn.commit()
                    st.success(t["mgr_saved_edit_msg"].format(tid=edit_tid, stage=ed_stage_lbl))
                    st.rerun()

                mgr_card_mode_lbl = st.selectbox(t["mgr_preview_type"], t["mgr_preview_opts"], key=f"mgr_card_mode_{ek}")
                is_bill_preview = (mgr_card_mode_lbl == t["mgr_preview_opts"][0])

                preview_row = dict(erow)
                preview_row["customer_name"] = ed_cust.strip()
                preview_row["customer_phone"] = ed_phone.strip()
                preview_row["reception_staff"] = ed_staff.strip()
                preview_row["technician_name"] = ed_tech.strip()
                preview_row["device_sn"] = ed_sn.strip()
                preview_row["device_specs"] = ed_specs.strip()
                preview_row["customer_issue"] = ed_issue.strip()
                preview_row["repaired_text"] = ed_rep.strip()
                preview_row["priority"] = ed_prio.strip()

                mc1, mc2 = st.columns(2)
                with mc1:
                    if st.button(t["mgr_show_card_btn"], key=f"mgr_show_single_card_btn_{ek}"):
                        st.session_state.show_mgr_card = True
                        st.rerun()
                with mc2:
                    if st.session_state.show_mgr_card and st.button(t["mgr_hide_card_btn"], key=f"mgr_hide_single_card_btn_{ek}"):
                        st.session_state.show_mgr_card = False
                        st.rerun()

                if st.session_state.show_mgr_card:
                    render_unified_document_card(
                        preview_row,
                        ed_stage_lbl,
                        is_rtl=(st.session_state.lang == "ar"),
                        mode="billing" if is_bill_preview else "tracking",
                        pay_label=ed_pay_lbl,
                        method_label=str(erow.get("payment_method") or "-"),
                        final_amount=ed_cost.strip(),
                        is_paid=(ed_pay_db == "Paid"),
                    )

            st.markdown("---")
            st.markdown(t["mgr_add_sec"])
            with st.container(border=True):
                ac1, ac2 = st.columns(2)
                with ac1:
                    add_cust = st.text_input(t["cust_name"], "عميل جديد", key="add_cust")
                    add_phone = st.text_input(t["mobile"], "0500000000", key="add_phone")
                    add_sn = st.text_input(t["sn"], "SN-900100", key="add_sn")
                with ac2:
                    add_staff = st.text_input(t["rec_staff"], "سالم الدوسري", key="add_staff")
                    add_stage_lbl = st.selectbox(t["mgr_target_stage"], t["stage_opts"], index=1, key="add_stage")
                    add_cost = st.text_input(t["mgr_cost_lbl"], "150 SAR", key="add_cost")

                lang_brands_map = DEVICE_BRANDS[st.session_state.lang]
                add_dtype = st.selectbox(t["dev_type"], list(lang_brands_map.keys()), key="add_dtype")
                add_brand = st.selectbox(t["brand"], lang_brands_map[add_dtype], key="add_brand")
                add_specs = st.text_input(t["mgr_specs_lbl"], "128 GB | Android | 2 yrs", key="add_specs")
                add_issue = st.text_input(t["init_note"], "وصف المشكلة من العميل", key="add_issue")
                add_dec = st.text_input(t["mgr_decision_lbl"], "إصلاح عطل / استبدال قطعة", key="add_dec")

                if st.button(t["mgr_create_btn"], key="mgr_create_submit"):
                    new_mgr_tid = generate_unique_ticket_id()
                    add_stage_db = {
                        "الاستقبال": "Reception", "الصيانة": "Maintenance", "الحساب": "Billing",
                        "Reception": "Reception", "Maintenance": "Maintenance", "Billing": "Billing"
                    }[add_stage_lbl]
                    new_hist = append_history("[]", t["depts"][3], f"إنشاء تذكرة من لوحة المدير في قسم {add_stage_lbl}")
                    cursor.execute("""
                        INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_mgr_tid,
                        add_cust.strip(),
                        add_staff.strip(),
                        add_phone.strip(),
                        add_sn.strip(),
                        add_dtype,
                        add_brand,
                        add_specs.strip(),
                        add_issue.strip(),
                        t["repaired_empty_msg"],
                        "Created from Manager dashboard.",
                        "متوسطة",
                        add_dec.strip(),
                        add_stage_db,
                        "Unpaid",
                        "لم يُحدد بعد",
                        str(datetime.now().date()),
                        "فهد المطيري",
                        add_cost.strip(),
                        new_hist,
                    ))
                    conn.commit()
                    st.session_state.current_ticket_id = new_mgr_tid
                    st.session_state.mgr_last_picked_tid = new_mgr_tid
                    st.success(t["mgr_created_msg"].format(tid=new_mgr_tid, stage=add_stage_lbl))
                    st.rerun()

            st.markdown("---")
            search_q = st.text_input(t["search_lbl"])
            f1, f2 = st.columns(2)
            mgr_stage = f1.selectbox(t["filt_dept"], [t["all_opt"]] + sorted(df_all["stage_disp"].unique().tolist()))
            mgr_pay = f2.selectbox(t["filt_pay"], [t["all_opt"]] + sorted(df_all["pay_disp"].unique().tolist()))

            mgr_df = df_all.copy()
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
                mgr_df = mgr_df[mgr_df["stage_disp"] == mgr_stage]
            if mgr_pay != t["all_opt"]:
                mgr_df = mgr_df[mgr_df["pay_disp"] == mgr_pay]

            st.dataframe(
                mgr_df.drop(columns=["stage_code", "pay_code", "stage_disp", "pay_disp"], errors="ignore"),
                use_container_width=True,
            )

            mgr_labels = [f"{r['ticket_id']} | {r['customer_name']} ({r['device_type']})" for _, r in df_all.iterrows()]
            del_choice = st.selectbox(t["pick_del"], mgr_labels)
            del_id = del_choice.split(" | ")[0].strip()

            if st.button(t["del_btn"], key="mgr_del_btn"):
                cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (del_id,))
                conn.commit()
                st.warning(t["del_msg"].format(tid=del_id))
                st.rerun()

            if st.button(t["add_demo"], key="mgr_add_demo_btn"):
                load_demo_data()
                st.rerun()

            if st.button(t["clear_all"], key="mgr_clear_all_btn"):
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

    with st.container(border=True):
        st.markdown(t["feats_title"])
        for item in t["feats"]:
            st.markdown(item)
