from datetime import date

import pandas as pd
import streamlit as st

from src.database import (
    get_all_investments,
    get_monthly_summary,
    get_recent_transactions,
    initialise_database,
)

from src.ui import (
    apply_global_styles,
    render_brand_header,
)


st.set_page_config(
    page_title="FinanceCanvas | Financial Intelligence",
    page_icon="💶",
    layout="wide",
    initial_sidebar_state="expanded",
)


apply_global_styles()
initialise_database()


def format_currency(amount):
    """
    Format a numeric value as euro currency.
    """

    return f"€{float(amount):,.2f}"


# Load dashboard information.
summary = get_monthly_summary()
recent_transactions = get_recent_transactions(
    limit=7
)
investment_records = get_all_investments()


# Calculate portfolio value.
portfolio_value = sum(
    float(investment["quantity"])
    * float(investment["current_price"])
    for investment in investment_records
)


# Calculate savings rate.
if summary["income"] > 0:
    savings_rate = (
        summary["savings"]
        / summary["income"]
        * 100
    )
else:
    savings_rate = 0.0


# Brand heading.
render_brand_header(
    title="FinanceCanvas",
    subtitle=(
        "Track spending, manage budgets, monitor "
        "investments and understand financial health."
    ),
)


st.caption(
    f"Dashboard summary for "
    f"{date.today().strftime('%B %Y')}"
)


# Main financial metrics.
metric_column1, metric_column2, metric_column3, (
    metric_column4
) = st.columns(4)


with metric_column1:
    st.metric(
        label="Monthly Income",
        value=format_currency(
            summary["income"]
        ),
    )


with metric_column2:
    st.metric(
        label="Monthly Expenses",
        value=format_currency(
            summary["expenses"]
        ),
    )


with metric_column3:
    st.metric(
        label="Monthly Savings",
        value=format_currency(
            summary["savings"]
        ),
    )


with metric_column4:
    st.metric(
        label="Portfolio Value",
        value=format_currency(
            portfolio_value
        ),
    )


st.write("")


summary_column1, summary_column2 = st.columns(2)


with summary_column1:
    st.subheader("Savings Performance")

    if summary["income"] > 0:
        progress_value = max(
            min(savings_rate / 100, 1.0),
            0.0,
        )

        st.metric(
            label="Current Savings Rate",
            value=f"{savings_rate:.1f}%",
        )

        st.progress(
            progress_value,
            text=(
                f"{savings_rate:.1f}% of monthly "
                "income retained"
            ),
        )

        if savings_rate >= 20:
            st.success(
                "Savings are currently above the "
                "20% benchmark used by FinanceCanvas."
            )

        elif savings_rate >= 10:
            st.info(
                "Savings are positive. Review flexible "
                "expenses for additional improvement."
            )

        else:
            st.warning(
                "The savings rate is below 10%."
            )

    else:
        st.info(
            "Add current-month income to calculate "
            "your savings performance."
        )


with summary_column2:
    st.subheader("Application Coverage")

    st.write(
        """
        FinanceCanvas currently combines personal-finance
        operations and data analytics in one application.
        """
    )

    coverage_data = {
        "Capability": [
            "Transaction Management",
            "Budget Monitoring",
            "Statement Import",
            "Investment Analytics",
            "Financial Health",
            "Expense Forecasting",
        ],
        "Status": [
            "Operational",
            "Operational",
            "Operational",
            "Operational",
            "Operational",
            "Operational",
        ],
    }

    st.dataframe(
        pd.DataFrame(coverage_data),
        hide_index=True,
        use_container_width=True,
    )


st.divider()


st.subheader("Recent Transactions")


if recent_transactions:
    transactions_df = pd.DataFrame(
        recent_transactions
    )

    transactions_df["transaction_date"] = (
        pd.to_datetime(
            transactions_df["transaction_date"],
            errors="coerce",
        ).dt.strftime("%d/%m/%Y")
    )

    transactions_df["amount"] = (
        transactions_df["amount"].apply(
            format_currency
        )
    )

    transactions_df = transactions_df.rename(
        columns={
            "transaction_date": "Date",
            "transaction_type": "Type",
            "category": "Category",
            "description": "Description",
            "amount": "Amount",
            "payment_method": "Payment Method",
        }
    )

    st.dataframe(
        transactions_df,
        hide_index=True,
        use_container_width=True,
    )

else:
    st.info(
        "No transactions are available."
    )


st.divider()


st.subheader("FinanceCanvas Features")


# Style homepage feature buttons like large cards.
st.markdown(
    """
    <style>
    div[data-testid="stButton"] > button {
        min-height: 155px;
        white-space: normal;
        text-align: left;
        justify-content: flex-start;
        align-items: flex-start;
        padding: 24px;
        border: 1px solid #DCE3EC;
        border-radius: 16px;
        background-color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        font-size: 1rem;
        line-height: 1.6;
        transition:
            transform 0.15s ease,
            box-shadow 0.15s ease,
            border-color 0.15s ease;
    }

    div[data-testid="stButton"] > button:hover {
        border-color: #2563EB;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.13);
        transform: translateY(-3px);
    }

    div[data-testid="stButton"] > button:focus {
        border-color: #2563EB;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def feature_navigation_button(
    label,
    destination,
    key,
):
    """
    Display a feature card and open its associated page.
    """

    if st.button(
        label=label,
        key=key,
        use_container_width=True,
    ):
        st.switch_page(destination)


# First row of feature cards.
feature_column1, feature_column2, feature_column3 = (
    st.columns(3)
)


with feature_column1:
    feature_navigation_button(
        label=(
            "📊 **Spending Intelligence** — "
            "Record, filter and analyse income and "
            "expenses using Python, Pandas and SQLite."
        ),
        destination="pages/2_Transaction_History.py",
        key="open_spending_intelligence",
    )


with feature_column2:
    feature_navigation_button(
        label=(
            "🎯 **Budget Management** — "
            "Compare planned budgets against actual "
            "spending and identify overspending risks."
        ),
        destination="pages/3_Budget_Tracker.py",
        key="open_budget_management",
    )


with feature_column3:
    feature_navigation_button(
        label=(
            "📈 **Investment Analytics** — "
            "Monitor portfolio value, returns, asset "
            "allocation and unrealised performance."
        ),
        destination="pages/5_Investment_Portfolio.py",
        key="open_investment_analytics",
    )


st.write("")


# Second row of feature cards.
feature_column4, feature_column5, feature_column6 = (
    st.columns(3)
)


with feature_column4:
    feature_navigation_button(
        label=(
            "📥 **Data Automation** — "
            "Extract, validate and import PDF bank "
            "statements with duplicate detection."
        ),
        destination="pages/4_Import_Statement.py",
        key="open_data_automation",
    )


with feature_column5:
    feature_navigation_button(
        label=(
            "🩺 **Financial Health** — "
            "Calculate net worth, savings rate, emergency "
            "coverage and debt indicators."
        ),
        destination="pages/6_Financial_Health.py",
        key="open_financial_health",
    )


with feature_column6:
    feature_navigation_button(
        label=(
            "🔮 **Forecasting** — "
            "Forecast future expenses and generate "
            "automated financial observations."
        ),
        destination="pages/7_Forecast_and_Insights.py",
        key="open_forecasting",
    )


st.divider()


st.caption(
    "FinanceCanvas is an educational financial analytics "
    "portfolio project. It does not provide regulated "
    "financial advice."
)

st.caption(
    "FinanceCanvas is an educational financial analytics "
    "portfolio project. It does not provide regulated "
    "financial advice."
)