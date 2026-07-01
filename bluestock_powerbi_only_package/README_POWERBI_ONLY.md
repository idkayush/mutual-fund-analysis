# Bluestock Power BI Package

This package contains only the Power BI-ready files for the dashboard task.

## Contents

- `bluestock_mf.db` — SQLite database generated from cleaned tables.
- `dashboard/powerbi_export/` — CSV exports ready to import into Power BI Desktop.
- `dashboard/assets/bluestock_theme.json` — Bluestock-style theme file.
- `dashboard/dax_measures.dax` — DAX measures to paste into Power BI.
- `dashboard/data_model_relationships.md` — model relationship guide.
- `dashboard/dashboard_build_checklist.md` — page-wise Power BI build checklist.
- `reports/dashboard_screenshots/` — folder where you can place exported dashboard page PNG screenshots.

## Use

1. Extract this folder into your existing `mutual-fund-analysis` project.
2. Open Power BI Desktop.
3. Import CSV files from `dashboard/powerbi_export/`.
4. Import theme from `dashboard/assets/bluestock_theme.json`.
5. Create relationships using `dashboard/data_model_relationships.md`.
6. Paste measures from `dashboard/dax_measures.dax`.
7. Build the 4 dashboard pages using `dashboard/dashboard_build_checklist.md`.
8. Save as `dashboard/bluestock_mf_dashboard.pbix`.
9. Export PDF as `reports/Dashboard.pdf`.
10. Save page screenshots in `reports/dashboard_screenshots/`.

Note: `.pbix` cannot be generated here because it requires Power BI Desktop, but all required data, theme, measures, and build instructions are included.
