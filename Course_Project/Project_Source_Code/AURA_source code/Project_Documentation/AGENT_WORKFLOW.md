# AURA Agent Workflow and Implementation Notes

## Workflow graph

```text
Faculty / HoD request
        |
        v
apniLeap AURA Coordinator
        |
        v
Faculty Profile Agent  -- consent and identity gate
        |
        +------------------------------+
        |                              |
        v                              v
Google Scholar Harvest Agent     Scopus/WoS Verification Agent
        |                              |
        +---------------+--------------+
                        v
              Duplicate Detection Agent
                        |
                        v
              Citation Analytics Agent
                        |
                        v
                 Validation Agent
                        |
                        v
             HoD / Dean / Research Office
                        |
               approved / corrections
                        |
                        v
                 Dashboard Agent
                        |
                        v
          Approved dashboard / NIRF-NAAC CSV
```

## Gate and safety rules

- A faculty profile is created before the workflow can run.
- Consent is recorded separately for Google Scholar, Scopus and Web of Science.
- A missing API credential or adapter is shown as not configured; the application does not scrape provider websites or invent verification results.
- Citation metrics use only records with `Verified` status. Unverified records are excluded.
- Duplicate DOI/title candidates are flagged. A reviewer must confirm a merge. The original row is retained and linked; it is not deleted.
- Workflow results remain unpublished until a Research Office, HoD or Dean reviewer approves them.
- Approved report exports include metric source names and source-record URLs.
- Actions are written to the audit table.

## Connector activation

The current local package has no provider credentials. Before activating live retrieval, the institution must provide approved access and configure secrets outside source control:

- `SCOPUS_API_KEY`
- `WOS_API_KEY`
- `AURA_SCHOLAR_ADAPTER_URL` (institution-approved adapter endpoint)

The connector readiness panel reports whether configuration exists. Actual provider API integration and institution-specific data mapping remain dependent on those credentials, provider terms and API response specifications.
