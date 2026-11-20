import streamlit as st
from datetime import datetime
import random
import sqlite3
import pandas as pd

# رمز الدخول الخاص بقسم المدير
MANAGER_PIN = "MGR-2026"

# 1. إعداد قاعدة البيانات المحلية (SQLite)
conn = sqlite3.connect("enterprise_helpdesk_dept_field_v3.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
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
""")
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
        background: linear-gradient(135deg,
