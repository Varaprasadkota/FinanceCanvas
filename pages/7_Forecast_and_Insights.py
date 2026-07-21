from datetime import date
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# Locate the main FinanceCanvas project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from src.database import (
    get_all_transactions,
    get_budgets_for_month,
    initialise_database,
)
from src.ui import apply_global_styles

st.set_page_config(
    page_title="Forecast and Insights | FinanceCanvas",
    page_icon="🔮",
    layout="wide",
)
apply_global_styles()

initialise_database()


st.title("🔮 Forecast and Automated Insights")

st.write(
    """
    Analyse historical spending and estimate future
    expenses, savings and potential budget risks.
    """
)

st.caption(
    "Forecasts are estimates based on recorded transaction "
    "history and should not be treated as financial advice."
)


# ---------------------------------------------------------
# Load and prepare transaction data.
# ---------------------------------------------------------

transaction_records = get_all_transactions()


if not transaction_records:
    st.info(
        "No transactions are available. Add or import "
        "transactions before generating forecasts."
    )

    st.stop()


transactions_df = pd.DataFrame(
    transaction_records
)


transactions_df["transaction_date"] = pd.to_datetime(
    transactions_df["transaction_date"],
    errors="coerce",
)


transactions_df["amount"] = pd.to_numeric(
    transactions_df["amount"],
    errors="coerce",
).fillna(0)


transactions_df = transactions_df[
    transactions_df["transaction_date"].notna()
].copy()


if transactions_df.empty:
    st.error(
        "The stored transaction dates could not be analysed."
    )

    st.stop()


transactions_df["month"] = (
    transactions_df["transaction_date"].dt.to_period("M")
)


income_df = transactions_df[
    transactions_df["transaction_type"] == "Income"
].copy()


expenses_df = transactions_df[
    transactions_df["transaction_type"] == "Expense"
].copy()


if expenses_df.empty:
    st.info(
        "At least one expense transaction is required "
        "to generate an expense forecast."
    )

    st.stop()


# ---------------------------------------------------------
# Create complete monthly totals.
# ---------------------------------------------------------

monthly_expenses = (
    expenses_df.groupby("month")["amount"]
    .sum()
    .sort_index()
)


first_month = monthly_expenses.index.min()
current_month = pd.Timestamp.today().to_period("M")


complete_month_index = pd.period_range(
    start=first_month,
    end=current_month,
    freq="M",
)


monthly_expenses = monthly_expenses.reindex(
    complete_month_index,
    fill_value=0,
)


monthly_income = (
    income_df.groupby("month")["amount"]
    .sum()
    .sort_index()
    .reindex(
        complete_month_index,
        fill_value=0,
    )
)


monthly_history_df = pd.DataFrame(
    {
        "Month": complete_month_index,
        "Expenses": monthly_expenses.values,
        "Income": monthly_income.values,
    }
)


monthly_history_df["Savings"] = (
    monthly_history_df["Income"]
    - monthly_history_df["Expenses"]
)


# ---------------------------------------------------------
# Forecast calculation.
# ---------------------------------------------------------

forecast_months = 3
history_count = len(monthly_expenses)


future_periods = pd.period_range(
    start=current_month + 1,
    periods=forecast_months,
    freq="M",
)


expense_values = monthly_expenses.values.astype(float)
time_values = np.arange(history_count)


if history_count >= 3:
    # Fit a simple linear trend to monthly spending.
    slope, intercept = np.polyfit(
        time_values,
        expense_values,
        1,
    )

    future_time_values = np.arange(
        history_count,
        history_count + forecast_months,
    )

    forecast_expenses = (
        slope * future_time_values
        + intercept
    )

    forecast_method = "Linear spending trend"

elif history_count == 2:
    # Use the average when only two months exist.
    forecast_expenses = np.repeat(
        expense_values.mean(),
        forecast_months,
    )

    forecast_method = "Two-month average"

else:
    # Use the available month when only one month exists.
    forecast_expenses = np.repeat(
        expense_values[0],
        forecast_months,
    )

    forecast_method = "Current-month estimate"


# Expenses cannot be negative.
forecast_expenses = np.maximum(
    forecast_expenses,
    0,
)


# Use the most recent three months to estimate income.
recent_income_values = monthly_income.tail(3)


if recent_income_values.sum() > 0:
    estimated_monthly_income = float(
        recent_income_values[
            recent_income_values > 0
        ].mean()
    )
else:
    estimated_monthly_income = 0.0


forecast_df = pd.DataFrame(
    {
        "Month": future_periods,
        "Forecast Expenses": forecast_expenses,
    }
)


forecast_df["Estimated Income"] = (
    estimated_monthly_income
)


forecast_df["Forecast Savings"] = (
    forecast_df["Estimated Income"]
    - forecast_df["Forecast Expenses"]
)


# ---------------------------------------------------------
# Summary calculations.
# ---------------------------------------------------------

current_month_expenses = float(
    monthly_expenses.iloc[-1]
)


previous_month_expenses = (
    float(monthly_expenses.iloc[-2])
    if history_count >= 2
    else 0.0
)


average_monthly_expenses = float(
    monthly_expenses.tail(3).mean()
)


next_month_forecast = float(
    forecast_df.iloc[0]["Forecast Expenses"]
)


next_month_savings = float(
    forecast_df.iloc[0]["Forecast Savings"]
)


if previous_month_expenses > 0:
    monthly_change_percentage = (
        (
            current_month_expenses
            - previous_month_expenses
        )
        / previous_month_expenses
        * 100
    )
else:
    monthly_change_percentage = 0.0


st.subheader("Forecast Summary")


metric_column1, metric_column2, metric_column3, metric_column4 = (
    st.columns(4)
)


with metric_column1:
    st.metric(
        label="Current-Month Expenses",
        value=f"€{current_month_expenses:,.2f}",
        delta=(
            f"{monthly_change_percentage:.1f}% "
            "vs previous month"
            if history_count >= 2
            else None
        ),
        delta_color="inverse",
    )


with metric_column2:
    st.metric(
        label="Three-Month Average",
        value=f"€{average_monthly_expenses:,.2f}",
    )


with metric_column3:
    st.metric(
        label="Next-Month Forecast",
        value=f"€{next_month_forecast:,.2f}",
    )


with metric_column4:
    st.metric(
        label="Estimated Next-Month Savings",
        value=f"€{next_month_savings:,.2f}",
    )


st.info(
    f"Forecast method used: {forecast_method}"
)


if history_count < 3:
    st.warning(
        "The forecast currently has limited historical data. "
        "Accuracy should improve after recording at least "
        "three complete months of transactions."
    )


# ---------------------------------------------------------
# Historical and forecast chart.
# ---------------------------------------------------------

st.subheader("Monthly Expense Forecast")


historical_chart_df = monthly_history_df[
    [
        "Month",
        "Expenses",
    ]
].copy()


historical_chart_df["Series"] = "Actual Expenses"

historical_chart_df = historical_chart_df.rename(
    columns={
        "Expenses": "Amount",
    }
)


future_chart_df = forecast_df[
    [
        "Month",
        "Forecast Expenses",
    ]
].copy()


future_chart_df["Series"] = "Forecast Expenses"

future_chart_df = future_chart_df.rename(
    columns={
        "Forecast Expenses": "Amount",
    }
)


combined_chart_df = pd.concat(
    [
        historical_chart_df,
        future_chart_df,
    ],
    ignore_index=True,
)


combined_chart_df["Month"] = (
    combined_chart_df["Month"]
    .astype(str)
)


forecast_chart = px.line(
    combined_chart_df,
    x="Month",
    y="Amount",
    color="Series",
    markers=True,
    title="Actual and Forecast Monthly Expenses",
    labels={
        "Amount": "Amount (€)",
    },
)


st.plotly_chart(
    forecast_chart,
    use_container_width=True,
)


# ---------------------------------------------------------
# Forecast table.
# ---------------------------------------------------------

st.subheader("Three-Month Forecast")


forecast_display_df = forecast_df.copy()


forecast_display_df["Month"] = (
    forecast_display_df["Month"]
    .dt.strftime("%B %Y")
)


currency_columns = [
    "Forecast Expenses",
    "Estimated Income",
    "Forecast Savings",
]


for column in currency_columns:
    forecast_display_df[column] = (
        forecast_display_df[column].apply(
            lambda value: f"€{value:,.2f}"
        )
    )


st.dataframe(
    forecast_display_df,
    hide_index=True,
    use_container_width=True,
)


# ---------------------------------------------------------
# Category-level forecast.
# ---------------------------------------------------------

st.subheader("Forecast by Expense Category")


recent_start_month = current_month - 2


recent_category_expenses_df = expenses_df[
    expenses_df["month"] >= recent_start_month
].copy()


category_monthly_df = (
    recent_category_expenses_df.groupby(
        [
            "category",
            "month",
        ]
    )["amount"]
    .sum()
    .reset_index()
)


category_forecast_records = []


for category in sorted(
    expenses_df["category"].dropna().unique()
):
    category_data = category_monthly_df[
        category_monthly_df["category"]
        == category
    ]


    category_period_series = (
        category_data.set_index("month")["amount"]
        .reindex(
            pd.period_range(
                start=recent_start_month,
                end=current_month,
                freq="M",
            ),
            fill_value=0,
        )
    )


    category_forecast = float(
        category_period_series.mean()
    )


    current_category_spending = float(
        category_period_series.iloc[-1]
    )


    category_forecast_records.append(
        {
            "Category": category,
            "Current Month": current_category_spending,
            "Next-Month Forecast": category_forecast,
        }
    )


category_forecast_df = pd.DataFrame(
    category_forecast_records
)


category_forecast_df = (
    category_forecast_df.sort_values(
        "Next-Month Forecast",
        ascending=False,
    )
)


category_chart = px.bar(
    category_forecast_df,
    x="Category",
    y="Next-Month Forecast",
    title="Estimated Next-Month Spending by Category",
    labels={
        "Next-Month Forecast": "Forecast Amount (€)",
    },
)


category_chart.update_layout(
    xaxis_tickangle=-35,
)


st.plotly_chart(
    category_chart,
    use_container_width=True,
)


category_display_df = category_forecast_df.copy()


category_display_df["Current Month"] = (
    category_display_df["Current Month"].apply(
        lambda value: f"€{value:,.2f}"
    )
)


category_display_df["Next-Month Forecast"] = (
    category_display_df[
        "Next-Month Forecast"
    ].apply(
        lambda value: f"€{value:,.2f}"
    )
)


st.dataframe(
    category_display_df,
    hide_index=True,
    use_container_width=True,
)


# ---------------------------------------------------------
# Budget-risk analysis.
# ---------------------------------------------------------

st.subheader("Potential Budget Risks")


budget_records = get_budgets_for_month(
    current_month.strftime("%Y-%m")
)


budget_risk_records = []


if budget_records:
    budgets_df = pd.DataFrame(
        budget_records
    )


    budget_forecast_df = pd.merge(
        category_forecast_df,
        budgets_df,
        left_on="Category",
        right_on="category",
        how="inner",
    )


    for _, row in budget_forecast_df.iterrows():
        budget_amount = float(
            row["budget_amount"]
        )

        expected_spending = float(
            row["Next-Month Forecast"]
        )


        if budget_amount > 0:
            expected_usage = (
                expected_spending
                / budget_amount
                * 100
            )
        else:
            expected_usage = 0


        if expected_spending > budget_amount:
            risk_status = "Likely Over Budget"

        elif expected_usage >= 80:
            risk_status = "Near Budget Limit"

        else:
            risk_status = "Low Risk"


        budget_risk_records.append(
            {
                "Category": row["Category"],
                "Budget": budget_amount,
                "Forecast Spending": expected_spending,
                "Expected Usage": expected_usage,
                "Risk": risk_status,
            }
        )


if budget_risk_records:
    budget_risk_df = pd.DataFrame(
        budget_risk_records
    )


    budget_risk_df = budget_risk_df.sort_values(
        "Expected Usage",
        ascending=False,
    )


    budget_risk_display_df = (
        budget_risk_df.copy()
    )


    budget_risk_display_df["Budget"] = (
        budget_risk_display_df["Budget"].apply(
            lambda value: f"€{value:,.2f}"
        )
    )


    budget_risk_display_df[
        "Forecast Spending"
    ] = budget_risk_display_df[
        "Forecast Spending"
    ].apply(
        lambda value: f"€{value:,.2f}"
    )


    budget_risk_display_df[
        "Expected Usage"
    ] = budget_risk_display_df[
        "Expected Usage"
    ].apply(
        lambda value: f"{value:.1f}%"
    )


    st.dataframe(
        budget_risk_display_df,
        hide_index=True,
        use_container_width=True,
    )


    high_risk_df = budget_risk_df[
        budget_risk_df["Risk"]
        == "Likely Over Budget"
    ]


    if not high_risk_df.empty:
        st.error(
            f"{len(high_risk_df)} category or categories "
            "may exceed their current budget based on "
            "recent spending patterns."
        )

else:
    st.info(
        "No matching category budgets are available for "
        "budget-risk analysis. Add current-month budgets "
        "through the Budget Tracker."
    )


# ---------------------------------------------------------
# Automated insights.
# ---------------------------------------------------------

st.subheader("Automated Financial Insights")


insights = []


if history_count >= 2:
    if monthly_change_percentage > 20:
        insights.append(
            f"Expenses increased by "
            f"{monthly_change_percentage:.1f}% compared "
            "with the previous month."
        )

    elif monthly_change_percentage < -10:
        insights.append(
            f"Expenses decreased by "
            f"{abs(monthly_change_percentage):.1f}% "
            "compared with the previous month."
        )


if not category_forecast_df.empty:
    top_category = category_forecast_df.iloc[0]

    insights.append(
        f"{top_category['Category']} is forecast to be "
        f"the largest expense category next month at "
        f"approximately "
        f"€{top_category['Next-Month Forecast']:,.2f}."
    )


if estimated_monthly_income > 0:
    if next_month_savings < 0:
        insights.append(
            "Forecast expenses are greater than estimated "
            "income, which may result in negative savings "
            "next month."
        )

    elif (
        next_month_savings
        / estimated_monthly_income
        < 0.10
    ):
        insights.append(
            "Forecast savings are below 10% of estimated "
            "income. Review flexible spending categories."
        )

    else:
        forecast_savings_rate = (
            next_month_savings
            / estimated_monthly_income
            * 100
        )

        insights.append(
            f"The estimated next-month savings rate is "
            f"{forecast_savings_rate:.1f}%."
        )


if next_month_forecast > average_monthly_expenses * 1.15:
    insights.append(
        "Next-month expenses are forecast to be more than "
        "15% above the recent monthly average."
    )


if not insights:
    insights.append(
        "More historical transactions are required to "
        "generate detailed financial observations."
    )


for insight in insights:
    st.info(insight)


# ---------------------------------------------------------
# Export forecast.
# ---------------------------------------------------------

st.subheader("Export Forecast")


forecast_export_df = forecast_df.copy()


forecast_export_df["Month"] = (
    forecast_export_df["Month"].astype(str)
)


forecast_csv = forecast_export_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Forecast CSV",
    data=forecast_csv,
    file_name="FinanceCanvas_three_month_forecast.csv",
    mime="text/csv",
    type="primary",
)