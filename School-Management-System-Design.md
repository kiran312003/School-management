# School Management System — Zoho CRM + Zoho Creator
## Solution Architecture & Implementation Plan

---

## 1. Overall Data Flow

```
CRM Webform → Leads → Admission Confirmed → Students (auto-created)
     → Academic Year / Class / Section / Subject / Teacher (linked)
     → Attendance / Examinations / Fees (child records under Student)
     → Zoho Creator Parent App (reads from CRM via Deluge/API, filtered by parent-student link)
```

CRM is the system of record. Creator has no duplicate master data — it either queries CRM directly (via zoho.crm Deluge tasks) or, for performance, maintains a thin read-optimized cache that is refreshed by CRM workflows the moment source data changes. Either approach is defensible; the design below uses the cache approach because it scales better for parent-facing read traffic and keeps CRM API limits under control — but I've flagged the direct-query alternative too.

---

## 2. Zoho CRM — Modules & Data Model

### 2.1 Core Modules (custom, unless noted)

| Module | Type | Purpose |
|---|---|---|
| Leads | Standard | Captures webform enquiries |
| Students | Custom | Master student record, one per admitted child |
| Academic Years | Custom | e.g. 2025–26, with start/end dates, "Current Year" flag |
| Classes | Custom | Grade 1, Grade 2, etc. |
| Sections | Custom | Section A/B under a Class, per Academic Year |
| Subjects | Custom | Subject master, linked to Class |
| Teachers | Custom | Staff master (or use Zoho Users if staff need CRM logins) |
| Class-Teacher-Subject Mapping | Custom (junction) | Which teacher teaches which subject to which section, per year |
| Student Enrollment History | Custom (child of Student) | One row per academic year a student was in — preserves history as they progress |
| Attendance | Custom | Daily record, one row per student per date |
| Examinations | Custom | Exam definitions (Midterm, Final, Unit Test 1…) with Class + Academic Year |
| Exam Subjects / Marks | Custom (child of Examination or its own module) | Marks per student per subject per exam |
| Fee Structure | Custom | Total fee applicable per Class/Academic Year, fee heads (tuition, transport, etc.) |
| Fee Payments | Custom (child of Student) | Installment-wise payment records |
| Parent | Custom | Parent/guardian record, linked to Student(s), holds Creator login identifier |

### 2.2 Key Relationships

- Lead → Student: 1:1 conversion on admission confirmation (custom "Convert to Student" button/function rather than standard Lead Convert, since target is a custom module, not Contact/Deal).
- Student → Enrollment History: 1:Many. Each year's Class/Section/Roll No is a row here, not overwritten on the Student record. The Student module itself only holds current Class/Section (lookup) for fast filtering; history lives in the child module. This satisfies "preserve historical information as students progress."
- Academic Year → Classes → Sections: Sections are scoped to a Class and Academic Year.
- Class-Teacher-Subject Mapping: junction module resolving the many-to-many between Teachers, Subjects, and Sections.
- Attendance: lookup to Student + lookup to Section/Class + Date. Uniqueness enforced by Student+Date.
- Examinations → Marks: Examination is the parent; Marks module has one row per Student per Subject per Examination.
- Fee Payments: lookup to Student, Installment Number, Amount, Date, Mode, Fee Structure reference. Fee Structure holds the total payable; Fee Payments are summed via rollup.
- Parent → Student: Many-to-many is realistic, so this is a junction module (Parent, Student, Relationship type) rather than a direct lookup on Student.

### 2.3 Student ID Generation

Zoho CRM doesn't auto-generate custom formatted IDs natively, so use a Deluge function on before insert:

```javascript
studentId = "STU" + zoho.crm.getRecordCount("Students") + 1;
// Better: use Academic Year + sequence for readability and to avoid gaps on deletes
yearCode = input.AcademicYear.get("Year_Code");
seqSearch = zoho.crm.searchRecords("Students","(Student_ID|starts_with|STU" + yearCode + ")");
nextSeq = seqSearch == null ? 1 : seqSearch.size() + 1;
newId = "STU" + yearCode + nextSeq.toString().rightPad(4,"0");
```

---

## 3. Admission Workflow

1. Webform submits to Leads with fields: Student Name, DOB, Class Applied For, Parent Name, Phone, Email, Previous School, etc.
2. Lead Status field drives the pipeline.
3. On Admission Confirmed:
   - Creates Student
   - Generates Student ID
   - Creates initial enrollment row
   - Creates/links Parent
   - Updates Lead status to Converted
4. On Rejected: Lead is closed with a Rejection Reason.

---

## 4. Attendance — Preventing Duplicates/Errors

- Uniqueness: Deluge validation checks for existing record for same Student + Date.
- Bulk marking: teachers mark a section in one action using Creator or custom button.
- Attendance percentage stored in Enrollment History or summary fields.

---

## 5. Examinations & Marks

- Validations: marks between 0 and max marks
- Calculated fields: total marks, percentage, grade, and class rank
- Student-level and class-level views through reports and dashboard

---

## 6. Fees

- Fee Structure defines total payable and fee-head breakdown
- Fee Payments child module stores installments
- Rollups track Total Fees, Amount Collected, Outstanding, Payment Status
- Dashboards show collection and overdue trends

---

## 7. Reports & Dashboards (CRM)

- Admission funnel
- Enrollment by class/section
- Attendance metrics
- Academic performance
- Fees and collection dashboard
- Combined Management Dashboard

---

## 8. Zoho Creator — Parent Application

### 8.1 Structure
- Parent Login via Creator user login or Zoho One SSO
- Landing page fetches linked students and child selector
- Tabs for profile, attendance, exam results, fee status

### 8.2 Connecting Creator ↔ CRM

Two valid patterns:

Pattern A — Live query
Creator pages read CRM directly.

Pattern B — Cached read layer
CRM pushes summaries to Creator whenever records change. This is the recommended pattern for scale and lower API load.

### 8.3 Access Control
- Parent sees only their own child data
- Filters are applied at query level and report/page level
- Row-level permission ensures data cannot be accessed by URL tampering

---

## 9. Suggested Additional Feature: Automated Fee-Due & Attendance-Alert Notifications

- Daily scheduled Deluge job scans outstanding fees and low attendance
- Sends email or SMS to parent
- Tracks Last_Notified_Date to avoid repeated spam
- Uses searchRecords with indexed criteria instead of full-table loops

---

## 10. What to Include in the Submission Write-Up

1. Data structure and relationships
2. CRM–Creator integration explanation
3. Additional feature justification and optimization points

---

This document is a design blueprint — the actual Zoho CRM/Creator build still needs to be done in a Zoho One trial account per the assignment's submission requirements.
