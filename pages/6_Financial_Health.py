from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# Locate the main FinanceCanvas project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from src.database import (
    get_all_investments,
    get_all_transactions,
    get_financial_profile,
    get_monthly_summary,
    initialise_database,
    save_financial_profile,
)
from src.ui import apply_global_styles

st.set_page_config(
    page_title="Financial Health | FinanceCanvas",
    page_icon="🩺",
    layout="wide",
)
apply_global_styles()

initialise_database()


st.title("🩺 Financial Health")

st.write(
    """
    Review your savings, debt, emergency fund,
    investments and overall financial position.
    """
)

st.caption(
    "This score is an educational analytical feature "
    "and does not constitute financial advice."
)


# Load the saved profile.
profile = get_financial_profile()


st.subheader("Financial Profile")


with st.form(
    key="financial_profile_form",
    clear_on_submit=False,
):
    form_column1, form_column2 = st.columns(2)

    with form_column1:
        cash_savings = st.number_input(
            label="Cash and Savings Balance (€)",
            min_value=0.00,
            value=float(profile["cash_savings"]),
            step=100.00,
            format="%.2f",
        )

        outstanding_debt = st.number_input(
            label="Outstanding Debt (€)",
            min_value=0.00,
            value=float(profile["outstanding_debt"]),
            step=100.00,
            format="%.2f",
        )

    with form_column2:
        monthly_debt_payment = st.number_input(
            label="Monthly Debt Payment (€)",
            min_value=0.00,
            value=float(profile["monthly_debt_payment"]),
            step=10.00,
            format="%.2f",
        )

        emergency_target_months = st.number_input(
            label="Emergency-Fund Target in Months",
            min_value=1,
            max_value=24,
            value=int(profile["emergency_target_months"]),
            step=1,
        )

    save_profile_button = st.form_submit_button(
        label="Save Financial Profile",
        type="primary",
    )


if save_profile_button:
    try:
        save_financial_profile(
            cash_savings=float(cash_savings),
            outstanding_debt=float(outstanding_debt),
            monthly_debt_payment=float(
                monthly_debt_payment
            ),
            emergency_target_months=int(
                emergency_target_months
            ),
        )

        st.success(
            "Financial profile saved successfully."
        )

        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            f"The financial profile could not be saved: {error}"
        )


st.divider()


# Reload the saved profile.
profile = get_financial_profile()

monthly_summary = get_monthly_summary()
transaction_records = get_all_transactions()
investment_records = get_all_investments()


# ---------------------------------------------------------
# Calculate current investment value.
# ---------------------------------------------------------

total_investment_value = 0.0

for investment in investment_records:
    quantity = float(investment["quantity"])
    current_price = float(investment["current_price"])

    total_investment_value += (
        quantity * current_price
    )


# ---------------------------------------------------------
# Calculate average monthly expenses.
# ---------------------------------------------------------

average_monthly_expenses = float(
    monthly_summary["expenses"]
)

investment_contribution = 0.0


if transaction_records:
    transactions_df = pd.DataFrame(
        transaction_records
    )

    transactions_df["transaction_date"] = (
        pd.to_datetime(
            transactions_df["transaction_date"],
            errors="coerce",
        )
    )

    transactions_df["amount"] = pd.to_numeric(
        transactions_df["amount"],
        errors="coerce",
    ).fillna(0)

    expense_transactions_df = transactions_df[
        transactions_df["transaction_type"]
        == "Expense"
    ].copy()

    expense_transactions_df = expense_transactions_df[
        expense_transactions_df[
            "transaction_date"
        ].notna()
    ]

    if not expense_transactions_df.empty:
        expense_transactions_df["month"] = (
            expense_transactions_df[
                "transaction_date"
            ].dt.to_period("M")
        )

        monthly_expense_history = (
            expense_transactions_df.groupby(
                "month"
            )["amount"]
            .sum()
            .sort_index()
        )

        # Use up to the most recent three months.
        average_monthly_expenses = float(
            monthly_expense_history.tail(3).mean()
        )

        current_month = (
            pd.Timestamp.today().to_period("M")
        )

        current_month_expenses_df = (
            expense_transactions_df[
                expense_transactions_df["month"]
                == current_month
            ]
        )

        investment_contribution = float(
            current_month_expenses_df.loc[
                current_month_expenses_df["category"]
                == "Investment Contribution",
                "amount",
            ].sum()
        )


# ---------------------------------------------------------
# Calculate financial indicators.
# ---------------------------------------------------------

monthly_income = float(
    monthly_summary["income"]
)

monthly_expenses = float(
    monthly_summary["expenses"]
)

monthly_savings = float(
    monthly_summary["savings"]
)

cash_savings = float(
    profile["cash_savings"]
)

outstanding_debt = float(
    profile["outstanding_debt"]
)

monthly_debt_payment = float(
    profile["monthly_debt_payment"]
)


net_worth = (
    cash_savings
    + total_investment_value
    - outstanding_debt
)


if monthly_income > 0:
    savings_rate = (
        monthly_savings / monthly_income
    ) * 100

    debt_to_income_ratio = (
        monthly_debt_payment / monthly_income
    ) * 100

    investment_rate = (
        investment_contribution / monthly_income
    ) * 100

else:
    savings_rate = 0.0
    debt_to_income_ratio = 0.0
    investment_rate = 0.0


if average_monthly_expenses > 0:
    emergency_fund_coverage = (
        cash_savings / average_monthly_expenses
    )
else:
    emergency_fund_coverage = 0.0


emergency_target_amount = (
    average_monthly_expenses
    * int(profile["emergency_target_months"])
)


emergency_fund_gap = max(
    emergency_target_amount - cash_savings,
    0,
)


# ---------------------------------------------------------
# Calculate financial health score.
# Maximum score: 100
# ---------------------------------------------------------

financial_health_score = 0


# Savings rate: maximum 30 points.
if savings_rate >= 20:
    savings_score = 30
elif savings_rate >= 10:
    savings_score = 20
elif savings_rate >= 0:
    savings_score = 10
else:
    savings_score = 0


# Emergency fund: maximum 30 points.
if emergency_fund_coverage >= 6:
    emergency_score = 30
elif emergency_fund_coverage >= 3:
    emergency_score = 20
elif emergency_fund_coverage >= 1:
    emergency_score = 10
else:
    emergency_score = 0


# Debt-to-income ratio: maximum 20 points.
if monthly_income <= 0:
    debt_score = 0
elif debt_to_income_ratio <= 20:
    debt_score = 20
elif debt_to_income_ratio <= 35:
    debt_score = 15
elif debt_to_income_ratio <= 50:
    debt_score = 5
else:
    debt_score = 0


# Net worth: maximum 10 points.
if net_worth >= 0:
    net_worth_score = 10
else:
    net_worth_score = 0


# Investment rate: maximum 10 points.
if investment_rate >= 10:
    investment_score = 10
elif investment_rate >= 5:
    investment_score = 5
else:
    investment_score = 0


financial_health_score = (
    savings_score
    + emergency_score
    + debt_score
    + net_worth_score
    + investment_score
)


if financial_health_score >= 80:
    health_status = "Strong"
elif financial_health_score >= 60:
    health_status = "Good"
elif financial_health_score >= 40:
    health_status = "Developing"
else:
    health_status = "Needs Attention"


# ---------------------------------------------------------
# Display the dashboard.
# ---------------------------------------------------------

st.subheader("Financial Health Summary")


metric_column1, metric_column2, metric_column3, metric_column4 = (
    st.columns(4)
)


with metric_column1:
    st.metric(
        label="Net Worth",
        value=f"€{net_worth:,.2f}",
    )


with metric_column2:
    st.metric(
        label="Savings Rate",
        value=f"{savings_rate:.1f}%",
    )


with metric_column3:
    st.metric(
        label="Emergency-Fund Coverage",
        value=f"{emergency_fund_coverage:.1f} months",
    )


with metric_column4:
    if monthly_income > 0:
        debt_ratio_display = (
            f"{debt_to_income_ratio:.1f}%"
        )
    else:
        debt_ratio_display = "N/A"

    st.metric(
        label="Debt-to-Income Ratio",
        value=debt_ratio_display,
    )


second_metric_column1, second_metric_column2, (
    second_metric_column3
), second_metric_column4 = st.columns(4)


with second_metric_column1:
    st.metric(
        label="Cash and Savings",
        value=f"€{cash_savings:,.2f}",
    )


with second_metric_column2:
    st.metric(
        label="Investment Value",
        value=f"€{total_investment_value:,.2f}",
    )


with second_metric_column3:
    st.metric(
        label="Average Monthly Expenses",
        value=f"€{average_monthly_expenses:,.2f}",
    )


with second_metric_column4:
    st.metric(
        label="Investment Rate",
        value=f"{investment_rate:.1f}%",
    )


st.divider()


# Financial health gauge.
gauge_figure = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=financial_health_score,
        title={
            "text": (
                f"Financial Health Score — "
                f"{health_status}"
            )
        },
        gauge={
            "axis": {
                "range": [0, 100],
            }
        },
    )
)


gauge_figure.update_layout(
    height=350,
)


st.plotly_chart(
    gauge_figure,
    use_container_width=True,
)


# ---------------------------------------------------------
# Score explanation.
# ---------------------------------------------------------

st.subheader("Score Breakdown")


score_breakdown_df = pd.DataFrame(
    [
        {
            "Indicator": "Savings Rate",
            "Score": savings_score,
            "Maximum Score": 30,
        },
        {
            "Indicator": "Emergency Fund",
            "Score": emergency_score,
            "Maximum Score": 30,
        },
        {
            "Indicator": "Debt-to-Income",
            "Score": debt_score,
            "Maximum Score": 20,
        },
        {
            "Indicator": "Net Worth",
            "Score": net_worth_score,
            "Maximum Score": 10,
        },
        {
            "Indicator": "Investment Rate",
            "Score": investment_score,
            "Maximum Score": 10,
        },
    ]
)


st.dataframe(
    score_breakdown_df,
    hide_index=True,
    use_container_width=True,
)


# ---------------------------------------------------------
# Emergency-fund target.
# ---------------------------------------------------------

st.subheader("Emergency-Fund Target")


target_column1, target_column2, target_column3 = (
    st.columns(3)
)


with target_column1:
    st.metric(
        label="Target Coverage",
        value=(
            f"{profile['emergency_target_months']} months"
        ),
    )


with target_column2:
    st.metric(
        label="Target Amount",
        value=f"€{emergency_target_amount:,.2f}",
    )


with target_column3:
    st.metric(
        label="Remaining Gap",
        value=f"€{emergency_fund_gap:,.2f}",
    )


if emergency_target_amount > 0:
    target_progress = min(
        cash_savings / emergency_target_amount,
        1.0,
    )

    st.progress(
        target_progress,
        text=(
            f"{target_progress * 100:.1f}% "
            "of the emergency-fund target completed"
        ),
    )


# ---------------------------------------------------------
# Generate financial observations.
# ---------------------------------------------------------

st.subheader("Financial Observations")


observations = []


if monthly_income <= 0:
    observations.append(
        "Add an income transaction for the current month "
        "to calculate income-based indicators."
    )


if savings_rate < 10:
    observations.append(
        "The current savings rate is below 10%. "
        "Review discretionary spending categories and "
        "consider setting a monthly savings target."
    )


if emergency_fund_coverage < 3:
    observations.append(
        "Cash savings currently cover fewer than three "
        "months of average expenses. Building an emergency "
        "reserve may improve financial resilience."
    )


if (
    monthly_income > 0
    and debt_to_income_ratio > 35
):
    observations.append(
        "Monthly debt payments exceed 35% of income. "
        "Consider reviewing repayment priorities and "
        "avoiding additional high-cost debt."
    )


if net_worth < 0:
    observations.append(
        "Outstanding debt is greater than cash savings "
        "and current investment value, resulting in "
        "negative net worth."
    )


if investment_rate < 5 and monthly_savings > 0:
    observations.append(
        "Investment contributions are below 5% of income. "
        "A regular contribution could be considered after "
        "essential expenses and emergency savings."
    )


if not observations:
    st.success(
        "The current indicators are generally healthy. "
        "Continue monitoring spending, savings and "
        "investment concentration."
    )

else:
    for observation in observations:
        st.info(observation)