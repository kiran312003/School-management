# School Management System — Zoho CRM + Zoho Creator

This workspace contains the full implementation blueprint for a school management solution built on Zoho CRM and Zoho Creator.

## Build order

1. Read the high-level system design in [School-Management-System-Design.md](School-Management-System-Design.md)
2. Follow the CRM setup sequence in [01-CRM-Build-Guide.md](01-CRM-Build-Guide.md)
3. Copy the Deluge functions in [02-Deluge-Scripts.md](02-Deluge-Scripts.md)
4. Build the parent-facing Creator app using [03-Creator-Build-Guide.md](03-Creator-Build-Guide.md)

## Recommended execution flow

- Build the CRM modules in the exact order listed in the guide
- Create automations and validation rules as you go
- Test each workflow before moving to the next step
- Complete the Creator app only after CRM data structures and logic are stable

## Project goals

- Lead-to-student admission workflow
- Student academic records
- Attendance tracking and monitoring
- Exam and marks management
- Fee management and alerts
- Parent portal access with read-only sync from CRM

## Important note

This repository is a structured project blueprint. The actual Zoho build still needs to be executed in your Zoho One trial account.
