import os

from datetime import date, datetime
from typing import List

from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ── Database ──────────────────────────────────────────────────────────────────
# On Render free tier, use /tmp (ephemeral). Locally falls back to instance/.
_db_path = os.environ.get(
    "DATABASE_URL",
    os.path.join(
        "/tmp" if os.path.isdir("/tmp") else os.path.join(os.path.dirname(__file__), "instance"),
        "school_management.db"
    )
)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{_db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ── Secret key ────────────────────────────────────────────────────────────────
# Render injects a random SECRET_KEY via render.yaml generateValue.
# Locally we fall back to the dev key.
app.secret_key = os.environ.get("SECRET_KEY", "school-management-demo-secret")

db = SQLAlchemy(app)


class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    parent_email = db.Column(db.String(150), nullable=False)
    grade_applied = db.Column(db.String(50), nullable=False)
    lead_status = db.Column(db.String(50), nullable=False, default="Enquiry")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    parent_email = db.Column(db.String(150), nullable=False)
    current_class = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(20), nullable=False, default="A")
    academic_year = db.Column(db.String(20), nullable=False, default="2026-2027")
    academic_status = db.Column(db.String(50), nullable=False, default="Active")
    admission_date = db.Column(db.Date, default=date.today)

    attendance = db.relationship("Attendance", backref="student_detail", lazy=True)
    exam_results = db.relationship("ExamResult", backref="student_detail", lazy=True)
    fee_records = db.relationship("FeeRecord", backref="student_detail", lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def attendance_percentage(self):
        total = len(self.attendance)
        if total == 0:
            return 0
        present = sum(1 for item in self.attendance if item.status == "Present")
        return round((present / total) * 100, 1)

    @property
    def average_marks(self):
        total = len(self.exam_results)
        if total == 0:
            return 0
        return round(sum(item.percentage for item in self.exam_results) / total, 1)

    @property
    def outstanding_amount(self):
        fee = self.fee_records[-1] if self.fee_records else None
        if fee is None:
            return 0
        return fee.outstanding_amount


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(20), nullable=False)
    unique_key = db.Column(db.String(100), unique=True, nullable=False)

    @property
    def display_date(self):
        return self.attendance_date.strftime("%Y-%m-%d")


class ExamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    exam_name = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)

    @property
    def percentage(self):
        if self.max_marks == 0:
            return 0
        return round((self.marks_obtained / self.max_marks) * 100, 1)


class FeeRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)
    total_fee = db.Column(db.Float, nullable=False, default=5000.0)
    collected_amount = db.Column(db.Float, nullable=False, default=0.0)
    payment_status = db.Column(db.String(30), nullable=False, default="Unpaid")

    @property
    def outstanding_amount(self):
        return round(self.total_fee - self.collected_amount, 2)


def generate_student_id() -> str:
    count = Student.query.count() + 1
    return f"STU-{datetime.now().year}-{count:04d}"


def generate_unique_attendance_key(student_id: int, attendance_date: str) -> str:
    return f"{student_id}_{attendance_date}"


def convert_lead_to_student(lead: Lead):
    if Student.query.filter_by(parent_email=lead.parent_email, first_name=lead.first_name, last_name=lead.last_name).first():
        return None

    student = Student(
        student_id=generate_student_id(),
        first_name=lead.first_name,
        last_name=lead.last_name,
        parent_email=lead.parent_email,
        current_class=lead.grade_applied,
        section="A",
        academic_year="2026-2027",
        academic_status="Active",
    )
    db.session.add(student)
    db.session.flush()

    fee = FeeRecord(
        student_id=student.id,
        academic_year=student.academic_year,
        total_fee=5000.0,
        collected_amount=0.0,
        payment_status="Unpaid",
    )
    db.session.add(fee)
    db.session.commit()

    lead.lead_status = "Converted to Student"
    db.session.commit()
    return student


def evaluate_defaulters() -> List[Student]:
    defaulters = []
    for student in Student.query.all():
        attendance_rate = student.attendance_percentage
        marks_rate = student.average_marks
        if attendance_rate < 75 or marks_rate < 40:
            student.academic_status = "At-Risk"
            defaulters.append(student)
        else:
            student.academic_status = "Active"
    db.session.commit()
    return defaulters


def seed_demo_data():
    if Lead.query.first() or Student.query.first():
        return

    leads = [
        Lead(first_name="Aarav", last_name="Patel", parent_email="parent1@example.com", grade_applied="Grade 5", lead_status="Confirmed"),
        Lead(first_name="Meera", last_name="Sharma", parent_email="parent2@example.com", grade_applied="Grade 6", lead_status="Enquiry"),
        Lead(first_name="Ishaan", last_name="Kumar", parent_email="parent3@example.com", grade_applied="Grade 4", lead_status="Interview Scheduled"),
    ]

    for lead in leads:
        db.session.add(lead)

    db.session.commit()

    for lead in leads:
        if lead.lead_status == "Confirmed":
            convert_lead_to_student(lead)

    students = Student.query.all()
    for student in students:
        for item in [
            Attendance(student_id=student.id, attendance_date=date(2026, 8, 1), status="Present", class_name=student.current_class, section=student.section, unique_key=generate_unique_attendance_key(student.id, "2026-08-01")),
            Attendance(student_id=student.id, attendance_date=date(2026, 8, 2), status="Present", class_name=student.current_class, section=student.section, unique_key=generate_unique_attendance_key(student.id, "2026-08-02")),
            Attendance(student_id=student.id, attendance_date=date(2026, 8, 3), status="Absent", class_name=student.current_class, section=student.section, unique_key=generate_unique_attendance_key(student.id, "2026-08-03")),
            Attendance(student_id=student.id, attendance_date=date(2026, 8, 4), status="Present", class_name=student.current_class, section=student.section, unique_key=generate_unique_attendance_key(student.id, "2026-08-04")),
        ]:
            db.session.add(item)

        for exam in [
            ("Mid-Term", "Math", 75, 100),
            ("Mid-Term", "Science", 65, 100),
            ("Final", "Math", 82, 100),
        ]:
            db.session.add(ExamResult(student_id=student.id, exam_name=exam[0], subject=exam[1], marks_obtained=exam[2], max_marks=exam[3]))

        fee = FeeRecord.query.filter_by(student_id=student.id).first()
        if fee:
            fee.total_fee = 5000.0
            fee.collected_amount = 2500.0 if student.first_name == "Aarav" else 1800.0
            fee.payment_status = "Partial" if fee.collected_amount < fee.total_fee else "Paid"

    db.session.commit()


@app.route("/")
def index():
    metrics = build_dashboard_metrics()
    return render_template("dashboard.html", metrics=metrics)


@app.route("/leads", methods=["GET", "POST"])
def leads():
    if request.method == "POST":
        lead = Lead(
            first_name=request.form["first_name"],
            last_name=request.form["last_name"],
            parent_email=request.form["parent_email"],
            grade_applied=request.form["grade_applied"],
            lead_status="Enquiry",
        )
        db.session.add(lead)
        db.session.commit()
        flash("Lead created successfully.")
        return redirect(url_for("leads"))

    leads_list = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template("leads.html", leads=leads_list)


@app.route("/admission_webform.html")
@app.route("/admission-webform")
def admission_webform():
    return send_from_directory(".", "admission_webform.html")


@app.route("/webform/submit", methods=["POST"])
def webform_submit():
    first_name = request.form.get("First Name", "").strip() or request.form.get("first_name", "Student")
    last_name = request.form.get("Last Name", "").strip() or request.form.get("last_name", "Applicant")
    parent_email = request.form.get("Email", "").strip() or request.form.get("parent_email", "parent@example.com")
    grade_applied = request.form.get("Class_Applied_For", "").strip() or request.form.get("grade_applied", "Grade 1")

    lead = Lead(
        first_name=first_name,
        last_name=last_name,
        parent_email=parent_email,
        grade_applied=grade_applied,
        lead_status="Enquiry",
    )
    db.session.add(lead)
    db.session.commit()
    flash(f"Admission enquiry received for {first_name} {last_name}. Logged as new Lead in Zoho CRM.")
    return redirect(url_for("leads"))


@app.route("/lead/<int:lead_id>/confirm", methods=["POST"])
def confirm_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if lead.lead_status != "Converted to Student":
        student = convert_lead_to_student(lead)
        if student is None:
            flash("This lead already has a matching student record.")
        else:
            flash(f"Lead confirmed and student {student.student_id} created.")
    else:
        flash("Lead already converted.")
    return redirect(url_for("leads"))


@app.route("/students")
def students():
    students_list = Student.query.order_by(Student.id.asc()).all()
    return render_template("students.html", students=students_list)


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    if request.method == "POST":
        student = Student.query.get_or_404(int(request.form["student_id"]))
        attendance_date = request.form["attendance_date"]
        status = request.form["status"]
        key = generate_unique_attendance_key(student.id, attendance_date)

        existing = Attendance.query.filter_by(unique_key=key).first()
        if existing:
            flash("Duplicate attendance record prevented.")
            return redirect(url_for("attendance"))

        att = Attendance(
            student_id=student.id,
            attendance_date=datetime.strptime(attendance_date, "%Y-%m-%d").date(),
            status=status,
            class_name=student.current_class,
            section=student.section,
            unique_key=key,
        )
        db.session.add(att)
        db.session.commit()
        flash("Attendance marked successfully.")
        return redirect(url_for("attendance"))

    attendance_records = Attendance.query.order_by(Attendance.attendance_date.desc()).all()
    students_list = Student.query.all()
    return render_template("attendance.html", attendance_records=attendance_records, students=students_list)


@app.route("/exams", methods=["GET", "POST"])
def exams():
    if request.method == "POST":
        student = Student.query.get_or_404(int(request.form["student_id"]))
        result = ExamResult(
            student_id=student.id,
            exam_name=request.form["exam_name"],
            subject=request.form["subject"],
            marks_obtained=float(request.form["marks_obtained"]),
            max_marks=float(request.form["max_marks"]),
        )
        db.session.add(result)
        db.session.commit()
        flash("Exam result recorded.")
        return redirect(url_for("exams"))

    exam_results = ExamResult.query.order_by(ExamResult.id.desc()).all()
    students_list = Student.query.all()
    return render_template("exams.html", exam_results=exam_results, students=students_list)


@app.route("/fees", methods=["GET", "POST"])
def fees():
    if request.method == "POST":
        student = Student.query.get_or_404(int(request.form["student_id"]))
        total_fee = float(request.form["total_fee"])
        collected = float(request.form["collected_amount"])
        fee = FeeRecord.query.filter_by(student_id=student.id).first()
        if fee is None:
            fee = FeeRecord(student_id=student.id, academic_year=student.academic_year, total_fee=total_fee, collected_amount=collected)
            db.session.add(fee)
        else:
            fee.total_fee = total_fee
            fee.collected_amount = collected
            fee.academic_year = student.academic_year
        fee.payment_status = "Paid" if fee.collected_amount >= fee.total_fee else ("Partial" if fee.collected_amount > 0 else "Unpaid")
        db.session.commit()
        flash("Fee record updated.")
        return redirect(url_for("fees"))

    fee_records = FeeRecord.query.order_by(FeeRecord.id.desc()).all()
    students_list = Student.query.all()
    return render_template("fees.html", fee_records=fee_records, students=students_list)


@app.route("/dashboard")
def dashboard():
    metrics = build_dashboard_metrics()
    return render_template("dashboard.html", metrics=metrics)


def build_dashboard_metrics():
    funnel = {
        "Enquiry": Lead.query.filter_by(lead_status="Enquiry").count(),
        "Interview Scheduled": Lead.query.filter_by(lead_status="Interview Scheduled").count(),
        "Offered": Lead.query.filter_by(lead_status="Offered").count(),
        "Confirmed": Lead.query.filter_by(lead_status="Confirmed").count(),
        "Converted to Student": Lead.query.filter_by(lead_status="Converted to Student").count(),
    }

    class_summary = []
    students_by_class = db.session.query(Student.current_class, db.func.sum(FeeRecord.collected_amount).label("collected"), db.func.sum(FeeRecord.total_fee).label("total")).join(FeeRecord, FeeRecord.student_id == Student.id).group_by(Student.current_class).all()
    for current_class, collected, total in students_by_class:
        class_summary.append({
            "class_name": current_class,
            "collected": float(collected or 0),
            "total": float(total or 0),
            "outstanding": float((total or 0) - (collected or 0))
        })

    defaulters = evaluate_defaulters()
    at_risk = []
    for student in defaulters:
        at_risk.append({
            "name": student.full_name,
            "status": student.academic_status,
            "attendance": student.attendance_percentage,
            "average_marks": student.average_marks,
        })

    total_students = Student.query.count()
    total_fee_collected = db.session.query(db.func.sum(FeeRecord.collected_amount)).scalar() or 0
    total_fee_total = db.session.query(db.func.sum(FeeRecord.total_fee)).scalar() or 0

    return {
        "total_students": total_students,
        "total_fees": float(total_fee_total),
        "collected": float(total_fee_collected),
        "outstanding": float(total_fee_total - total_fee_collected),
        "funnel": funnel,
        "class_summary": class_summary,
        "defaulters": at_risk,
    }


@app.route("/parent", methods=["GET", "POST"])
def parent_portal():
    if request.method == "POST":
        parent_email = request.form["parent_email"].strip().lower()
        students = Student.query.filter_by(parent_email=parent_email).all()
        if not students:
            flash("No student record found for that parent email.")
            return redirect(url_for("parent_portal"))
        session["parent_email"] = parent_email
        session["student_id"] = students[0].id
        return redirect(url_for("parent_dashboard"))

    return render_template("parent_login.html")


@app.route("/parent/dashboard")
def parent_dashboard():
    parent_email = session.get("parent_email")
    if not parent_email:
        return redirect(url_for("parent_portal"))

    students = Student.query.filter_by(parent_email=parent_email).all()
    selected_student = Student.query.get(session.get("student_id")) if session.get("student_id") else students[0]
    if not students:
        return redirect(url_for("parent_portal"))

    attendance_records = Attendance.query.filter_by(student_id=selected_student.id).order_by(Attendance.attendance_date.asc()).all()
    total_days = len(attendance_records)
    present_days = sum(1 for entry in attendance_records if entry.status == "Present")
    attendance_percentage = round((present_days / total_days) * 100, 1) if total_days else 0

    fee_record = FeeRecord.query.filter_by(student_id=selected_student.id).order_by(FeeRecord.id.desc()).first()
    exam_results = ExamResult.query.filter_by(student_id=selected_student.id).all()

    return render_template(
        "parent_dashboard.html",
        students=students,
        selected_student=selected_student,
        attendance_records=attendance_records,
        attendance_percentage=attendance_percentage,
        present_days=present_days,
        total_days=total_days,
        fee_record=fee_record,
        exam_results=exam_results,
    )


@app.route("/parent/select/<int:student_id>")
def select_parent_student(student_id):
    session["student_id"] = student_id
    return redirect(url_for("parent_dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


with app.app_context():
    db.create_all()
    seed_demo_data()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
