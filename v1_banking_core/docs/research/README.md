# V1 Research & Documentation Hub

This folder is the **knowledge base** of the ATM & Banking ecosystem: architecture blueprints
for this codebase + **domain research** explaining how real banks, ATMs, payments, loans and
regulations work — with workflows, diagrams and real RBI data validation.

## Domain Knowledge Series (10–19) — how banking actually works

| Doc | Covers |
|-----|--------|
| [`domain/10-banking-fundamentals.md`](domain/10-banking-fundamentals.md) | What a bank is, balance sheet, fractional reserves, credit multiplier, Indian banking structure, RBI levers (repo 5.25%, CRR 3%, SLR 18%) |
| [`domain/11-atm-operations.md`](domain/11-atm-operations.md) | ATM hardware/software anatomy, withdrawal sequence, NFS network, interchange fees, cash management |
| [`domain/12-transaction-lifecycle.md`](domain/12-transaction-lifecycle.md) | Authorisation → clearing → settlement; NEFT/RTGS/IMPS/UPI/cards/CTS/NACH; netting; UPI scale (22.7 Bn txns/mo) |
| [`domain/13-interbank-relationships.md`](domain/13-interbank-relationships.md) | RBI settlement accounts, NPCI, CCIL, SWIFT, nostro/vostro/loro, Rupee Vostro, inter-bank money market (repo/SDF/MSF/CBLO) |
| [`domain/14-loans-and-credit.md`](domain/14-loans-and-credit.md) | Loan lifecycle, 5 Cs, eligibility matrix, LTV norms, EBLR vs MCLR pricing, PSL 40%, NPA rules, document checklists (SBI rates as of 2026) |
| [`domain/15-kyc-aml-regulations.md`](domain/15-kyc-aml-regulations.md) | KYC tiers & OVDs, CTR/STR reporting to FIU-IND, PMLA, Basel III capital/liquidity (CAR 11.5%, LCR 100%), DICGC ₹5 lakh |
| [`domain/16-interest-rates.md`](domain/16-interest-rates.md) | Repo → MCLR/EBLR → loan rates; LAF corridor (SDF 5.00/repo 5.25/MSF 5.50); MCLR components; deposit stickiness |
| [`domain/17-fraud-and-security.md`](domain/17-fraud-and-security.md) | Fraud taxonomy (card/UPI/account-takeover/social), detection stack, RBI liability rules, PCI-DSS |
| [`domain/18-credit-scoring.md`](domain/18-credit-scoring.md) | CIBIL 300–900, score factors, scorecard maths (WOE/IV), report contents, Indian bureaus |
| [`domain/19-real-data-validation.md`](domain/19-real-data-validation.md) | Shipped RBI data, computed facts, refresh workflow, sources table, caveats |

> Rates/limits in the domain docs are **as of Aug 2026** (RBI MPC Aug 5, 2026; SBI published
> rates; RBI CRR/SLR Directions 2025). Always verify against the primary sources in doc 19.

## Architecture Series (01–08) — how this codebase works

| Doc | Covers |
|-----|--------|
| `01-system-architecture.md` | High-level component diagram, layers, design patterns, filesystem layout |
| `02-database-architecture.md` | Schema for all 3 SQLite databases + connection architecture |
| `03-data-workflow.md` | End-to-end data pipeline: RBI CSV → ingestion → analysis → models → reports |
| `04-ml-model-architecture.md` | All ML/DL models, algorithms, data sources, interfaces, training pipeline |
| `05-cli-workflow.md` | Menu structure map, interaction flows, design decisions |
| `06-user-system.md` | Registration (adult/minor), KYC levels, passbook, transactions |
| `07-web-dashboard.md` | Flask routes, templates, CLI↔web data flow |
| `08-roadmap.md` | Evolution v1→v4, limitations, roadmap, decision log |

## Diagram Gallery

- **Mermaid diagrams** — embedded in every domain doc (`flowchart` / `sequenceDiagram`);
  render natively on GitHub.
- **PNG architecture diagrams** — `00-system-architecture.png`, `01-database-erd.png`,
  `02-ml-architecture.png`, `03-data-pipeline.png`, `04-cli-menu-structure.png`,
  `05-user-system-flow.png` (regenerate with `python v1_banking_core/docs/research/generate_diagrams.py`).
- ASCII diagrams: `architecture_text_diagram.txt`, `architecture_overview.png`, etc.

## Data & Validation

- Real RBI data: `../data/raw/RBI_ATM_Card_Statistics.csv` (65 banks × 10 months)
- Refresh script: `../scripts/download_rbi_data.py` (see doc 19)
