# Zoho Creator Build Guide — Parent Application

This implements Pattern B: Creator holds a thin, read-only cache that CRM pushes into via Deluge.

---

## STEP 1 — Create the App

Zoho Creator → New Application → name it School_Parent_App.

---

## STEP 2 — Create the Connection to CRM

Setup → Connections → New Connection → choose Zoho CRM → authorize.
Name it crm_connection.

---

## STEP 3 — Forms (cache tables)

### Student_Profile
| Field | Type |
|---|---|
| Student_ID_Ref | Single Line |
| Student_Name | Single Line |
| Photo | Image |
| Current_Class | Single Line |
| Current_Section | Single Line |
| Parent_Email | Email |

### Attendance_Summary
| Field | Type |
|---|---|
| Student_ID_Ref | Single Line |
| Month | Single Line |
| Present_Days | Number |
| Total_Days | Number |
| Attendance_Percentage | Decimal |

### Exam_Results
| Field | Type |
|---|---|
| Student_ID_Ref | Single Line |
| Exam_Name | Single Line |
| Subject | Single Line |
| Marks_Obtained | Number |
| Max_Marks | Number |
| Grade | Single Line |

### Fee_Summary
| Field | Type |
|---|---|
| Student_ID_Ref | Single Line |
| Total_Fees | Currency |
| Amount_Collected | Currency |
| Outstanding | Currency |
| Payment_Status | Single Line |

### Fee_Payment_History
| Field | Type |
|---|---|
| Student_ID_Ref | Single Line |
| Payment_Date | Date |
| Amount_Paid | Currency |
| Mode | Single Line |
| Receipt_Number | Single Line |

---

## STEP 4 — User Login & Access Filtering

Settings → Users → enable self-signup or add parents individually.

```javascript
loggedInEmail = zoho.loginuser;
myStudents = Student_Profile[Parent_Email == loggedInEmail];
```

If a parent has multiple children, show a selector.

---

## STEP 5 — Pages

### Home page
On load, use the access-filter script above. If multiple students, show a student dropdown.

### Student_Dashboard page
Tabs/sections for Profile, Attendance, Exam Results, Fee Status.

**Profile tab**
```javascript
profile = Student_Profile[Student_ID_Ref == input.selectedStudentId];
```

**Attendance tab**
```javascript
attRecords = Attendance_Summary[Student_ID_Ref == input.selectedStudentId];
```

**Exam Results tab**
```javascript
results = Exam_Results[Student_ID_Ref == input.selectedStudentId];
```

**Fee Status tab**
```javascript
feeSummary = Fee_Summary[Student_ID_Ref == input.selectedStudentId];
paymentHistory = Fee_Payment_History[Student_ID_Ref == input.selectedStudentId];
```

---

## STEP 6 — Row-Level Security

Set criteria-based permissions on each form using Parent_Email == zoho.loginuser.

---

## STEP 7 — Verify the Sync

1. In CRM, mark attendance for a test student.
2. Confirm the CRM workflow pushes a row into Creator Attendance_Summary.
3. Log into the Creator app as the parent.
4. Repeat for fee payment and marks entry.

This is the key demo for your submission.

---

## What's Left for You To Do By Hand

- Create actual accounts in your Zoho One trial
- Build the modules and fields in the CRM UI
- Style the Creator pages
- Test edge cases such as zero linked students or duplicate attendance marks
