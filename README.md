# AURA – Research Intelligence & Publication Analytics Portal

## 1. Team Details

| Sl. No. | Name | USN | Division |
|---|---|---|---|
| 1 | Ravi Shantesh Desai | 01FE23BCI028 | B |
| 2 | Shreya Santosh Desai | 01FE23BCI016 | B |
| 3 | Anurag G | 01FE24BCI409 | B |
| 4 | Tejas M | 01FE23BCI052 | B |

**Department:** Computer Science and Artificial Intelligence  
**Institution:** KLE Technological University, Hubballi

## 2. Project Overview

AURA is a web-based research management platform developed to simplify the management of faculty research profiles, academic publications, citations and institutional research reports.

It provides a centralized system for publication management, source verification, reviewer approval, research analytics and NIRF/NAAC reporting.

## 3. Problem Statement

Academic research information is often maintained across multiple spreadsheets and platforms, making publication tracking, verification, duplicate detection and institutional reporting difficult.

AURA addresses these challenges through a centralized platform that organizes research records and simplifies publication management and verification.

## 4. Objectives

- Centralize faculty and publication records.
- Manage publication submissions and verification.
- Identify potential duplicate publications.
- Maintain citation information and research metrics.
- Implement reviewer authentication and approval.
- Generate faculty-wise and department-wise analytics.
- Support institutional research reporting.

## 5. Overview of 12 Assignments

The project coursework consists of the following 12 assignments.

| Assignment | Description |
|---|---|
| Assignment 1 | [Official assignment title] |
| Assignment 2 | [Official assignment title] |
| Assignment 3 | [Official assignment title] |
| Assignment 4 | [Official assignment title] |
| Assignment 5 | [Official assignment title] |
| Assignment 6 | [Official assignment title] |
| Assignment 7 | [Official assignment title] |
| Assignment 8 | [Official assignment title] |
| Assignment 9 | [Official assignment title] |
| Assignment 10 | [Official assignment title] |
| Assignment 11 | [Official assignment title] |
| Assignment 12 | [Official assignment title] |

## 6. Technologies Used

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python
- **Database:** SQLite
- **Data Handling:** JSON and CSV
- **Testing:** Python unittest

## 7. Implementation

The application consists of the following modules:

1. **Dashboard:** Displays publication statistics and research analytics.
2. **Faculty Management:** Maintains faculty profiles and research information.
3. **Publication Registry:** Stores and manages academic publications.
4. **Research Intelligence:** Supports research workflows, source verification and duplicate detection.
5. **Review and Approval:** Allows authorized reviewers to approve or return submissions.
6. **Citation Analytics:** Organizes citation information and faculty research metrics.
7. **Reports:** Supports institutional research reporting and CSV exports.
8. **Audit Trail:** Maintains records of important application activities.

The system uses a Python backend connected to an SQLite database, with an HTML, CSS and JavaScript frontend.

## 8. Results

The project provides a centralized research management application with:

- Faculty profile management.
- Publication submission and verification.
- Reviewer approval workflows.
- Duplicate publication screening.
- Citation evidence management.
- Research analytics and reporting.
- Audit history.

The existing database containing 553 imported publication records has been preserved.

External Google Scholar, Scopus and Web of Science integrations require appropriate configuration and credentials.

## 9. Project Source Code

```text
AURA_College_Portal/
│
├── index.html
├── server.py
├── intelligence.py
├── manage_reviewers.py
├── replace_authority_data.py
├── aura.sqlite3
├── seed_records.json
│
├── source_workbooks/
├── Project_Documentation/
├── backups/
│
├── test_app.py
├── test_auth.py
├── test_import_refresh.py
│
└── README.md
```

## 10. Project Execution

**Requirements:** Python 3.8 or newer.

Run the following commands:

```bash
cd AURA_College_Portal

python3 manage_reviewers.py \
--id researchadmin \
--name "Research Office Administrator" \
--role "Research Office"

python3 server.py
```

Open the application:

http://localhost:8765

## 11. Project Links

- **Source Code:** [GitHub Repository](GITHUB_REPOSITORY_URL)
- **Assignments:** [Assignment Folder](Assignments/)
- **Project Documentation:** [Documentation](Project_Documentation/)
- **Final Report:** [Final Report](Final_Report/)

## 12. Conclusion

AURA provides a centralized platform for managing institutional research information, faculty publications, citation verification and research analytics.

The project aims to improve the accuracy, accessibility and efficiency of academic research management while providing a foundation for institutional reporting and future research intelligence enhancements.

---

**KLE Technological University**  
**Department of Computer Science and Artificial Intelligence**