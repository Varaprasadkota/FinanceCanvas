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

def delete_transactions(transaction_ids):
    """
    Delete multiple transactions using the existing
    single-transaction delete function.
    """

    clean_ids = sorted(
        {
            int(transaction_id)
            for transaction_id in transaction_ids
        }
    )

    deleted_count = 0

    for transaction_id in clean_ids:
        delete_transaction(transaction_id)
        deleted_count += 1

    return deleted_count

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
# =========================================================
# BULK TRANSACTION DELETION
# =========================================================

st.divider()

st.subheader("🗑️ Bulk Delete Transactions")

st.warning(
    """
    Bulk deletion is permanent. Deleted records will be removed
    from the dashboard, budgets, financial-health calculations
    and forecasts.
    """
)


# Reload transactions so this section always uses current records.
bulk_transaction_records = get_all_transactions()


if not bulk_transaction_records:
    st.info(
        "No transactions are available for bulk deletion."
    )

else:
    bulk_df = pd.DataFrame(
        bulk_transaction_records
    )

    bulk_df["transaction_date"] = pd.to_datetime(
        bulk_df["transaction_date"],
        errors="coerce",
    )

    bulk_df["amount"] = pd.to_numeric(
        bulk_df["amount"],
        errors="coerce",
    ).fillna(0.0)

    bulk_df = bulk_df[
        bulk_df["transaction_date"].notna()
    ].copy()


    if bulk_df.empty:
        st.error(
            "Transaction dates could not be processed."
        )

    else:
        st.write(
            """
            Filter the records and tick every transaction
            that you want to remove.
            """
        )


        # -------------------------------------------------
        # Bulk-delete filters
        # -------------------------------------------------

        earliest_bulk_date = (
            bulk_df["transaction_date"].min().date()
        )

        latest_bulk_date = (
            bulk_df["transaction_date"].max().date()
        )


        bulk_date_column1, bulk_date_column2 = (
            st.columns(2)
        )


        with bulk_date_column1:
            bulk_start_date = st.date_input(
                label="Bulk Delete Start Date",
                value=earliest_bulk_date,
                min_value=earliest_bulk_date,
                max_value=latest_bulk_date,
                format="DD/MM/YYYY",
                key="bulk_delete_start_date",
            )


        with bulk_date_column2:
            bulk_end_date = st.date_input(
                label="Bulk Delete End Date",
                value=latest_bulk_date,
                min_value=earliest_bulk_date,
                max_value=latest_bulk_date,
                format="DD/MM/YYYY",
                key="bulk_delete_end_date",
            )


        available_bulk_types = sorted(
            bulk_df["transaction_type"]
            .dropna()
            .unique()
            .tolist()
        )

        available_bulk_categories = sorted(
            bulk_df["category"]
            .dropna()
            .unique()
            .tolist()
        )


        bulk_filter_column1, bulk_filter_column2 = (
            st.columns(2)
        )


        with bulk_filter_column1:
            selected_bulk_types = st.multiselect(
                label="Transaction Types",
                options=available_bulk_types,
                default=available_bulk_types,
                key="bulk_delete_types",
            )


        with bulk_filter_column2:
            selected_bulk_categories = st.multiselect(
                label="Categories",
                options=available_bulk_categories,
                default=available_bulk_categories,
                key="bulk_delete_categories",
            )


        bulk_description_search = st.text_input(
            label="Search Description",
            placeholder=(
                "Example: Apple, rent, salary, transfer"
            ),
            key="bulk_delete_description_search",
        )


        if bulk_start_date > bulk_end_date:
            st.error(
                "Bulk Delete Start Date cannot be later "
                "than Bulk Delete End Date."
            )

        else:
            # ---------------------------------------------
            # Apply filters
            # ---------------------------------------------

            filtered_bulk_df = bulk_df[
                (
                    bulk_df["transaction_date"].dt.date
                    >= bulk_start_date
                )
                & (
                    bulk_df["transaction_date"].dt.date
                    <= bulk_end_date
                )
            ].copy()


            if selected_bulk_types:
                filtered_bulk_df = filtered_bulk_df[
                    filtered_bulk_df[
                        "transaction_type"
                    ].isin(selected_bulk_types)
                ]

            else:
                filtered_bulk_df = (
                    filtered_bulk_df.iloc[0:0]
                )


            if selected_bulk_categories:
                filtered_bulk_df = filtered_bulk_df[
                    filtered_bulk_df[
                        "category"
                    ].isin(selected_bulk_categories)
                ]

            else:
                filtered_bulk_df = (
                    filtered_bulk_df.iloc[0:0]
                )


            if bulk_description_search.strip():
                description_mask = (
                    filtered_bulk_df["description"]
                    .fillna("")
                    .astype(str)
                    .str.contains(
                        bulk_description_search.strip(),
                        case=False,
                        regex=False,
                    )
                )

                filtered_bulk_df = (
                    filtered_bulk_df[
                        description_mask
                    ]
                )


            if filtered_bulk_df.empty:
                st.info(
                    "No transactions match the bulk-delete "
                    "filters."
                )

            else:
                st.caption(
                    f"{len(filtered_bulk_df)} transaction(s) "
                    "match the selected filters."
                )


                # -----------------------------------------
                # Create the selectable transaction table
                # -----------------------------------------

                bulk_selection_df = (
                    filtered_bulk_df.copy()
                )

                bulk_selection_df["Delete"] = False

                bulk_selection_df["Date"] = (
                    bulk_selection_df[
                        "transaction_date"
                    ].dt.strftime("%d/%m/%Y")
                )

                bulk_selection_df["Type"] = (
                    bulk_selection_df[
                        "transaction_type"
                    ]
                )

                bulk_selection_df["Category"] = (
                    bulk_selection_df["category"]
                )

                bulk_selection_df["Description"] = (
                    bulk_selection_df[
                        "description"
                    ].fillna("")
                )

                bulk_selection_df["Amount"] = (
                    bulk_selection_df.apply(
                        lambda row: (
                            f"+€{row['amount']:,.2f}"
                            if row[
                                "transaction_type"
                            ] == "Income"
                            else (
                                f"-€{row['amount']:,.2f}"
                            )
                        ),
                        axis=1,
                    )
                )

                bulk_selection_df[
                    "Payment Method"
                ] = bulk_selection_df[
                    "payment_method"
                ]


                select_all_visible = st.checkbox(
                    label=(
                        "Select every transaction currently "
                        "shown by these filters"
                    ),
                    key="bulk_select_all_visible",
                )


                if select_all_visible:
                    bulk_selection_df["Delete"] = True


                editor_key = (
                    "bulk_delete_editor_"
                    f"{bulk_start_date}_"
                    f"{bulk_end_date}_"
                    f"{select_all_visible}_"
                    f"{len(filtered_bulk_df)}"
                )


                edited_bulk_df = st.data_editor(
                    bulk_selection_df[
                        [
                            "Delete",
                            "transaction_id",
                            "Date",
                            "Type",
                            "Category",
                            "Description",
                            "Amount",
                            "Payment Method",
                        ]
                    ],
                    hide_index=True,
                    use_container_width=True,
                    num_rows="fixed",
                    disabled=[
                        "transaction_id",
                        "Date",
                        "Type",
                        "Category",
                        "Description",
                        "Amount",
                        "Payment Method",
                    ],
                    column_config={
                        "Delete": (
                            st.column_config.CheckboxColumn(
                                label="Select",
                                help=(
                                    "Tick the transaction "
                                    "for deletion."
                                ),
                                default=False,
                            )
                        ),
                        "transaction_id": (
                            st.column_config.NumberColumn(
                                label="Record ID",
                                format="%d",
                            )
                        ),
                    },
                    key=editor_key,
                )


                selected_bulk_rows = (
                    edited_bulk_df[
                        edited_bulk_df["Delete"]
                    ].copy()
                )


                selected_transaction_ids = (
                    selected_bulk_rows[
                        "transaction_id"
                    ]
                    .astype(int)
                    .tolist()
                )


                selected_original_df = (
                    filtered_bulk_df[
                        filtered_bulk_df[
                            "transaction_id"
                        ].isin(
                            selected_transaction_ids
                        )
                    ].copy()
                )


                st.divider()


                # -----------------------------------------
                # Selection summary
                # -----------------------------------------

                selected_count = len(
                    selected_transaction_ids
                )

                selected_income = float(
                    selected_original_df.loc[
                        selected_original_df[
                            "transaction_type"
                        ] == "Income",
                        "amount",
                    ].sum()
                )

                selected_expenses = float(
                    selected_original_df.loc[
                        selected_original_df[
                            "transaction_type"
                        ] == "Expense",
                        "amount",
                    ].sum()
                )


                selection_metric1, selection_metric2, (
                    selection_metric3
                ) = st.columns(3)


                with selection_metric1:
                    st.metric(
                        label="Selected Transactions",
                        value=selected_count,
                    )


                with selection_metric2:
                    st.metric(
                        label="Selected Income",
                        value=f"€{selected_income:,.2f}",
                    )


                with selection_metric3:
                    st.metric(
                        label="Selected Expenses",
                        value=(
                            f"€{selected_expenses:,.2f}"
                        ),
                    )


                if selected_count > 0:
                    # -------------------------------------
                    # Backup selected records
                    # -------------------------------------

                    backup_df = (
                        selected_original_df.copy()
                    )

                    backup_df[
                        "transaction_date"
                    ] = backup_df[
                        "transaction_date"
                    ].dt.strftime("%Y-%m-%d")

                    selected_backup_csv = (
                        backup_df.to_csv(
                            index=False
                        ).encode("utf-8")
                    )


                    st.download_button(
                        label=(
                            "⬇️ Download Selected "
                            "Transactions Before Deleting"
                        ),
                        data=selected_backup_csv,
                        file_name=(
                            "financecanvas_"
                            "bulk_delete_backup.csv"
                        ),
                        mime="text/csv",
                        use_container_width=True,
                    )


                    st.error(
                        f"You are preparing to permanently "
                        f"delete {selected_count} "
                        f"transaction(s)."
                    )


                    confirm_bulk_delete = st.checkbox(
                        label=(
                            "I understand that bulk "
                            "deletion cannot be undone."
                        ),
                        key="confirm_bulk_delete_checkbox",
                    )


                    required_confirmation = (
                        f"DELETE {selected_count}"
                    )


                    confirmation_text = st.text_input(
                        label=(
                            "Type the confirmation phrase: "
                            f"{required_confirmation}"
                        ),
                        key="bulk_delete_confirmation_text",
                    )


                    confirmation_matches = (
                        confirmation_text.strip()
                        == required_confirmation
                    )


                    bulk_delete_button = st.button(
                        label=(
                            f"🗑️ Permanently Delete "
                            f"{selected_count} Transactions"
                        ),
                        type="primary",
                        use_container_width=True,
                        disabled=not (
                            confirm_bulk_delete
                            and confirmation_matches
                        ),
                    )


                    if bulk_delete_button:
                        try:
                            deleted_count = (
                                delete_transactions(
                                    selected_transaction_ids
                                )
                            )

                            st.success(
                                f"{deleted_count} transaction(s) "
                                "deleted successfully."
                            )

                            # Refresh dashboard, budget and
                            # forecast calculations.
                            st.rerun()

                        except Exception as error:
                            st.error(
                                "The selected transactions "
                                f"could not be deleted: {error}"
                            )

                else:
                    st.info(
                        "Tick at least one transaction in "
                        "the Select column."
                    )        