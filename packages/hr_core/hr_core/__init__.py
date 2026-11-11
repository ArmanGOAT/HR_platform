"""hr_core — one preprocessing code path for both branches (docs/ARCHITECTURE.md, 6.3 and 9).

Ingest, Search and the offline scripts import the same functions, so a resume is cleaned
and cut into chunks exactly the same way during training and in the demo.

Planned modules:
    language   — detect en / ru / uz / unknown
    anonymize  — remove names, e-mails, phones, links; compute person_key
    chunking   — split a resume into sections (summary, experience, projects, education, skills)
    skills     — normalize skill names (JS -> JavaScript)
    tokenize   — the tokenizer used by every ranker
"""

__version__ = "0.1.0"
