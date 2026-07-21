from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# Find the main FinanceCanvas project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allow this page to import code from the src folder.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from src.database import (
    get_all_transactions,
    initialise_database,
)
from src.ui import apply_global_styles

st.set_page_config(
    page_title="Transaction History | FinanceCanvas",
    page_icon="📋",
    layout="wide",
)
apply_global_styles()

# Make sure the database and table exist.
initialise_database()


st.title("📋 Transaction History")

st.write(
    """
    Review, filter and export your recorded income
    and expense transactions.
    """
)


# Read all transactions from SQLite.
transaction_records = get_all_transactions()


# Stop the page when there are no transactions.
if not transaction_records:
    st.info(
        "No transactions are available. "
        "Open Add Transaction to create your first transaction."
    )

    st.stop()


# Convert the database records into a Pandas DataFrame.
transactions_df = pd.DataFrame(transaction_records)


# Convert database values into suitable data types.
transactions_df["transaction_date"] = pd.to_datetime(
    transactions_df["transaction_date"],
    errors="coerce",
)

transactions_df["amount"] = pd.to_numeric(
    transactions_df["amount"],
    errors="coerce",
).fillna(0)


st.subheader("Filters")


# Find the earliest and latest transaction dates.
earliest_date = transactions_df["transaction_date"].min().date()
latest_date = transactions_df["transaction_date"].max().date()


date_column1, date_column2 = st.columns(2)

with date_column1:
    start_date = st.date_input(
        label="Start Date",
        value=earliest_date,
        min_value=earliest_date,
        max_value=latest_date,
        format="DD/MM/YYYY",
    )

with date_column2:
    end_date = st.date_input(
        label="End Date",
        value=latest_date,
        min_value=earliest_date,
        max_value=latest_date,
        format="DD/MM/YYYY",
    )


# Create lists of available transaction types and categories.
transaction_types = sorted(
    transactions_df["transaction_type"]
    .dropna()
    .unique()
    .tolist()
)

categories = sorted(
    transactions_df["category"]
    .dropna()
    .unique()
    .tolist()
)


filter_column1, filter_column2 = st.columns(2)

with filter_column1:
    selected_types = st.multiselect(
        label="Transaction Type",
        options=transaction_types,
        default=transaction_types,
    )

with filter_column2:
    selected_categories = st.multiselect(
        label="Category",
        options=categories,
        default=categories,
    )


# Validate the selected date range.
if start_date > end_date:
    st.error(
        "Start Date cannot be later than End Date."
    )

    st.stop()


# Apply the date filter.
filtered_df = transactions_df[
    (
        transactions_df["transaction_date"].dt.date
        >= start_date
    )
    & (
        transactions_df["transaction_date"].dt.date
        <= end_date
    )
].copy()


# Apply transaction-type filtering.
if selected_types:
    filtered_df = filtered_df[
        filtered_df["transaction_type"].isin(
            selected_types
        )
    ]
else:
    filtered_df = filtered_df.iloc[0:0]


# Apply category filtering.
if selected_categories:
    filtered_df = filtered_df[
        filtered_df["category"].isin(
            selected_categories
        )
    ]
else:
    filtered_df = filtered_df.iloc[0:0]


st.divider()


# Calculate filtered totals.
filtered_income = filtered_df.loc[
    filtered_df["transaction_type"] == "Income",
    "amount",
].sum()

filtered_expenses = filtered_df.loc[
    filtered_df["transaction_type"] == "Expense",
    "amount",
].sum()

filtered_balance = filtered_income - filtered_expenses

transaction_count = len(filtered_df)


# Display summary cards.
metric_column1, metric_column2, metric_column3, metric_column4 = (
    st.columns(4)
)

with metric_column1:
    st.metric(
        label="Transactions",
        value=transaction_count,
    )

with metric_column2:
    st.metric(
        label="Income",
        value=f"€{filtered_income:,.2f}",
    )

with metric_column3:
    st.metric(
        label="Expenses",
        value=f"€{filtered_expenses:,.2f}",
    )

with metric_column4:
    st.metric(
        label="Balance",
        value=f"€{filtered_balance:,.2f}",
    )


st.subheader("Transactions")


if filtered_df.empty:
    st.warning(
        "No transactions match the selected filters."
    )

else:
    # Create a separate copy for displaying.
    display_df = filtered_df.copy()

    display_df["transaction_date"] = (
        display_df["transaction_date"].dt.strftime(
            "%d/%m/%Y"
        )
    )

    display_df["amount"] = display_df["amount"].apply(
        lambda amount: f"€{amount:,.2f}"
    )

    # Select and arrange the displayed columns.
    display_df = display_df[
        [
            "transaction_date",
            "transaction_type",
            "category",
            "description",
            "amount",
            "payment_method",
        ]
    ]

    # Rename columns into readable headings.
    display_df = display_df.rename(
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
        display_df,
        hide_index=True,
        use_container_width=True,
    )


    # Prepare a CSV version of the filtered transactions.
    export_df = filtered_df.copy()

    export_df["transaction_date"] = (
        export_df["transaction_date"].dt.strftime(
            "%Y-%m-%d"
        )
    )

    csv_data = export_df.to_csv(
        index=False
    ).encode("utf-8")


    st.download_button(
        label="⬇️ Download Filtered Transactions",
        data=csv_data,
        file_name="FinanceCanvas_transactions.csv",
        mime="text/csv",
        type="primary",
    )