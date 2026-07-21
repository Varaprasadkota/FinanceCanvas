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


feature_column1, feature_column2, feature_column3 = (
    st.columns(3)
)


with feature_column1:
    st.markdown(
        """
        <div class="feature-card">
            <h4>📊 Spending Intelligence</h4>
            <p>
                Record, filter and analyse income and
                expenses using Python, Pandas and SQLite.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


with feature_column2:
    st.markdown(
        """
        <div class="feature-card">
            <h4>🎯 Budget Management</h4>
            <p>
                Compare planned budgets against actual
                spending and identify overspending risks.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


with feature_column3:
    st.markdown(
        """
        <div class="feature-card">
            <h4>📈 Investment Analytics</h4>
            <p>
                Monitor portfolio value, returns,
                allocation and unrealised performance.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.write("")


feature_column4, feature_column5, feature_column6 = (
    st.columns(3)
)


with feature_column4:
    st.markdown(
        """
        <div class="feature-card">
            <h4>📥 Data Automation</h4>
            <p>
                Clean, validate and import CSV bank
                statements with duplicate detection.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


with feature_column5:
    st.markdown(
        """
        <div class="feature-card">
            <h4>🩺 Financial Health</h4>
            <p>
                Calculate net worth, savings rate,
                emergency coverage and debt indicators.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


with feature_column6:
    st.markdown(
        """
        <div class="feature-card">
            <h4>🔮 Forecasting</h4>
            <p>
                Forecast future expenses and generate
                automated financial observations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.divider()


st.caption(
    "FinanceCanvas is an educational financial analytics "
    "portfolio project. It does not provide regulated "
    "financial advice."
)