# CRM Build Guide — Step-by-Step (Execute in this order)

Do these in a Zoho One trial account: Setup → Developer Space → Modules and Fields to create modules, Setup → Automation → Workflow Rules for automations, Setup → Customization → Functions for Deluge functions.

Build order matters — later modules reference earlier ones via lookups.

---

## STEP 1 — Academic Years module

Custom module: Academic_Years

| Field | Type | Notes |
|---|---|---|
| Year_Name | Single Line (e.g. "2025-26") | Required, unique |
| Year_Code | Single Line (e.g. "2526") | Required, unique — used in Student ID |
| Start_Date | Date | Required |
| End_Date | Date | Required |
| Is_Current | Checkbox | Only one record should be true at a time |

Validation rule: on save, if Is_Current = true, run a workflow → Deluge function that sets Is_Current = false on all other Academic Year records.

---

## STEP 2 — Classes module

Custom module: Classes

| Field | Type | Notes |
|---|---|---|
| Class_Name | Single Line (e.g. "Grade 5") | Required |
| Class_Order | Number | For sorting |

---

## STEP 3 — Sections module

Custom module: Sections

| Field | Type | Notes |
|---|---|---|
| Section_Name | Single Line (e.g. "A") | Required |
| Class | Lookup → Classes | Required |
| Academic_Year | Lookup → Academic_Years | Required |
| Class_Teacher | Lookup → Teachers | Set after Teachers module exists |
| Capacity | Number | Optional |

Display name formula: Class.Class_Name + " - " + Section_Name + " (" + Academic_Year.Year_Name + ")"

---

## STEP 4 — Subjects module

Custom module: Subjects

| Field | Type | Notes |
|---|---|---|
| Subject_Name | Single Line | Required |
| Subject_Code | Single Line | Required, unique |
| Class | Lookup → Classes | Which class this subject applies to |

---

## STEP 5 — Teachers module

Custom module: Teachers

| Field | Type | Notes |
|---|---|---|
| Teacher_Name | Single Line | Required |
| Email | Email | Required, unique |
| Phone | Phone | |
| Employee_ID | Single Line | Unique |
| User | Lookup → Users (standard) | If teachers need CRM logins |

Go back to Sections and set Class_Teacher lookup values.

---

## STEP 6 — Class-Teacher-Subject Mapping module

Custom module: Subject_Assignments

| Field | Type | Notes |
|---|---|---|
| Section | Lookup → Sections | Required |
| Subject | Lookup → Subjects | Required |
| Teacher | Lookup → Teachers | Required |
| Academic_Year | Lookup → Academic_Years | Required |

Validation: prevent duplicate rows for same Section+Subject+Academic_Year combo.

---

## STEP 7 — Students module

Custom module: Students

| Field | Type | Notes |
|---|---|---|
| Student_ID | Single Line | Auto-generated, read-only after creation |
| Student_Name | Single Line | Required |
| DOB | Date | Required |
| Gender | Picklist | |
| Current_Class | Lookup → Classes | |
| Current_Section | Lookup → Sections | |
| Current_Academic_Year | Lookup → Academic_Years | |
| Admission_Date | Date | |
| Status | Picklist | Default "Active" |
| Source_Lead | Lookup → Leads | |
| Photo | Image | Optional |
| Blood_Group | Picklist | Optional |
| Address | Multi-line | |
| Total_Fees | Currency | |
| Amount_Collected | Currency | |
| Outstanding | Formula | Total_Fees - Amount_Collected |
| Payment_Status | Picklist | Set by Deluge |
| Attendance_Percentage | Percent | Set by scheduled Deluge function |
| Last_Fee_Notified_Date | Date | For notification idempotency |
| Last_Attendance_Notified_Date | Date | For notification idempotency |

Field-level security: Student_ID read-only after creation.

---

## STEP 8 — Enrollment History module

Custom module: Enrollment_History (child list on Students)

| Field | Type | Notes |
|---|---|---|
| Student | Lookup → Students | Required |
| Academic_Year | Lookup → Academic_Years | Required |
| Class | Lookup → Classes | Required |
| Section | Lookup → Sections | Required |
| Roll_Number | Single Line | |
| Promotion_Status | Picklist | Promoted/Retained/Transferred |
| Attendance_Percentage_YearEnd | Percent | Snapshot at year close |

One row created automatically per student per academic year.

---

## STEP 9 — Parent module + Parent-Student mapping

Custom module: Parents

| Field | Type | Notes |
|---|---|---|
| Parent_Name | Single Line | Required |
| Email | Email | Required, unique |
| Phone | Phone | Required |
| Relationship | Picklist | Father/Mother/Guardian |

Custom module: Parent_Student_Mapping

| Field | Type | Notes |
|---|---|---|
| Parent | Lookup → Parents | Required |
| Student | Lookup → Students | Required |
| Is_Primary_Contact | Checkbox | For notifications |

---

## STEP 10 — Lead → Student Conversion

In Leads, add custom fields:
- Class_Applied_For (Lookup → Classes)
- Rejection_Reason (Picklist)
- Admission_Stage (Picklist: New/Contacted/Document Verification/Interview Scheduled/Admission Confirmed/Rejected)

Build webform with Student Name, DOB, Class Applied For, Parent Name, Parent Email, Parent Phone, Previous School, Address.

Workflow rule: On Admission_Stage = "Admission Confirmed" → trigger Deluge function convertLeadToStudent.

---

## STEP 11 — Attendance module

Custom module: Attendance

| Field | Type | Notes |
|---|---|---|
| Student | Lookup → Students | Required |
| Section | Lookup → Sections | Denormalized for reporting |
| Date | Date | Required |
| Status | Picklist (Present/Absent/Late/Excused) | Required |
| Marked_By | Lookup → Users | Auto-set to logged-in user |

Validation rule: reject duplicate Student+Date rows.

Scheduled function nightly: calculateAttendancePercentage.

---

## STEP 12 — Fee Structure + Fee Payments

Custom module: Fee_Structure

| Field | Type | Notes |
|---|---|---|
| Class | Lookup → Classes | Required |
| Academic_Year | Lookup → Academic_Years | Required |
| Fee_Head | Picklist | Tuition/Transport/Lab/Library/Other |
| Amount | Currency | Required |
| Due_Date | Date | |

Custom module: Fee_Payments (child list on Students)

| Field | Type | Notes |
|---|---|---|
| Student | Lookup → Students | Required |
| Fee_Structure | Lookup → Fee_Structure | Required |
| Installment_Number | Number | |
| Amount_Paid | Currency | Required |
| Payment_Date | Date | Required |
| Mode | Picklist | Cash/Card/UPI/Bank Transfer |
| Receipt_Number | Single Line | Unique |

Workflow Rule: On Fee_Payments create/edit → function recalculateFeeStatus updates Amount_Collected, Outstanding, Payment_Status on Student.

Total_Fees on Student: Deluge function sums applicable Fee_Structure rows for Current_Class + Current_Academic_Year.

---

## STEP 13 — Examinations + Marks

Custom module: Examinations

| Field | Type | Notes |
|---|---|---|
| Exam_Name | Single Line | Required |
| Class | Lookup → Classes | Required |
| Academic_Year | Lookup → Academic_Years | Required |
| Exam_Date | Date | |

Custom module: Marks

| Field | Type | Notes |
|---|---|---|
| Student | Lookup → Students | Required |
| Examination | Lookup → Examinations | Required |
| Subject | Lookup → Subjects | Required |
| Marks_Obtained | Number | Required |
| Max_Marks | Number | Pulled from Examination config |
| Grade | Single Line | Set by Deluge |

Validation: Marks_Obtained must be between 0 and Max_Marks.

Scheduled function: calculateRanksAndGrades.

---

## STEP 14 — Notification automation (additional feature)

Scheduled function daily at 8 AM:
- Loop overdue Fee_Payments and low-attendance Students using searchRecords
- Send email/SMS to linked Parent
- Update Last_Fee_Notified_Date / Last_Attendance_Notified_Date

Full script in 02-Deluge-Scripts.md.

---

## STEP 15 — Reports & Dashboards

Create these under Reports in CRM:

1. Admission Funnel
2. Enrollment by Class/Section
3. Attendance Below 75%
4. Fee Outstanding by Class
5. Exam Performance

Combine into one Dashboard with KPI tiles.

---

Next file: 02-Deluge-Scripts.md has every script referenced above.
