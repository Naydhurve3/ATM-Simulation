# Project Roadmap

## Evolution History

```
v1.0 (Initial)          v2.0 (Enhanced)             v3.0 (Current)
+----------------+     +-------------------+     +----------------------+
| Basic RBI data  |     | ML Models (13)    |     | DataLayer Singleton  |
| CLI display     |     | User System       |     | Property connections |
| Simple ATM      |     | ATM Simulator     |     | Dynamic Passbook     |
| Single user     |     | Web Dashboard     |     | Multi-account        |
|                 |     | Reports/PDF       |     | Dashboard redesign   |
|                 |     | Auto-retrain      |     | Architecture cleanup |
|                 |     | Phase 2 models(7) |     | 60 tests passing     |
+----------------+     +-------------------+     +----------------------+
```

---

## Current State (v3.0)

### Completed Features
- CLI application with 11-option main menu and 6 sub-menus
- RBI ATM/Card statistics ingestion, cleaning, and analysis
- 20 ML/DL models covering forecasting, clustering, anomaly detection, credit scoring, churn, loan risk, recommendations, and more
- User system with adult/minor registration, KYC, forgot card/PIN, recovery
- ATM simulator with withdraw, deposit, transfer, fraud detection, loan offers
- Web dashboard with 5 pages (Flask + Plotly)
- Multi-account passbook generation (PDF/PNG/JSON)
- Training data export with 10 dataset types
- Auto-retrain scheduler with freshness monitoring
- 5 educational demo walkthroughs
- Bank explorer (65 banks with attributes comparison)
- Savings goals, investment suggestions, RFM analysis, sentiment analysis

### Architecture Improvements (v3.0)
- **DatabaseManager singleton**: Unified connection management with auto-reconnect
- **Property-based connections**: 7 key classes re-fetch from DatabaseManager on every access
- **Dynamic passbook format**: PNG (<=20 txns) or PDF (>20 txns), single file per user
- **Dashboard redesign**: Modern banking-portal aesthetic with dark navy header
- **Dead code removal**: FeatureEngineering, ModelExplainer, 10 unused viz methods
- **Emoji-free menus**: Cross-terminal compatible text labels
- **Unified DB patterns**: DataIngestion/DataAnalysis now use DatabaseManager
- **60 tests passing**: Component-level model, validation, and utility tests

---

## Known Limitations

| Issue | Impact | Status |
|-------|--------|--------|
| LSTM/TF protobuf conflict on Windows | LSTM falls back to dummy class | Won't fix (Windows TF issue) |
| No integration tests for CLI orchestration | Risk of regressions in menu flow | Future work |
| Training data pipeline not consumed by models | CSVs exported but never read by ML | Future work |
| Missing `requirements.txt` entries | Fresh install will miss flask, plotly, etc. | Fixed (added) |

---

## Future Roadmap

### Short-term (v3.1)
1. **Wire training data pipeline** — Make CreditScorer, ChurnPredictor, LoanDefaultModel, SpendingForecaster accept optional CSV input from DataGenerator exports
2. **Integration tests** — Simulate full registration → transaction → passbook cycle with `pytest`
3. **Performance optimization** — Profile slow models (BankClustering, CashDemandForecaster) and add caching

### Medium-term (v3.2)
4. **Docker containerization** — `Dockerfile` + `docker-compose.yml` for reproducible environment
5. **REST API** — Flask RESTful endpoints for all ML models (beyond dashboard)
6. **Async model training** — Background task queue for model retraining
7. **Database migrations** — Alembic-style versioned schema migrations

### Long-term (v4.0)
8. **Production database** — Migrate from SQLite to PostgreSQL for concurrent access
9. **Real ATM integration** — Connect to actual ATM network APIs (NPCI/NFS)
10. **CI/CD pipeline** — GitHub Actions for automated testing and deployment
11. **Mobile app** — Flutter/React Native companion app
12. **Real-time fraud detection** — Stream processing with Kafka/Flink
13. **Federated learning** — Train models across bank data without centralizing

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| v3.0 | DatabaseManager singleton over raw sqlite3.connect | Eliminate connection leaks, stale connection errors |
| v3.0 | Property-based connections in 7 classes | Defense-in-depth against code that closes shared connections |
| v3.0 | Dynamic passbook format (PNG vs PDF by txn count) | Better UX: PNG scrolls naturally for small data, PDF for large |
| v3.0 | Single stable filename per user (overwrite) | Prevents file multiplication; one passbook per user at any time |
| v3.0 | Multi-account by name/phone/email match | Catches same person registering multiple times across banks |
| v3.0 | No emoji in menus | Windows PowerShell 5.1 cannot render multi-byte emoji |
| v3.0 | Dead code removal (FeatureEngineering, explainer, 10 viz methods) | Prevents confusion, reduces maintenance surface |
| v3.0 | Keep ₹ sign in monetary display | Renders correctly on all terminals |
