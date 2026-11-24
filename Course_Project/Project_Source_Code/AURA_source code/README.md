# AURA — Research Intelligence & Publication Analytics Portal

AURA is a local institutional research-management portal for publication registry management, faculty research profiles, source-evidence verification, reviewer decisions, hybrid research-intelligence workflows and approved reporting.

## What's changed in this redesign

- Reworked the interface into a light institutional SaaS design system with a compact sidebar, consistent typography, refined tables, status chips, responsive layouts and clearer page hierarchy.
- Added a Faculty Directory page with profile details and verified-evidence-only publication, citation and h-index metrics.
- Added global search entry (press Enter to search the publication registry) and a department filter in the registry.
- Expanded the overview with year-wise publication and department distribution summaries based on the live registry.
- Reframed the Research Intelligence workspace with a clearly labelled workflow architecture, connector readiness and structured run results instead of a default raw JSON dump.
- Preserved the existing Python HTTP server, SQLite schema, API endpoints, imported data and existing workflows. No database migration was required.

## Existing capabilities retained

- 553 imported publication records from the 2024, 2025 and 2026 authority workbooks.
- Paper submission with title-similarity screening and duplicate acknowledgement.
- Publication registry, status/year/department filtering, record detail view and CSV export.
- Reviewer login, approve/return decisions, required review notes and audit logging.
- Faculty profile intake with separate Google Scholar, Scopus and Web of Science consent flags.
- Citation evidence intake and reviewer verification with source URLs.
- Hybrid AURA workflow run, duplicate candidate detection, verified-evidence citation metrics, validation warnings and human approval gate.
- Approved NIRF/NAAC-oriented CSV metrics export.

## Data integrity and important limitations

The supplied SQLite database remains in place and all existing publication/reviewer tables and records are preserved. On first startup, the project’s existing `intelligence.ensure_tables()` initializer creates four additive Research Intelligence tables (`faculty_profiles`, `citation_records`, `workflow_runs` and `source_verifications`) when they are absent; it does not alter or rewrite the existing publication table. A pre-startup database backup is included at `backups/aura_before_redesign.sqlite3`. The 553 imported records remain in their original `Imported · Unverified` state; the redesign does not mark historical entries as approved or verified.

The Faculty Directory reports metrics from `citation_records` linked to faculty profiles and marked `Verified`. The current project does not automatically reconcile the imported spreadsheet's free-text faculty names to the separate faculty-profile table. Do not interpret registry counts as faculty-verified metrics.

Google Scholar, Scopus and Web of Science connectors are readiness checks only until institution-approved endpoints, credentials and licences are configured. AURA does not scrape provider websites and does not claim that harvesting has occurred. The agent workflow is a hybrid, rule-based Python workflow with human approval, not an autonomous AI-agent service.

The NIRF/NAAC export is an approved metrics CSV extract, not a preformatted official submission template. PDF export, institutional SSO, HTTPS deployment, production-grade role/permission administration, full cross-source publication duplicate resolution, provider API integrations and advanced accreditation templates remain deployment/product work.

The supplied database contains no reviewer accounts. Create an authorized local reviewer as described below before testing reviewer-only actions. Do not share the reviewer password or database file.

## Requirements

- macOS or Linux
- Python 3.8 or newer
- No third-party Python packages required for the application

## Run on macOS

1. Extract the ZIP archive.
2. Open Terminal and enter the project folder:

   ```bash
   cd AURA_College_Portal
   ```

3. Create an authorized reviewer account (choose the actual official's name and a strong password):

   ```bash
   python3 manage_reviewers.py --id researchadmin --name "Research Office Administrator" --role "Research Office"
   ```

   Valid roles are `HOD`, `Dean` and `Research Office`. The command prompts for a password of at least 12 characters. The supplied database has no reviewer account preconfigured.

4. Start the server:

   ```bash
   python3 server.py
   ```

5. Open [http://localhost:8765](http://localhost:8765).
6. Stop the server with `Control + C`.

The server binds to `127.0.0.1` and is intended for local demonstration. Do not expose it directly to the public internet.

## Tests

Run the existing automated test suite:

```bash
python3 -m unittest discover -v
```

The six existing unit tests cover registry matching, seed integrity, authentication primitives and authority-data refresh behaviour. The redesigned JavaScript was also syntax-checked with Node.js. A temporary-database HTTP integration test exercised context loading, reviewer login, publication submission, reviewer approval, faculty profile creation, citation evidence intake and verification, workflow execution and approval, approved report export, and audit logging. The integration test did not write test records into the supplied database.

## Project structure

| File | Purpose |
|---|---|
| `server.py` | Local HTTP server, SQLite access, authentication and API routes |
| `intelligence.py` | Faculty profiles, citation evidence, connector readiness, workflow and approved report logic |
| `index.html` | Responsive AURA frontend and client-side interactions |
| `aura.sqlite3` | Persistent publication, reviewer, session, audit and Research Intelligence data |
| `backups/aura_before_redesign.sqlite3` | Original database backup from before app startup initialized the four Research Intelligence tables |
| `seed_records.json` | Imported authority publication records |
| `source_workbooks/` | Original 2024–2026 source spreadsheets |
| `Project_Documentation/` | Supplied project guide and workflow documentation |
| `manage_reviewers.py` | Authorized reviewer account creation |
| `replace_authority_data.py` | Controlled authority spreadsheet refresh utility |
| `test_*.py` | Existing automated tests |

## Security and deployment notes

Before institutional deployment, add HTTPS, institutional SSO, login throttling, secure secret management, scheduled database backups, privacy/legal review, production hosting and a formal permission matrix. Restrict access to the SQLite database, original workbooks and exported faculty data. Never commit API keys or reviewer credentials to source control.
