from pathlib import Path
import sys

import streamlit as st


# Find the main FinanceCanvas project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allow this page to import files from the src folder.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from src.database import (
    add_transaction,
    get_transaction_count,
    initialise_database,
)
from src.ui import apply_global_styles

# Configure the page.
st.set_page_config(
    page_title="Add Transaction | FinanceCanvas",
    page_icon="➕",
    layout="wide",
)
apply_global_styles()

# Create the database and transactions table.
initialise_database()


st.title("➕ Add Transaction")

st.write(
    "Record your income and expenses in the FinanceCanvas database."
)


# Select income or expense.
transaction_type = st.radio(
    "Transaction Type",
    options=["Expense", "Income"],
    horizontal=True,
)


# Show different categories based on transaction type.
if transaction_type == "Income":
    categories = [
        "Salary",
        "Bonus",
        "Freelance",
        "Investment Income",
        "Refund",
        "Other Income",
    ]
else:
    categories = [
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


# Create the transaction form.
with st.form(
    key="transaction_form",
    clear_on_submit=True,
):
    transaction_date = st.date_input(
        "Transaction Date",
        format="DD/MM/YYYY",
    )

    category = st.selectbox(
        "Category",
        options=categories,
    )

    description = st.text_input(
        "Description",
        placeholder="Example: Monthly rent",
    )

    amount = st.number_input(
        "Amount (€)",
        min_value=0.01,
        value=0.01,
        step=0.01,
        format="%.2f",
    )

    currency = st.selectbox(
        "Currency",
        options=["EUR"],
    )

    payment_method = st.selectbox(
        "Payment Method",
        options=[
            "Debit Card",
            "Credit Card",
            "Bank Transfer",
            "Direct Debit",
            "Cash",
            "Other",
        ],
    )

    submitted = st.form_submit_button(
        "Save Transaction",
        type="primary",
    )


# Save the form information.
if submitted:
    try:
        add_transaction(
            transaction_date=transaction_date.isoformat(),
            transaction_type=transaction_type,
            category=category,
            description=description.strip(),
            amount=float(amount),
            currency=currency,
            payment_method=payment_method,
        )

        st.success(
            f"{transaction_type} of €{amount:,.2f} saved successfully."
        )

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            f"The transaction could not be saved: {error}"
        )


st.divider()

st.metric(
    label="Total Transactions Stored",
    value=get_transaction_count(),
)