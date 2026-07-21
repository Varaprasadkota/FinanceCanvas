# FinanceCanvas

### Expense, Investment and Financial Intelligence Platform

FinanceCanvas is a responsive personal-finance analytics application built with Python, Streamlit, Pandas, Plotly and SQLite.

The platform combines expense tracking, budget monitoring, investment analysis, financial-health indicators and expense forecasting in one interactive application.

> This project is designed for educational and portfolio purposes. It does not provide regulated financial advice.

---

## Project Overview

Managing expenses, investments and financial goals through separate spreadsheets can make financial analysis difficult.

FinanceCanvas addresses this problem by creating one central platform where users can:

- Record income and expenses
- Import CSV bank statements
- Monitor monthly budgets
- Track investment performance
- Calculate financial-health indicators
- Forecast future expenses
- Generate automated financial observations

---

## Key Features

### Transaction Management

- Add income and expense transactions
- Edit existing transactions
- Delete incorrect transactions
- Filter transaction history
- Export filtered transactions to CSV
- Store information in a SQLite database

### Bank Statement Import

- Upload CSV bank statements
- Validate transaction dates and amounts
- Clean missing information
- Identify invalid records
- Prevent duplicate imports
- Preview data before saving

### Budget Analytics

- Create monthly budgets by category
- Compare budgets with actual spending
- Calculate remaining budget
- Track percentage of budget used
- Identify near-limit and over-budget categories
- Visualise budget versus actual spending

### Investment Portfolio

- Record stocks, ETFs, funds, bonds and cryptocurrency
- Calculate invested amount
- Calculate current portfolio value
- Measure unrealised gain or loss
- Calculate return percentage
- Update current prices manually
- Analyse asset allocation
- Identify best and lowest-performing holdings

### Financial Health

- Calculate estimated net worth
- Measure monthly savings rate
- Calculate emergency-fund coverage
- Analyse debt-to-income ratio
- Measure investment contribution rate
- Generate an educational financial-health score
- Produce automated financial observations

### Expense Forecasting

- Analyse historical monthly expenses
- Forecast expenses for the next three months
- Estimate future savings
- Forecast expenses by category
- Identify potential budget risks
- Export forecast results to CSV

---

## Technology Stack

| Area | Technology |
|---|---|
| Application | Streamlit |
| Programming | Python |
| Data analysis | Pandas and NumPy |
| Database | SQLite |
| Data visualisation | Plotly |
| File processing | CSV and OpenPyXL |
| Version control | Git and GitHub |
| Deployment | Streamlit Community Cloud |

---

## Application Architecture

```text
Manual Entry / CSV Statement
             |
             v
     Data Validation and Cleaning
             |
             v
        SQLite Database
             |
             v
     Python and Pandas Analysis
             |
             v
 Streamlit Dashboards and Plotly Charts