    ```
                    JOB DESCRIPTION PDF
                           │
                           ▼
                    Job Understanding
                           │
                           ▼
                       JobProfile
                           │
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
               Resume PDF     Requirements
                    │             │
                    ▼             │
              Resume Parsing      │
                    │             │
                    ▼             │
               ResumeProfile      │
                    └──────┬──────┘
                           ▼
                  Requirement Matcher
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        Exact/Fuzzy    Semantic       Experience
          Match          Match           Match
             └─────────────┼─────────────┘
                           ▼
                    Evidence Mapping
                           │
              Requirement → Resume Span
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        Scoring Engine            Extra Detector
              │                         │
              ▼                         ▼
          Score 0–100              Relevant Extras
              │                  (no score impact)
              └────────────┬────────────┘
                           ▼
                    Candidate Report
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   Score Analysis     Evidence Viewer     Recommendations
                           │
                           ▼
                    Resume PDF Viewer
                           │
                  transparent highlights
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
           HR View                  Applicant View

```