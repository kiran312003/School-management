# Live Zoho Build Checklist — Complete School Management System

This is the exact execution plan for building the project in a Zoho One trial account.

---

## 1. Create the CRM modules

Create these modules in this exact order:

### A. Academic_Years
Fields:
- Year_Name (Single Line, required)
- Year_Code (Single Line, required, unique)
- Start_Date (Date, required)
- End_Date (Date, required)
- Is_Current (Checkbox)

Notes:
- Make sure only one record is current.
- This is used for Student_ID generation.

### B. Classes
Fields:
- Class_Name (Single Line, required)
- Class_Order (Number)

### C. Sections
Fields:
- Section_Name (Single Line, required)
- Class (Lookup to Classes, required)
- Academic_Year (Lookup to Academic_Years, required)
- Class_Teacher (Lookup to Teachers)
- Capacity (Number)

Display name formula:
Class.Class_Name + " - " + Section_Name + " (" + Academic_Year.Year_Name + ")"

### D. Subjects
Fields:
- Subject_Name (Single Line, required)
- Subject_Code (Single Line, required, unique)
- Class (Lookup to Classes)

### E. Teachers
Fields:
- Teacher_Name (Single Line, required)
- Email (Email, required, unique)
- Phone (Phone)
- Employee_ID (Single Line, unique)
- User (Lookup to Users)

Return to Sections after creating Teachers and assign Class_Teacher values.

### F. Subject_Assignments
Fields:
- Section (Lookup to Sections, required)
- Subject (Lookup to Subjects, required)
- Teacher (Lookup to Teachers, required)
- Academic_Year (Lookup to Academic_Years, required)

Validation rule:
- Prevent duplicate Section + Subject + Academic_Year combination.

### G. Students
Fields:
- Student_ID (Single Line, required)
- Student_Name (Single Line, required)
- DOB (Date, required)
- Gender (Picklist)
- Current_Class (Lookup to Classes)
- Current_Section (Lookup to Sections)
- Current_Academic_Year (Lookup to Academic_Years)
- Admission_Date (Date)
- Status (Picklist: Active, Inactive, Graduated, Transferred Out)
- Source_Lead (Lookup to Leads)
- Photo (Image)
- Blood_Group (Picklist)
- Address (Multi-line)
- Total_Fees (Currency)
- Amount_Collected (Currency)
- Outstanding (Formula: Total_Fees - Amount_Collected)
- Payment_Status (Picklist: Paid, Partially Paid, Overdue)
- Attendance_Percentage (Percent)
- Last_Fee_Notified_Date (Date)
- Last_Attendance_Notified_Date (Date)

Set field-level security for Student_ID as read-only after creation.

### H. Enrollment_History
Fields:
- Student (Lookup to Students, required)
- Academic_Year (Lookup to Academic_Years, required)
- Class (Lookup to Classes, required)
- Section (Lookup to Sections, required)
- Roll_Number (Single Line)
- Promotion_Status (Picklist: Promoted, Retained, Transferred)
- Attendance_Percentage_YearEnd (Percent)

### I. Parents
Fields:
- Parent_Name (Single Line, required)
- Email (Email, required, unique)
- Phone (Phone, required)
- Relationship (Picklist: Father, Mother, Guardian)

### J. Parent_Student_Mapping
Fields:
- Parent (Lookup to Parents, required)
- Student (Lookup to Students, required)
- Is_Primary_Contact (Checkbox)

### K. Attendance
Fields:
- Student (Lookup to Students, required)
- Section (Lookup to Sections)
- Date (Date, required)
- Status (Picklist: Present, Absent, Late, Excused)
- Marked_By (Lookup to Users)

Validation rule:
- Reject duplicates for Student + Date.

### L. Fee_Structure
Fields:
- Class (Lookup to Classes, required)
- Academic_Year (Lookup to Academic_Years, required)
- Fee_Head (Picklist: Tuition, Transport, Lab, Library, Other)
- Amount (Currency, required)
- Due_Date (Date)

### M. Fee_Payments
Fields:
- Student (Lookup to Students, required)
- Fee_Structure (Lookup to Fee_Structure, required)
- Installment_Number (Number)
- Amount_Paid (Currency, required)
- Payment_Date (Date, required)
- Mode (Picklist: Cash, Card, UPI, Bank Transfer)
- Receipt_Number (Single Line, unique)

### N. Examinations
Fields:
- Exam_Name (Single Line, required)
- Class (Lookup to Classes, required)
- Academic_Year (Lookup to Academic_Years, required)
- Exam_Date (Date)

### O. Marks
Fields:
- Student (Lookup to Students, required)
- Examination (Lookup to Examinations, required)
- Subject (Lookup to Subjects, required)
- Marks_Obtained (Number, required)
- Max_Marks (Number)
- Grade (Single Line)

Validation:
- Marks_Obtained must be between 0 and Max_Marks.

---

## 2. Create the required Lead fields

In standard Leads module, add:
- Class_Applied_For (Lookup to Classes)
- Rejection_Reason (Picklist)
- Admission_Stage (Picklist: New, Contacted, Document Verification, Interview Scheduled, Admission Confirmed, Rejected)

Create webform using:
- Student Name
- DOB
- Class Applied For
- Parent Name
- Parent Email
- Parent Phone
- Previous School
- Address

Set default status value to New.

---

## 3. Build the automations

### A. Academic Years current flag rule
Create a workflow on Academic_Years:
- When Is_Current is checked
- Run Deluge function to set all other Academic_Years Is_Current = false

### B. Student ID generation
Create a Workflow Rule on Students -> Create.
- Trigger: Create
- Use function: generateStudentId

### C. Lead conversion
Workflow on Leads:
- When Admission_Stage = Admission Confirmed
- Trigger: convertLeadToStudent

### D. Attendance uniqueness validation
Validation rule on Attendance:
- Run function: preventDuplicateAttendance
- Before save

### E. Attendance summary calculation
Scheduled function nightly:
- calculateAttendancePercentage

### F. Fee recalculation
Workflow on Fee_Payments:
- On create or edit
- Trigger: recalculateFeeStatus

### G. Exam result grade/rank
Scheduled function or on-demand button after marks close:
- calculateRanksAndGrades

### H. Notification automation
Scheduled daily function:
- dailyAlertsJob

---

## 4. Add the Deluge scripts exactly

Use the scripts from 02-Deluge-Scripts.md as the source.

Important rule:
- Keep field API names matching your actual Zoho module API names.
- If your API names differ from the examples, adjust them before saving.

---

## 5. Create the Creator app

Create a new Creator app named:
School_Parent_App

Then create these forms:

### Student_Profile
- Student_ID_Ref
- Student_Name
- Photo
- Current_Class
- Current_Section
- Parent_Email

### Attendance_Summary
- Student_ID_Ref
- Month
- Present_Days
- Total_Days
- Attendance_Percentage

### Exam_Results
- Student_ID_Ref
- Exam_Name
- Subject
- Marks_Obtained
- Max_Marks
- Grade

### Fee_Summary
- Student_ID_Ref
- Total_Fees
- Amount_Collected
- Outstanding
- Payment_Status

### Fee_Payment_History
- Student_ID_Ref
- Payment_Date
- Amount_Paid
- Mode
- Receipt_Number

Set up connection:
- Setup → Connections → New Connection → Zoho CRM
- Name: crm_connection

---

## 6. Creator pages and security

### Home page
- Get logged-in user's email
- Find all linked students
- If >1, provide selector
- Else auto-select the only child

### Student Dashboard pages
Create tabs:
- Profile
- Attendance
- Exam Results
- Fee Status

Use scripts like:
```javascript
loggedInEmail = zoho.loginuser;
myStudents = Student_Profile[Parent_Email == loggedInEmail];
```

For access control, add row-level security using criteria:
- Parent_Email == zoho.loginuser

---

## 7. Test sequence

Test in this order:

### Test 1: Admission flow
1. Submit lead through webform
2. Confirm Lead record created
3. Set Admission_Stage = Admission Confirmed
4. Check Student is created
5. Check Parent is created and mapping exists
6. Check Enrollment_History row exists
7. Check Student_ID generated

### Test 2: Attendance flow
1. Add Attendance record for a student
2. Confirm duplicate prevention works
3. Run nightly attendance function
4. Check Attendance_Percentage updated

### Test 3: Fees
1. Add Fee_Structure rows
2. Add Fee_Payment row
3. Check Amount_Collected updated
4. Check Outstanding and Payment_Status update

### Test 4: Marks
1. Add Examinations and Marks rows
2. Run grade/rank function
3. Verify Grade and rank values

### Test 5: Creator sync
1. Update a CRM record
2. Confirm Creator cache updates
3. Log in as the parent
4. Verify only that parent sees their student data

---

## 8. Final submission checklist

Prepare the project submission with:
- 1 screenshot of CRM module structure
- 1 screenshot of the lead-to-student workflow
- 1 screenshot of the attendance validation rule
- 1 screenshot of fee status update
- 1 screenshot of the Creator parent dashboard
- 1 brief explanation of how CRM is the system of record and Creator is a read-only cache
- 1 paragraph explaining the additional notification feature

---

## 9. Final advice

Do not try to build everything at once. Build in this order:
1. Modules
2. Fields
3. Core data flow
4. Validation rules
5. Deluge scripts
6. Reporting
7. Creator app
8. Final test and screenshots

If you follow this order exactly, the implementation will be stable and your submission will be clear and professional.
