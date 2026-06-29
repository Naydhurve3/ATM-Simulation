# Architecture Documentation

This folder contains the complete architecture blueprints for the ATM & Banking Ecosystem v3.0.

## Contents

| File | Description |
|------|-------------|
| `01-system-architecture.md` | High-level component diagram, layer breakdown, design patterns, filesystem layout |
| `02-database-architecture.md` | Complete schema for all 3 SQLite databases, table definitions, inter-database relationships, connection architecture |
| `03-data-workflow.md` | End-to-end data pipeline from RBI CSV → ingestion → analysis → visualization → reports |
| `04-ml-model-architecture.md` | All 20 ML/DL models, algorithms, data sources, interface, training pipeline |
| `05-cli-workflow.md` | Menu structure map (11 main + 6 sub-menus), interaction flow, key design decisions |
| `06-user-system.md` | Registration flow (adult/minor), KYC levels, passbook generation, transaction types |
| `07-web-dashboard.md` | Flask routes, template structure, data flow between CLI and dashboard threads |
| `08-roadmap.md` | Project evolution v1→v3, current state, known limitations, future roadmap, decision log |

## Generated Diagrams

### Comprehensive Architecture PNGs (recommended)

| File | Description |
|------|-------------|
| `00-system-architecture.png` | Full layered system architecture with all components, layers, and connections |
| `01-database-erd.png` | Complete entity-relationship diagram across all 3 databases (atm_data, ecosystem, feature_store) |
| `02-ml-architecture.png` | All 20 ML/DL models with their data sources, algorithms, and output metrics |
| `03-data-pipeline.png` | End-to-end data flow: CSV → Ingestion → Analysis → Models → Output |
| `04-cli-menu-structure.png` | Full menu navigation map with all sub-menus and entry points |
| `05-user-system-flow.png` | User registration, login, recovery, and passbook generation flows |

### Auto-generated Diagrams (from original generator)

| File | Description |
|------|-------------|
| `architecture_overview.png` | High-level system architecture diagram (text-based) |
| `data_flow_diagram.png` | Data pipeline flow diagram (text-based) |
| `database_schema_diagram.png` | Database ER diagram (text-based) |
| `architecture_text_diagram.txt` | ASCII text overview |

## Regenerating Diagrams

To regenerate the **comprehensive** PNG diagrams:

```bash
python docs/architecture/generate_diagrams.py
```

To regenerate the **auto-generated** PNG diagrams (from original generator):

```bash
python -c "from src.data.generate_diagrams import generate_all; generate_all()"
```

Diagrams are generated directly to `docs/architecture/`.

## Quick Start

```bash
pip install -r requirements.txt
python run.py
```
