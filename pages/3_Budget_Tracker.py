from datetime import date
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


# Find the main FinanceCanvas project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allow imports from the src folder.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from src.database import (
    get_budgets_for_month,
    get_expenses_by_category,
    initialise_database,
    save_budget,
)
from src.ui import apply_global_styles

st.set_page_config(
    page_title="Budget Tracker | FinanceCanvas",
    page_icon="🎯",
    layout="wide",
)
apply_global_styles()

# Ensure all database tables exist.
initialise_database()


st.title("🎯 Monthly Budget Tracker")

st.write(
    """
    Set monthly spending limits and compare them
    with your actual expenses.
    """
)


expense_categories = [
    "Rent",
    "Groceries",
    "Transport",
    "Loan EMI",
    "Family Support",
    "Utilities",
    "Insurance",
    "Entertainment",
    "Shopping",
    "Healthcare",
    "Education",
    "Investment Contribution",
    "Other Expense",
]


# Select a date representing the required budget month.
selected_date = st.date_input(
    label="Select Budget Month",
    value=date.today().replace(day=1),
    format="DD/MM/YYYY",
)

selected_month = selected_date.strftime("%Y-%m")
selected_month_name = selected_date.strftime("%B %Y")


st.caption(
    f"Budget analysis for {selected_month_name}"
)


st.subheader("Set or Update Budget")


with st.form(
    key="budget_form",
    clear_on_submit=False,
):
    budget_category = st.selectbox(
        label="Expense Category",
        options=expense_categories,
    )

    budget_amount = st.number_input(
        label="Monthly Budget (€)",
        min_value=0.00,
        value=0.00,
        step=10.00,
        format="%.2f",
    )

    save_budget_button = st.form_submit_button(
        label="Save Budget",
        type="primary",
    )


if save_budget_button:
    try:
        save_budget(
            budget_month=selected_month,
            category=budget_category,
            budget_amount=float(budget_amount),
        )

        st.success(
            f"{budget_category} budget of "
            f"€{budget_amount:,.2f} saved for "
            f"{selected_month_name}."
        )

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            f"The budget could not be saved: {error}"
        )


st.divider()


# Retrieve budgets and actual expenses.
budget_records = get_budgets_for_month(
    selected_month
)

expense_records = get_expenses_by_category(
    selected_month
)


# Convert database results into DataFrames.
budgets_df = pd.DataFrame(
    budget_records,
    columns=["category", "budget_amount"],
)

expenses_df = pd.DataFrame(
    expense_records,
    columns=["category", "actual_spending"],
)


# Combine budget and expense information.
budget_analysis_df = pd.merge(
    budgets_df,
    expenses_df,
    on="category",
    how="outer",
)


# Replace missing values with zero.
budget_analysis_df["budget_amount"] = (
    budget_analysis_df["budget_amount"]
    .fillna(0)
    .astype(float)
)

budget_analysis_df["actual_spending"] = (
    budget_analysis_df["actual_spending"]
    .fillna(0)
    .astype(float)
)


# Calculate remaining budget.
budget_analysis_df["remaining"] = (
    budget_analysis_df["budget_amount"]
    - budget_analysis_df["actual_spending"]
)


# Calculate percentage of budget used.
budget_analysis_df["budget_used_percentage"] = (
    budget_analysis_df.apply(
        lambda row: (
            row["actual_spending"]
            / row["budget_amount"]
            * 100
        )
        if row["budget_amount"] > 0
        else 0,
        axis=1,
    )
)


def calculate_status(row):
    """
    Determine the spending status for each category.
    """

    if row["budget_amount"] == 0:
        return "No Budget Set"

    if row["actual_spending"] > row["budget_amount"]:
        return "Over Budget"

    if row["budget_used_percentage"] >= 80:
        return "Near Limit"

    return "Within Budget"


budget_analysis_df["status"] = (
    budget_analysis_df.apply(
        calculate_status,
        axis=1,
    )
)


# Sort categories alphabetically.
budget_analysis_df = (
    budget_analysis_df.sort_values("category")
)


# Calculate overall totals.
total_budget = budget_analysis_df[
    "budget_amount"
].sum()

total_spent = budget_analysis_df[
    "actual_spending"
].sum()

total_remaining = total_budget - total_spent


if total_budget > 0:
    overall_budget_used = (
        total_spent / total_budget
    ) * 100
else:
    overall_budget_used = 0


st.subheader("Budget Summary")


metric_column1, metric_column2, metric_column3, metric_column4 = (
    st.columns(4)
)

with metric_column1:
    st.metric(
        label="Total Budget",
        value=f"€{total_budget:,.2f}",
    )

with metric_column2:
    st.metric(
        label="Actual Spending",
        value=f"€{total_spent:,.2f}",
    )

with metric_column3:
    st.metric(
        label="Remaining Budget",
        value=f"€{total_remaining:,.2f}",
    )

with metric_column4:
    st.metric(
        label="Budget Used",
        value=f"{overall_budget_used:.1f}%",
    )


# Show an overall progress bar.
if total_budget > 0:
    progress_value = min(
        overall_budget_used / 100,
        1.0,
    )

    st.progress(
        progress_value,
        text=(
            f"{overall_budget_used:.1f}% "
            "of the total budget used"
        ),
    )
else:
    st.info(
        "Save at least one category budget "
        "to calculate overall budget usage."
    )


st.subheader("Budget Analysis")


if budget_analysis_df.empty:
    st.info(
        "No budgets or expenses are available "
        f"for {selected_month_name}."
    )

else:
    display_df = budget_analysis_df.copy()

    display_df["budget_amount"] = (
        display_df["budget_amount"].apply(
            lambda value: f"€{value:,.2f}"
        )
    )

    display_df["actual_spending"] = (
        display_df["actual_spending"].apply(
            lambda value: f"€{value:,.2f}"
        )
    )

    display_df["remaining"] = (
        display_df["remaining"].apply(
            lambda value: f"€{value:,.2f}"
        )
    )

    display_df["budget_used_percentage"] = (
        display_df[
            "budget_used_percentage"
        ].apply(
            lambda value: f"{value:.1f}%"
        )
    )

    display_df = display_df.rename(
        columns={
            "category": "Category",
            "budget_amount": "Budget",
            "actual_spending": "Spent",
            "remaining": "Remaining",
            "budget_used_percentage": "Budget Used",
            "status": "Status",
        }
    )

    display_df = display_df[
        [
            "Category",
            "Budget",
            "Spent",
            "Remaining",
            "Budget Used",
            "Status",
        ]
    ]

    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
    )


    st.subheader("Budget vs Actual Spending")


    chart_df = budget_analysis_df[
        [
            "category",
            "budget_amount",
            "actual_spending",
        ]
    ].copy()

    chart_df = chart_df.rename(
        columns={
            "category": "Category",
            "budget_amount": "Budget",
            "actual_spending": "Actual Spending",
        }
    )

    chart_df = chart_df.melt(
        id_vars="Category",
        value_vars=[
            "Budget",
            "Actual Spending",
        ],
        var_name="Measure",
        value_name="Amount",
    )


    budget_chart = px.bar(
        chart_df,
        x="Category",
        y="Amount",
        color="Measure",
        barmode="group",
        title=(
            f"Budget vs Actual Spending — "
            f"{selected_month_name}"
        ),
        labels={
            "Amount": "Amount (€)",
        },
    )

    budget_chart.update_layout(
        xaxis_tickangle=-35,
    )

    st.plotly_chart(
        budget_chart,
        use_container_width=True,
    )


# Show categories that exceeded their budgets.
over_budget_df = budget_analysis_df[
    budget_analysis_df["status"]
    == "Over Budget"
]


if not over_budget_df.empty:
    st.error(
        f"{len(over_budget_df)} category or categories "
        "have exceeded their monthly budgets."
    )