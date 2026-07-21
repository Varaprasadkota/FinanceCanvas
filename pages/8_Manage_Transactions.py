from datetime import date
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# Locate the main FinanceCanvas project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from src.database import (
    delete_transaction,
    get_all_transactions,
    initialise_database,
    update_transaction,
)
from src.ui import apply_global_styles

st.set_page_config(
    page_title="Manage Transactions | FinanceCanvas",
    page_icon="✏️",
    layout="wide",
)
apply_global_styles()

initialise_database()


st.title("✏️ Manage Transactions")

st.write(
    """
    Correct transaction information or remove an
    incorrectly recorded transaction.
    """
)


transaction_records = get_all_transactions()


if not transaction_records:
    st.info(
        "No transactions are available to manage."
    )

    st.stop()


# Create a lookup dictionary using transaction IDs.
transaction_lookup = {
    int(transaction["transaction_id"]): transaction
    for transaction in transaction_records
}


def create_transaction_label(transaction_id):
    """
    Create a readable label for the selection menu.
    """

    transaction = transaction_lookup[transaction_id]

    return (
        f"{transaction['transaction_date']} | "
        f"{transaction['transaction_type']} | "
        f"{transaction['category']} | "
        f"€{float(transaction['amount']):,.2f}"
    )


selected_transaction_id = st.selectbox(
    label="Select Transaction",
    options=list(transaction_lookup.keys()),
    format_func=create_transaction_label,
)


selected_transaction = transaction_lookup[
    selected_transaction_id
]


st.divider()


# Convert the saved date into a date-input value.
saved_date = pd.to_datetime(
    selected_transaction["transaction_date"],
    errors="coerce",
)


if pd.isna(saved_date):
    default_date = date.today()
else:
    default_date = saved_date.date()


income_categories = [
    "Salary",
    "Bonus",
    "Freelance",
    "Investment Income",
    "Refund",
    "Other Income",
]


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


all_categories = (
    income_categories
    + expense_categories
)


# Include imported categories not already in the standard list.
saved_category = str(
    selected_transaction["category"]
)


if saved_category not in all_categories:
    all_categories.insert(
        0,
        saved_category,
    )


payment_methods = [
    "Debit Card",
    "Credit Card",
    "Bank Transfer",
    "Direct Debit",
    "Cash",
    "Bank Statement",
    "Other",
]


saved_payment_method = str(
    selected_transaction["payment_method"]
)


if saved_payment_method not in payment_methods:
    payment_methods.insert(
        0,
        saved_payment_method,
    )


saved_transaction_type = str(
    selected_transaction["transaction_type"]
)


if saved_transaction_type == "Income":
    type_index = 0
else:
    type_index = 1


st.subheader("Edit Selected Transaction")


with st.form(
    key=f"edit_transaction_{selected_transaction_id}",
):
    transaction_type = st.selectbox(
        label="Transaction Type",
        options=[
            "Income",
            "Expense",
        ],
        index=type_index,
    )

    transaction_date = st.date_input(
        label="Transaction Date",
        value=default_date,
        format="DD/MM/YYYY",
    )

    category_index = all_categories.index(
        saved_category
    )

    category = st.selectbox(
        label="Category",
        options=all_categories,
        index=category_index,
    )

    description = st.text_input(
        label="Description",
        value=str(
            selected_transaction["description"] or ""
        ),
    )

    amount = st.number_input(
        label="Amount (€)",
        min_value=0.01,
        value=float(
            selected_transaction["amount"]
        ),
        step=0.01,
        format="%.2f",
    )

    currency = st.selectbox(
        label="Currency",
        options=["EUR"],
    )

    payment_method_index = (
        payment_methods.index(
            saved_payment_method
        )
    )

    payment_method = st.selectbox(
        label="Payment Method",
        options=payment_methods,
        index=payment_method_index,
    )

    update_button = st.form_submit_button(
        label="Update Transaction",
        type="primary",
    )


if update_button:
    try:
        update_transaction(
            transaction_id=selected_transaction_id,
            transaction_date=(
                transaction_date.isoformat()
            ),
            transaction_type=transaction_type,
            category=category,
            description=description,
            amount=float(amount),
            currency=currency,
            payment_method=payment_method,
        )

        st.success(
            "Transaction updated successfully."
        )

        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            f"The transaction could not be updated: {error}"
        )


st.divider()


st.subheader("Delete Selected Transaction")

st.warning(
    "Deleting a transaction is permanent and will "
    "change dashboard, budget and forecast calculations."
)


confirm_delete = st.checkbox(
    label=(
        "I understand that this transaction "
        "will be permanently deleted."
    ),
    key=f"confirm_delete_{selected_transaction_id}",
)


delete_button = st.button(
    label="Delete Transaction",
    type="secondary",
    disabled=not confirm_delete,
)


if delete_button:
    try:
        delete_transaction(
            selected_transaction_id
        )

        st.success(
            "Transaction deleted successfully."
        )

        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            f"The transaction could not be deleted: {error}"
        )