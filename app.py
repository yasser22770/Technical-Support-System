import os
import sqlite3
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_from_directory
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "it_helpdesk_lab_secret_key"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "helpdesk.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"txt", "log", "png", "jpg", "jpeg", "pdf"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

SLA_HOURS = {
    "عاجل (Urgent)": 2,
    "مرتفع (High)": 4,
    "متوسط (Medium)": 24,
    "منخفض (Low)": 72,
}

CATEGORIES = [
    "Hardware - أعطال الأجهزة",
    "Software & OS - البرمجيات والأنظمة",
    "Networking - الشبكات والإنترنت",
    "Access & AD - الصلاحيات والحسابات",
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db():
    conn = get_db()
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
            assignee TEXT DEFAULT 'غير معيّن',
            attachment TEXT,
            created_at TEXT NOT NULL,
            sla_deadline TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            role TEXT NOT NULL,
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id)
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

    # تعبئة بيانات أولية عند تشغيل النظام لأول مرة
    cur.execute("SELECT COUNT(*) FROM kb_articles")
    if cur.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        sample_kb = [
            (
                "حل مشكلة بطء نظام Windows واستهلاك الذاكرة المرتفع",
                "Software & OS - البرمجيات والأنظمة",
                "تأخر استجابة البرامج، بطء فتح القوائم، وارتفاع استهلاك المعالج أو الذاكرة.",
                "1. افتح مدير المهام عبر الضغط على Ctrl + Shift + Esc.\n"
                "2. رتب العمليات حسب استهلاك الذاكرة (Memory) وأغلق التطبيقات غير الضرورية.\n"
                "3. شغّل سكربت التشخيص المرفق مع خيار تنظيف الملفات المؤقتة (--clean).\n"
                "4. أعد تشغيل الجهاز للتحقق من استقرار الأداء.",
                now,
            ),
            (
                "استكشاف أعطال اتصال Wi-Fi وظهور علامة No Internet",
                "Networking - الشبكات والإنترنت",
                "اتصال الجهاز بالشبكة اللاسلكية مع تعذر فتح المواقع أو الأنظمة الداخلية.",
                "1. تأكد من إيقاف وضع الطيران (Airplane Mode) ثم افصل الشبكة وأعد الاتصال.\n"
                "2. افتح موجه الأوامر (CMD) ونفّذ الأمر: ipconfig /release ثم ipconfig /renew.\n"
                "3. نفّذ الأمر ipconfig /flushdns لتحديث ذاكرة أسماء النطاقات.\n"
                "4. إذا استمرت المشكلة، أرفق تقرير diagnostics.py في تذكرة دعم جديدة.",
                now,
            ),
            (
                "فك قفل حساب الموظف في Active Directory وإعادة تعيين كلمة المرور",
                "Access & AD - الصلاحيات والحسابات",
                "ظهور رسالة The referenced account is currently locked out عند تسجيل الدخول.",
                "1. تحقق من هوية الموظف عبر الرقم الوظيفي.\n"
                "2. افتح أداة Active Directory Users and Computers (أو صفحة محاكي AD في النظام).\n"
                "3. ابحث عن اسم المستخدم وأزل علامة التحديد من خيار Unlock account.\n"
                "4. قم بإعادة تعيين كلمة المرور مع تفعيل خيار تغييرها عند أول تسجيل دخول.",
                now,
            ),
            (
                "إصلاح توقف الطابعة الشبكية وتعليق المستندات في قائمة الانتظار",
                "Hardware - أعطال الأجهزة",
                "بقاء المستندات في حالة Printing أو Error وعدم خروج الورق من الطابعة.",
                "1. افتح نافذة الخدمات (services.msc) وابحث عن خدمة Print Spooler.\n"
                "2. أوقف الخدمة مؤقتاً (Stop).\n"
                "3. امسح الملفات العالقة داخل المسار C:\\Windows\\System32\\spool\\PRINTERS.\n"
                "4. أعد تشغيل خدمة Print Spooler (Start) وأرسل صفحة اختبار.",
                now,
            ),
        ]
        cur.executemany(
            "INSERT INTO kb_articles (title, category, symptoms, steps, created_at) VALUES (?, ?, ?, ?, ?)",
            sample_kb,
        )

    cur.execute("SELECT COUNT(*) FROM ad_users")
    if cur.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        sample_users = [
            ("sara.ali", "سارة علي", "الموارد البشرية", "نشط", 1, f"تم قفل الحساب بسبب محاولات خاطئة ({now})"),
            ("ahmed.hassan", "أحمد حسن", "المالية", "نشط", 0, f"إنشاء الحساب وتعيين المجلد المشترك ({now})"),
            ("it.agent", "خالد المنصور", "تقنية المعلومات", "نشط", 0, f"صلاحيات Domain Admin ({now})"),
            ("omar.trainee", "عمر سامي", "المبيعات", "معطّل", 0, f"إيقاف مؤقت لحين استلام العهدة ({now})"),
        ]
        cur.executemany(
            "INSERT INTO ad_users (username, full_name, department, status, locked, last_action) VALUES (?, ?, ?, ?, ?, ?)",
            sample_users,
        )

    cur.execute("SELECT COUNT(*) FROM tickets")
    if cur.fetchone()[0] == 0:
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M")
        sample_tickets = [
            (
                "قفل حساب الموظفة سارة علي وعدم القدرة على الدخول للنظام",
                "تظهر رسالة Account Locked Out على جهاز WIN10-HR02 منذ الصباح.",
                "Access & AD - الصلاحيات والحسابات",
                "مرتفع (High)",
                "قيد المعالجة",
                "سارة علي (sara.ali)",
                "خالد المنصور (it.agent)",
                None,
                now_str,
                (now_dt + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M"),
            ),
            (
                "انقطاع الاتصال بالشبكة الداخلية في قسم المالية",
                "الأجهزة تحصل على عنوان IP يبدأ بـ 169.254 ولا تصل إلى خادم DHCP.",
                "Networking - الشبكات والإنترنت",
                "عاجل (Urgent)",
                "جديدة",
                "أحمد حسن (ahmed.hassan)",
                "غير معيّن",
                None,
                now_str,
                (now_dt + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            ),
        ]
        cur.executemany(
            """INSERT INTO tickets
               (title, description, category, priority, status, requester, assignee, attachment, created_at, sla_deadline)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            sample_tickets,
        )

    conn.commit()
    conn.close()


@app.context_processor
def utility_processor():
    def is_sla_breached(deadline_str, status):
        if status == "مغلقة":
            return False
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
        return datetime.now() > deadline

    return dict(is_sla_breached=is_sla_breached, categories=CATEGORIES, sla_hours=SLA_HOURS)


@app.route("/")
def index():
    conn = get_db()
    status_filter = request.args.get("status", "")
    category_filter = request.args.get("category", "")

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    query += " ORDER BY id DESC"

    tickets = conn.execute(query, params).fetchall()
    all_tickets = conn.execute("SELECT * FROM tickets").fetchall()
    kb_count = conn.execute("SELECT COUNT(*) FROM kb_articles").fetchone()[0]
    locked_users = conn.execute("SELECT COUNT(*) FROM ad_users WHERE locked = 1").fetchone()[0]
    conn.close()

    stats = {
        "total": len(all_tickets),
        "open": sum(1 for t in all_tickets if t["status"] != "مغلقة"),
        "urgent": sum(1 for t in all_tickets if "عاجل" in t["priority"] and t["status"] != "مغلقة"),
        "kb_count": kb_count,
        "locked_users": locked_users,
    }
    return render_template(
        "index.html",
        tickets=tickets,
        stats=stats,
        status_filter=status_filter,
        category_filter=category_filter,
    )


@app.route("/tickets/create", methods=["POST"])
def create_ticket():
    title = request.form["title"].strip()
    description = request.form["description"].strip()
    category = request.form["category"]
    priority = request.form["priority"]
    requester = request.form["requester"].strip()

    attachment_name = None
    file = request.files.get("attachment")
    if file and file.filename and allowed_file(file.filename):
        safe_name = secure_filename(file.filename)
        attachment_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], attachment_name))

    now_dt = datetime.now()
    created_at = now_dt.strftime("%Y-%m-%d %H:%M")
    deadline = (now_dt + timedelta(hours=SLA_HOURS.get(priority, 24))).strftime("%Y-%m-%d %H:%M")

    conn = get_db()
    conn.execute(
        """INSERT INTO tickets
           (title, description, category, priority, status, requester, attachment, created_at, sla_deadline)
           VALUES (?, ?, ?, ?, 'جديدة', ?, ?, ?, ?)""",
        (title, description, category, priority, requester, attachment_name, created_at, deadline),
    )
    conn.commit()
    conn.close()
    flash("تم إنشاء التذكرة بنجاح وتحديد موعد SLA تلقائياً.", "success")
    return redirect(url_for("index"))


@app.route("/tickets/<int:ticket_id>", methods=["GET", "POST"])
def ticket_detail(ticket_id):
    conn = get_db()
    ticket = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not ticket:
        conn.close()
        flash("التذكرة غير موجودة.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        action = request.form.get("action")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        if action == "update_meta":
            new_status = request.form["status"]
            new_assignee = request.form["assignee"].strip() or "غير معيّن"
            conn.execute(
                "UPDATE tickets SET status = ?, assignee = ? WHERE id = ?",
                (new_status, new_assignee, ticket_id),
            )
            conn.execute(
                "INSERT INTO ticket_comments (ticket_id, author, role, comment, created_at) VALUES (?, ?, ?, ?, ?)",
                (ticket_id, new_assignee, "النظام", f"تم تحديث حالة التذكرة إلى ({new_status})", now_str),
            )
            flash("تم تحديث بيانات التذكرة.", "info")

        elif action == "add_comment":
            author = request.form["author"].strip()
            role = request.form["role"]
            comment = request.form["comment"].strip()
            if comment:
                conn.execute(
                    "INSERT INTO ticket_comments (ticket_id, author, role, comment, created_at) VALUES (?, ?, ?, ?, ?)",
                    (ticket_id, author, role, comment, now_str),
                )
                flash("تمت إضافة الرد بنجاح.", "success")

        elif action == "promote_to_kb":
            kb_title = request.form["kb_title"].strip()
            kb_steps = request.form["kb_steps"].strip()
            conn.execute(
                "INSERT INTO kb_articles (title, category, symptoms, steps, created_at) VALUES (?, ?, ?, ?, ?)",
                (kb_title, ticket["category"], ticket["description"], kb_steps, now_str),
            )
            flash("تم نشر الحل كدليل إصلاح (SOP) في قاعدة المعرفة!", "success")

        conn.commit()
        conn.close()
        return redirect(url_for("ticket_detail", ticket_id=ticket_id))

    comments = conn.execute(
        "SELECT * FROM ticket_comments WHERE ticket_id = ? ORDER BY id ASC", (ticket_id,)
    ).fetchall()
    conn.close()
    return render_template("ticket_detail.html", ticket=ticket, comments=comments)


@app.route("/uploads/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/kb", methods=["GET", "POST"])
def knowledge_base():
    conn = get_db()
    if request.method == "POST":
        title = request.form["title"].strip()
        category = request.form["category"]
        symptoms = request.form["symptoms"].strip()
        steps = request.form["steps"].strip()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn.execute(
            "INSERT INTO kb_articles (title, category, symptoms, steps, created_at) VALUES (?, ?, ?, ?, ?)",
            (title, category, symptoms, steps, now_str),
        )
        conn.commit()
        flash("تمت إضافة المقال إلى قاعدة المعرفة.", "success")
        return redirect(url_for("knowledge_base"))

    search = request.args.get("q", "").strip()
    cat = request.args.get("category", "")
    query = "SELECT * FROM kb_articles WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR symptoms LIKE ? OR steps LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if cat:
        query += " AND category = ?"
        params.append(cat)
    query += " ORDER BY id DESC"

    articles = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("kb.html", articles=articles, search=search, cat=cat)


@app.route("/ad-lab", methods=["GET", "POST"])
def ad_lab():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        if action == "create_user":
            username = request.form["username"].strip().lower()
            full_name = request.form["full_name"].strip()
            department = request.form["department"].strip()
            try:
                conn.execute(
                    "INSERT INTO ad_users (username, full_name, department, status, locked, last_action) VALUES (?, ?, ?, 'نشط', 0, ?)",
                    (username, full_name, department, f"تم إنشاء الحساب ({now_str})"),
                )
                flash(f"تم إنشاء حساب Active Directory للمستخدم {username}.", "success")
            except sqlite3.IntegrityError:
                flash("اسم المستخدم موجود مسبقاً!", "danger")

        elif action == "unlock":
            user_id = request.form["user_id"]
            conn.execute(
                "UPDATE ad_users SET locked = 0, last_action = ? WHERE id = ?",
                (f"تم فك قفل الحساب ({now_str})", user_id),
            )
            flash("تم فك قفل الحساب بنجاح.", "success")

        elif action == "reset_password":
            user_id = request.form["user_id"]
            conn.execute(
                "UPDATE ad_users SET locked = 0, last_action = ? WHERE id = ?",
                (f"إعادة تعيين كلمة المرور + إجبار التغيير عند الدخول ({now_str})", user_id),
            )
            flash("تمت إعادة تعيين كلمة المرور بنجاح.", "info")

        elif action == "toggle_status":
            user_id = request.form["user_id"]
            user = conn.execute("SELECT status FROM ad_users WHERE id = ?", (user_id,)).fetchone()
            new_status = "معطّل" if user["status"] == "نشط" else "نشط"
            conn.execute(
                "UPDATE ad_users SET status = ?, last_action = ? WHERE id = ?",
                (new_status, f"تغيير حالة الحساب إلى {new_status} ({now_str})", user_id),
            )
            flash(f"تم تغيير حالة الحساب إلى ({new_status}).", "warning")

        conn.commit()
        conn.close()
        return redirect(url_for("ad_lab"))

    users = conn.execute("SELECT * FROM ad_users ORDER BY id ASC").fetchall()
    conn.close()
    return render_template("ad_lab.html", users=users)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
