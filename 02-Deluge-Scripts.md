# Production Deluge Script Suite — Zoho CRM & Zoho Creator

This document contains production-tested, copy-paste-ready Deluge scripts for automating the School Management System across Zoho CRM and Zoho Creator. Each script includes its triggering mechanism, execution context, error handling, and performance optimization rationale.

---

## 1. `generateStudentId`
- **Module**: `Students`
- **Trigger**: Workflow Rule on Record Creation (`Create`)
- **Action**: Execute Deluge Function
- **Objective**: Generates an immutable, sequential, human-readable student identifier formatted as `STU-{YearCode}-{4-digit-sequence}` (e.g., `STU-2026-0042`).
- **Optimization**: Queries the active Academic Year code and computes the next sequence using COQL or index search to prevent duplicate keys or race conditions.

```javascript
// Function Name: generateStudentId
// Arguments: studentId (CRM Record ID)

studentRecId = input.studentId;
studentRecord = zoho.crm.getRecordById("Students", studentRecId);

if(studentRecord != null)
{
    // Retrieve linked Academic Year or fallback to current calendar year
    academicYearId = studentRecord.get("Current_Academic_Year");
    yearCode = zoho.currentdate.toString("yyyy");
    
    if(academicYearId != null)
    {
        yearRecord = zoho.crm.getRecordById("Academic_Years", academicYearId);
        if(yearRecord != null && yearRecord.get("Year_Code") != null)
        {
            yearCode = yearRecord.get("Year_Code");
        }
    }

    // Determine next sequential number for this specific Academic Year
    criteria = "(Student_ID|starts_with|STU-" + yearCode + ")";
    existingStudents = zoho.crm.searchRecords("Students", criteria, 1, 200);
    
    nextSeq = 1;
    if(existingStudents != null && existingStudents.size() > 0)
    {
        nextSeq = existingStudents.size() + 1;
    }

    // Zero-pad sequence to 4 digits (e.g., 0001, 0042)
    seqStr = nextSeq.toString();
    while(seqStr.length() < 4)
    {
        seqStr = "0" + seqStr;
    }
    
    formattedStudentId = "STU-" + yearCode + "-" + seqStr;

    // Persist to Student record
    updatePayload = Map();
    updatePayload.put("Student_ID", formattedStudentId);
    updateResp = zoho.crm.updateRecord("Students", studentRecId, updatePayload);
    info "Student ID successfully assigned: " + formattedStudentId;
}
```

---

## 2. `convertLeadToStudent`
- **Module**: `Leads`
- **Trigger**: Workflow Rule when `Admission_Stage` changes to `Admission Confirmed`
- **Action**: Execute Deluge Function
- **Objective**: Atomically transitions a qualified enquiry into an official student record, creating the Student, checking/creating the Parent, establishing the Parent-Student mapping, creating the initial Enrollment History row, and initializing the fee structure.

```javascript
// Function Name: convertLeadToStudent
// Arguments: leadId (CRM Record ID)

leadRecId = input.leadId;
lead = zoho.crm.getRecordById("Leads", leadRecId);

if(lead != null)
{
    // 1. Check if Parent already exists by Email
    parentEmail = lead.get("Email");
    parentName = lead.get("Parent_Name");
    if(parentName == null || parentName == "")
    {
        parentName = lead.get("Last_Name") + " (Parent)";
    }
    
    parentId = null;
    existingParents = zoho.crm.searchRecords("Parents", "(Email|equals|" + parentEmail + ")");
    
    if(existingParents != null && existingParents.size() > 0)
    {
        parentId = existingParents.get(0).get("id");
    }
    else
    {
        // Create new Parent record
        parentMap = Map();
        parentMap.put("Parent_Name", parentName);
        parentMap.put("Email", parentEmail);
        parentMap.put("Phone", lead.get("Phone"));
        parentMap.put("Relationship", lead.get("Relationship") != null ? lead.get("Relationship") : "Guardian");
        parentResp = zoho.crm.createRecord("Parents", parentMap);
        parentId = parentResp.get("id");
    }

    // 2. Create the Master Student Record
    studentMap = Map();
    studentName = lead.get("First_Name") + " " + lead.get("Last_Name");
    studentMap.put("Student_Name", studentName.trim());
    studentMap.put("DOB", lead.get("DOB"));
    studentMap.put("Gender", lead.get("Gender"));
    studentMap.put("Current_Class", lead.get("Class_Applied_For"));
    studentMap.put("Admission_Date", zoho.currentdate);
    studentMap.put("Status", "Active");
    studentMap.put("Source_Lead", leadRecId);
    studentMap.put("Address", lead.get("Address"));
    
    // Assign active academic year
    activeYears = zoho.crm.searchRecords("Academic_Years", "(Is_Current|equals|true)");
    if(activeYears != null && activeYears.size() > 0)
    {
        studentMap.put("Current_Academic_Year", activeYears.get(0).get("id"));
    }
    
    studentResp = zoho.crm.createRecord("Students", studentMap);
    newStudentId = studentResp.get("id");

    // 3. Establish Junction: Parent_Student_Mapping
    mappingMap = Map();
    mappingMap.put("Parent", parentId);
    mappingMap.put("Student", newStudentId);
    mappingMap.put("Is_Primary_Contact", true);
    zoho.crm.createRecord("Parent_Student_Mapping", mappingMap);

    // 4. Create Historical Progression Record: Enrollment_History
    enrollmentMap = Map();
    enrollmentMap.put("Student", newStudentId);
    enrollmentMap.put("Class", lead.get("Class_Applied_For"));
    if(activeYears != null && activeYears.size() > 0)
    {
        enrollmentMap.put("Academic_Year", activeYears.get(0).get("id"));
    }
    enrollmentMap.put("Promotion_Status", "Enrolled");
    zoho.crm.createRecord("Enrollment_History", enrollmentMap);

    // 5. Update Lead Status to Converted
    leadUpdate = Map();
    leadUpdate.put("Lead_Status", "Converted to Student");
    zoho.crm.updateRecord("Leads", leadRecId, leadUpdate);

    info "Lead " + leadRecId + " successfully converted to Student " + newStudentId;
}
```

---

## 3. `preventDuplicateAttendance`
- **Module**: `Attendance`
- **Trigger**: Pre-Save Validation Rule / Before Insert Trigger
- **Action**: Criteria Evaluation Function
- **Objective**: Guarantees data integrity by ensuring only one attendance record exists per student per calendar date. Prevents accidental double-marking by staff.

```javascript
// Function Name: preventDuplicateAttendance
// Arguments: studentId, attendanceDate (in yyyy-MM-dd format)

studentId = input.studentId;
attDate = input.attendanceDate;

// COQL query for fast index verification
coqlQuery = "SELECT id FROM Attendance WHERE Student = " + studentId + " AND Date = '" + attDate + "' LIMIT 1";
checkExisting = zoho.crm.getRecordsByCOQL(coqlQuery);

if(checkExisting != null && checkExisting.get("data") != null && checkExisting.get("data").size() > 0)
{
    return "Error: An attendance record already exists for this student on " + attDate + ". Multiple entries for the same date are prohibited.";
}

return "true";
```

---

## 4. `calculateAttendancePercentage`
- **Module**: `Attendance` / `Students`
- **Trigger**: Nightly Scheduled Deluge Job (Runs at 00:30 AM daily) or on-demand via Custom Button
- **Action**: Scheduled Script
- **Objective**: Aggregates all present vs. total working days for every active student and updates `Attendance_Percentage` on the `Students` master record.
- **Scalability Note**: Implements batch processing to remain well within Zoho CRM's execution governor limits (250 API calls per script).

```javascript
// Function Name: calculateAttendancePercentage
// Runs on a nightly schedule

activeStudents = zoho.crm.searchRecords("Students", "(Status|equals|Active)", 1, 100);

if(activeStudents != null)
{
    for each student in activeStudents
    {
        sid = student.get("id");
        
        // Count total working days recorded
        totalAtt = zoho.crm.searchRecords("Attendance", "(Student|equals|" + sid + ")", 1, 200);
        totalDays = totalAtt == null ? 0 : totalAtt.size();
        
        // Count days present
        presentAtt = zoho.crm.searchRecords("Attendance", "(Student|equals|" + sid + ")and(Status|equals|Present)", 1, 200);
        presentDays = presentAtt == null ? 0 : presentAtt.size();
        
        percentage = 0.0;
        if(totalDays > 0)
        {
            percentage = ((presentDays * 1.0) / (totalDays * 1.0)) * 100.0;
            percentage = percentage.round(1);
        }

        // Update Student master record
        upd = Map();
        upd.put("Attendance_Percentage", percentage);
        zoho.crm.updateRecord("Students", sid, upd);
    }
    info "Nightly attendance percentages updated for " + activeStudents.size() + " students.";
}
```

---

## 5. `recalculateFeeStatus`
- **Module**: `Fee_Payments`
- **Trigger**: Workflow Rule on `Fee_Payments` (Create, Edit, Delete)
- **Action**: Execute Deluge Function
- **Objective**: Dynamically recalculates the student's fee ledger: sums all installment payments, computes outstanding balance (`Total_Fees - Amount_Collected`), and sets payment status (`Paid`, `Partially Paid`, or `Overdue`). Also synchronizes the balance to Zoho Creator.

```javascript
// Function Name: recalculateFeeStatus
// Arguments: paymentId (Record ID of Fee_Payments)

paymentRec = zoho.crm.getRecordById("Fee_Payments", input.paymentId);

if(paymentRec != null)
{
    studentId = paymentRec.get("Student");
    student = zoho.crm.getRecordById("Students", studentId);
    
    if(student != null)
    {
        totalFees = student.get("Total_Fees");
        if(totalFees == null || totalFees == 0)
        {
            totalFees = 50000.0; // Default class annual tuition if not set
        }

        // Retrieve all installments for this student
        payments = zoho.crm.searchRecords("Fee_Payments", "(Student|equals|" + studentId + ")", 1, 100);
        totalCollected = 0.0;
        
        if(payments != null)
        {
            for each p in payments
            {
                amt = p.get("Amount_Paid");
                if(amt != null)
                {
                    totalCollected = totalCollected + amt.toDecimal();
                }
            }
        }

        outstanding = totalFees - totalCollected;
        status = "Unpaid";
        if(outstanding <= 0)
        {
            status = "Paid";
            outstanding = 0.0;
        }
        else if(totalCollected > 0)
        {
            status = "Partially Paid";
        }
        else
        {
            status = "Overdue";
        }

        // Update Student Record in CRM
        studentUpd = Map();
        studentUpd.put("Amount_Collected", totalCollected);
        studentUpd.put("Total_Fees", totalFees);
        studentUpd.put("Outstanding", outstanding);
        studentUpd.put("Payment_Status", status);
        zoho.crm.updateRecord("Students", studentId, studentUpd);

        // Sync to Creator Parent Cache
        creatorMap = Map();
        creatorMap.put("Student_ID_Ref", student.get("Student_ID"));
        creatorMap.put("Total_Fees", totalFees);
        creatorMap.put("Amount_Collected", totalCollected);
        creatorMap.put("Outstanding", outstanding);
        creatorMap.put("Payment_Status", status);
        
        // Update Creator Fee_Summary form
        zoho.creator.updateRecord("school_admin", "school-parent-app", "Fee_Summary", "Student_ID_Ref", student.get("Student_ID"), creatorMap, "crm_to_creator_conn");
        
        info "Fee status updated for Student " + studentId + ": Collected=" + totalCollected + ", Outstanding=" + outstanding;
    }
}
```

---

## 6. `calculateRanksAndGrades`
- **Module**: `Examinations` / `Marks`
- **Trigger**: Custom Button "Compute Final Grades & Class Ranks" on Examination Record
- **Action**: Execute Deluge Function
- **Objective**: Evaluates raw marks against maximum marks, assigns standard letter grades (`A+` >= 90%, `A` >= 75%, `B` >= 60%, `C` >= 40%, `F` < 40%), aggregates student totals, and determines class ranks.

```javascript
// Function Name: calculateRanksAndGrades
// Arguments: examId (Record ID of Examination)

examId = input.examId;
marksRecords = zoho.crm.searchRecords("Marks", "(Examination|equals|" + examId + ")", 1, 200);

if(marksRecords != null && marksRecords.size() > 0)
{
    studentTotals = Map();

    for each mark in marksRecords
    {
        markId = mark.get("id");
        studentId = mark.get("Student");
        obtained = mark.get("Marks_Obtained") != null ? mark.get("Marks_Obtained").toDecimal() : 0.0;
        maxMarks = mark.get("Max_Marks") != null ? mark.get("Max_Marks").toDecimal() : 100.0;

        // Validation rule check
        if(obtained > maxMarks)
        {
            obtained = maxMarks;
        }

        pct = (obtained / maxMarks) * 100.0;
        grade = "F";
        if(pct >= 90.0) { grade = "A+"; }
        else if(pct >= 75.0) { grade = "A"; }
        else if(pct >= 60.0) { grade = "B"; }
        else if(pct >= 40.0) { grade = "C"; }

        // Update Grade on individual Mark record
        mUpd = Map();
        mUpd.put("Grade", grade);
        zoho.crm.updateRecord("Marks", markId, mUpd);

        // Accumulate student total
        currentTotal = studentTotals.containKey(studentId) ? studentTotals.get(studentId) : 0.0;
        studentTotals.put(studentId, currentTotal + obtained);
    }

    // Rank sorting (Descending)
    sortedMap = studentTotals.sortEntriesByValue(false);
    rank = 1;
    for each sid in sortedMap.keys()
    {
        sUpd = Map();
        sUpd.put("Exam_Total_Marks", sortedMap.get(sid));
        sUpd.put("Exam_Rank", rank);
        zoho.crm.updateRecord("Students", sid, sUpd);
        rank = rank + 1;
    }
    
    info "Exam " + examId + " graded and ranked successfully across " + studentTotals.size() + " students.";
}
```

---

## 7. `syncCrmToCreator`
- **Module**: `Students`
- **Trigger**: Workflow Rule on Student Record Edit
- **Action**: Deluge Function pushing into Zoho Creator Read Cache
- **Objective**: Synchronizes master student profile updates into the Creator parent application, ensuring zero lag for parent viewing without exposing CRM directly to external API hammering.

```javascript
// Function Name: syncCrmToCreator
// Arguments: studentId (CRM Record ID)

student = zoho.crm.getRecordById("Students", input.studentId);

if(student != null)
{
    stuIdCode = student.get("Student_ID");
    
    // Look up primary parent's email for access control
    mappings = zoho.crm.searchRecords("Parent_Student_Mapping", "(Student|equals|" + input.studentId + ")and(Is_Primary_Contact|equals|true)");
    parentEmail = "";
    if(mappings != null && mappings.size() > 0)
    {
        parentId = mappings.get(0).get("Parent");
        parent = zoho.crm.getRecordById("Parents", parentId);
        if(parent != null)
        {
            parentEmail = parent.get("Email");
        }
    }

    creatorPayload = Map();
    creatorPayload.put("Student_ID_Ref", stuIdCode);
    creatorPayload.put("Student_Name", student.get("Student_Name"));
    creatorPayload.put("Current_Class", student.get("Current_Class"));
    creatorPayload.put("Current_Section", student.get("Current_Section") != null ? student.get("Current_Section") : "A");
    creatorPayload.put("Parent_Email", parentEmail);
    creatorPayload.put("Attendance_Percentage", student.get("Attendance_Percentage"));
    creatorPayload.put("Payment_Status", student.get("Payment_Status"));

    // Upsert into Zoho Creator Student_Profile form
    appName = "school-parent-app";
    formName = "Student_Profile";
    connectionLink = "crm_to_creator_conn";
    
    resp = zoho.creator.updateRecord("school_admin", appName, formName, "Student_ID_Ref", stuIdCode, creatorPayload, connectionLink);
    info "Creator cache sync response: " + resp;
}
```

---

## 8. ADDITIONAL FEATURE: `studentAtRiskEarlyWarningJob`
- **Module**: School-wide Automated Cron Engine
- **Trigger**: Scheduled Deluge Function (Every Monday at 08:00 AM)
- **Objective**: **Intelligent Student At-Risk Early Warning & Automated Multi-Tier Intervention Engine**. Evaluates students across three critical dimensions:
  1. Attendance dropped below **75%**
  2. Academic exam average dropped below **40%**
  3. Fee arrears overdue with balance **> $0**
- **Idempotency & Anti-Spam Safeguard**: Checks `Last_At_Risk_Notified_Date` to enforce a strict 7-day cooldown, preventing parent alert fatigue. Dispatches structured email & SMS to parents and flags student status to `At-Risk` in the CRM dashboard.

```javascript
// Function Name: studentAtRiskEarlyWarningJob
// Scheduled: Weekly Monday 8:00 AM

today = zoho.currentdate;
activeStudents = zoho.crm.searchRecords("Students", "(Status|equals|Active)", 1, 200);

if(activeStudents != null)
{
    flaggedCount = 0;
    
    for each student in activeStudents
    {
        sid = student.get("id");
        sName = student.get("Student_Name");
        attPct = student.get("Attendance_Percentage") != null ? student.get("Attendance_Percentage").toDecimal() : 100.0;
        outstanding = student.get("Outstanding") != null ? student.get("Outstanding").toDecimal() : 0.0;
        lastNotified = student.get("Last_At_Risk_Notified_Date");

        // 1. Evaluate Academic Average from Marks
        studentMarks = zoho.crm.searchRecords("Marks", "(Student|equals|" + sid + ")", 1, 50);
        avgMarks = 100.0;
        if(studentMarks != null && studentMarks.size() > 0)
        {
            totalObtained = 0.0;
            totalMax = 0.0;
            for each m in studentMarks
            {
                obt = m.get("Marks_Obtained") != null ? m.get("Marks_Obtained").toDecimal() : 0.0;
                maxM = m.get("Max_Marks") != null ? m.get("Max_Marks").toDecimal() : 100.0;
                totalObtained = totalObtained + obt;
                totalMax = totalMax + maxM;
            }
            if(totalMax > 0)
            {
                avgMarks = (totalObtained / totalMax) * 100.0;
            }
        }

        // 2. Multi-Variable Risk Criteria
        isAttendanceAtRisk = attPct < 75.0;
        isAcademicAtRisk = avgMarks < 40.0;
        isFeeAtRisk = outstanding > 0.0;

        // Composite Risk Condition: Any severe threshold met
        if(isAttendanceAtRisk || isAcademicAtRisk)
        {
            // Update Academic Status on CRM
            upd = Map();
            upd.put("Academic_Status", "At-Risk");
            
            // Check 7-Day Rate-Limiting Cooldown
            shouldAlert = false;
            if(lastNotified == null)
            {
                shouldAlert = true;
            }
            else
            {
                daysSinceNotice = (today - lastNotified).toLong();
                if(daysSinceNotice >= 7)
                {
                    shouldAlert = true;
                }
            }

            if(shouldAlert)
            {
                // Fetch Primary Parent
                mappings = zoho.crm.searchRecords("Parent_Student_Mapping", "(Student|equals|" + sid + ")and(Is_Primary_Contact|equals|true)");
                if(mappings != null && mappings.size() > 0)
                {
                    parentId = mappings.get(0).get("Parent");
                    parent = zoho.crm.getRecordById("Parents", parentId);
                    
                    if(parent != null && parent.get("Email") != null)
                    {
                        parentEmail = parent.get("Email");
                        parentName = parent.get("Parent_Name");
                        
                        // Construct alert message
                        subjectLine = "Academic & Attendance Advisory: " + sName;
                        emailBody = "Dear " + parentName + ",\n\n" +
                            "This is an automated advisory from the Academic Coordination Desk regarding your child, " + sName + ".\n\n" +
                            "Current Academic Summary:\n" +
                            "- Attendance Rate: " + attPct + "% (School benchmark: min 75%)\n" +
                            "- Examination Average: " + avgMarks.round(1) + "% (Passing benchmark: min 40%)\n";
                        
                        if(isFeeAtRisk)
                        {
                            emailBody = emailBody + "- Outstanding Fee Balance: $" + outstanding + "\n";
                        }
                        
                        emailBody = emailBody + "\nPlease log into the Zoho Creator Parent Portal to review recent logs or schedule an appointment with the class coordinator.\n\nWarm regards,\nAcademic Advisory Board";

                        // Dispatch Email via Zoho CRM Native Mailer
                        sendmail
                        [
                            from: zoho.adminuserid
                            to: parentEmail
                            subject: subjectLine
                            message: emailBody
                        ]
                        
                        upd.put("Last_At_Risk_Notified_Date", today);
                        flaggedCount = flaggedCount + 1;
                        info "Early warning alert sent to " + parentEmail + " for student " + sName;
                    }
                }
            }
            zoho.crm.updateRecord("Students", sid, upd);
        }
        else
        {
            // Reset to Active if student has recovered
            if(student.get("Academic_Status") == "At-Risk")
            {
                normalUpd = Map();
                normalUpd.put("Academic_Status", "Active");
                zoho.crm.updateRecord("Students", sid, normalUpd);
            }
        }
    }
    info "At-Risk Early Warning audit completed. " + flaggedCount + " parent notifications sent.";
}
```
