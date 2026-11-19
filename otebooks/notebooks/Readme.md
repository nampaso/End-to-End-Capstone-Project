# Kenyan Retail Sales Performance Analysis (H1 2026)

## Business Problem
Duka Electronics wants to know which branches and products drive growth and where to focus marketing spend in H2 2026.

### Project Brief (Phase 1: Ask)
- **Stakeholder:** Head of Commercial Operations & Marketing, Duka Electronics.
- **Decision Informed:** Allocation of KES 15M H2 2026 marketing and promotional budget across branches and product categories, plus retention actions for underperforming branches.
- **Analytical Questions:**
  1. How did monthly and quarterly revenue, order volume, and gross margin trend across branches in H1 2026?
  2. Which product categories drive the highest revenue share versus the highest gross profit margin?
  3. Is the Q2 revenue contraction in Mombasa and Nakuru driven by lower order frequency or smaller order values?
  4. Do Gold loyalty customers generate significantly higher order spend than Bronze customers?
  5. Which branch and product combinations deliver the strongest gross profit and return rates?
- **Success Criteria:** A reproducible SQLite and Python pipeline, a Looker Studio dashboard, an Excel stakeholder workbook, and quantified H2 recommendations targeting at least 12% growth in H2 gross profit.

## Key Findings
- Nairobi generates 36% of revenue, but Eldoret grew fastest (+50% in Q2 vs Q1).
- Laptops are 58% of revenue from only 22% of orders.
- Mombasa and Nakuru revenue fell by about a quarter in Q2 and need attention.
- Gold loyalty customers have a statistically significantly higher order value than Bronze customers (p < 0.001).

## Tools
Python (pandas, NumPy, Matplotlib, Seaborn, SciPy, openpyxl) · SQLite · Looker Studio

## Repository Structure
data/         raw data or generator script
src/          reusable cleaning pipeline (cleaning.py)
notebooks/    01_cleaning.ipynb, 02_eda.ipynb, 03_analysis.ipynb
sql/          queries.sql
reports/      executive_summary.pdf, visual_report.pdf, dashboard.png, slides.pdf, stakeholder_summary.xlsx

## How to Run
pip install -r requirements.txt
python data/generate_data.py
jupyter notebook notebooks/01_cleaning.ipynb
jupyter notebook notebooks/02_eda.ipynb
jupyter notebook notebooks/03_analysis.ipynb

## Dashboard Link
[Insert Your Published Looker Studio URL Here]

## Author Details
- **Name:** [Your Full Name]
- **Track:** Track [A/B/C] - Data Analytics
- **Program:** Power Learn Project (PLP) Capstone (2026)
