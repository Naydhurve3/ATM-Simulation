# Web Dashboard Architecture

## Overview

The web dashboard is a **Flask** application with **Plotly** charts, launched from the CLI (option 6) in a separate thread. It runs on `http://127.0.0.1:5000` and provides a graphical alternative to the CLI for data exploration.

## Launch Flow

```
CLI Option 6 ([Web] Web Dashboard)
  |
  +--> src/dashboard/app.py / run_dashboard()
  |      +--> Initializes Flask app
  |      +--> Accepts injected: data_analysis, data_visualization,
  |      |                      user_manager, user_data
  |      +--> Starts in daemon thread
  |      +--> Auto-opens browser to http://127.0.0.1:5000
  |
  +--> CLI remains usable
  +--> Press Enter to stop dashboard thread
```

## Routes

```
+============================================================+
| Route              | Method | Template       | Description |
+============================================================+
| /                  | GET    | index.html     | Dashboard   |
|                    |        |                | home page   |
| /analysis          | GET    | analysis.html  | RBI data    |
|                    |        |                | analysis    |
| /ml                | GET    | ml.html        | ML model    |
|                    |        |                | results     |
| /personal          | GET    | personal.html  | User        |
|                    |        |                | portfolio   |
| /monitoring        | GET    | monitoring.html| Model       |
|                    |        |                | health      |
+============================================================+
```

## Template Structure (6 templates)

```
src/dashboard/templates/
  +-- base.html           # Master layout with navigation
  +-- index.html          # Home dashboard with KPIs
  +-- analysis.html       # Data analysis charts
  +-- ml.html             # ML model results
  +-- personal.html       # User portfolio
  +-- monitoring.html     # Model health monitoring
```

## Template Design

### base.html
- Dark navy gradient header (#0c1a32)
- Sticky navigation with `request.path`-based active tab highlighting
- 4 color-coded metric card gradients:
  - Blue (#2563eb) for primary metrics
  - Green (#22c55e) for positive metrics
  - Amber (#f59e0b) for warnings
  - Red (#dc2626) for critical metrics
- Polished card/table/badge styles
- Responsive grid layout

### index.html
- Section title with subtitle
- Metric sub-labels for context
- Interactive Plotly charts in grid (gauge, top banks, monthly trend)

### analysis.html, ml.html, personal.html, monitoring.html
- Consistent styling with section titles
- Icon-based headers
- Refined typography
- Data tables and Plotly charts embedded

## Key Design Decisions

1. **Injected dependencies**: Dashboard receives pre-initialized `DataAnalysis`, `DataVisualization`, `UserManager`, and user data — avoids re-initializing the pipeline
2. **Daemon thread**: Dashboard runs in background; CLI stays interactive
3. **Plotly over matplotlib**: Interactive charts allow zoom, hover data, and export
4. **Responsive design**: CSS grid adapts to screen size for desktop/mobile viewing

## Data Flow

```
CLI (main thread)                Dashboard Thread
+------------------+            +-------------------+
| BankingAnalytics | ──inject──>| run_dashboard()   |
| Suite            |            |   Flask(__name__) |
|   .da ───────────┼──────────>|   app.da = ...    |
|   .viz ──────────┼──────────>|   app.viz = ...   |
|   .um ───────────┼──────────>|   app.um = ...    |
|   .user ─────────┼──────────>|   app.user = ...  |
+------------------+            +--------+----------+
                                          |
                                Browser requests
                                          |
                                          v
                                Flask routes read
                                from injected objects
                                          |
                                          v
                                Plotly JSON data embedded
                                in Jinja2 templates
                                          |
                                          v
                                Rendered HTML sent
                                to browser
```
