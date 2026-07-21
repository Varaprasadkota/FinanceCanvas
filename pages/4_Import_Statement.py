from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# Locate the main FinanceCanvas project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from src.database import (
    import_transactions,
    initialise_database,
)
from src.ui import apply_global_styles

st.set_page_config(
    page_title="Import Statement | FinanceCanvas",
    page_icon="📥",
    layout="wide",
)
apply_global_styles()

initialise_database()


st.title("📥 Import Bank Statement")

st.write(
    """
    Upload a CSV file containing income and expense
    transactions. FinanceCanvas will validate and clean the
    information before saving it.
    """
)


# Create an example CSV template.
template_df = pd.DataFrame(
    [
        {
            "Date": "2026-07-01",
            "Type": "Income",
            "Category": "Salary",
            "Description": "Monthly salary",
            "Amount": 3000.00,
            "Currency": "EUR",
            "Payment Method": "Bank Transfer",
        },
        {
            "Date": "2026-07-02",
            "Type": "Expense",
            "Category": "Groceries",
            "Description": "Supermarket",
            "Amount": 75.50,
            "Currency": "EUR",
            "Payment Method": "Debit Card",
        },
        {
            "Date": "2026-07-03",
            "Type": "Expense",
            "Category": "Transport",
            "Description": "Leap card top-up",
            "Amount": 20.00,
            "Currency": "EUR",
            "Payment Method": "Debit Card",
        },
    ]
)


template_csv = template_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download CSV Template",
    data=template_csv,
    file_name="FinanceCanvas_import_template.csv",
    mime="text/csv",
)


st.caption(
    """
    Required columns: Date, Type, Description and Amount.
    Category, Currency and Payment Method may be left blank.
    """
)


uploaded_file = st.file_uploader(
    label="Upload CSV Statement",
    type=["csv"],
    help="Upload a CSV file using the FinanceCanvas template format.",
)


if uploaded_file is None:
    st.info(
        "Download the template, review its structure and "
        "upload a CSV file to continue."
    )

    st.stop()


# Read the uploaded file.
try:
    uploaded_df = pd.read_csv(
        uploaded_file
    )

except UnicodeDecodeError:
    st.error(
        "The file encoding could not be read. "
        "Save the statement as a UTF-8 CSV file."
    )

    st.stop()

except Exception as error:
    st.error(
        f"The CSV file could not be opened: {error}"
    )

    st.stop()


st.subheader("Original File Preview")

st.dataframe(
    uploaded_df.head(20),
    hide_index=True,
    use_container_width=True,
)


# Remove unnecessary spaces from column names.
uploaded_df.columns = [
    str(column).strip()
    for column in uploaded_df.columns
]


required_columns = [
    "Date",
    "Type",
    "Description",
    "Amount",
]


missing_columns = [
    column
    for column in required_columns
    if column not in uploaded_df.columns
]


if missing_columns:
    st.error(
        "The following required columns are missing: "
        + ", ".join(missing_columns)
    )

    st.write(
        "Use the Download CSV Template button to obtain "
        "the correct file format."
    )

    st.stop()


# Add optional columns when they are missing.
optional_columns = {
    "Category": "",
    "Currency": "EUR",
    "Payment Method": "Bank Statement",
}


for column, default_value in optional_columns.items():
    if column not in uploaded_df.columns:
        uploaded_df[column] = default_value


# Keep only the FinanceCanvas transaction columns.
cleaned_df = uploaded_df[
    [
        "Date",
        "Type",
        "Category",
        "Description",
        "Amount",
        "Currency",
        "Payment Method",
    ]
].copy()


# Clean text values.
text_columns = [
    "Type",
    "Category",
    "Description",
    "Currency",
    "Payment Method",
]


for column in text_columns:
    cleaned_df[column] = (
        cleaned_df[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )


# Standardise transaction types.
cleaned_df["Type"] = (
    cleaned_df["Type"].str.title()
)


# Convert transaction dates.
cleaned_df["Parsed Date"] = pd.to_datetime(
    cleaned_df["Date"],
    errors="coerce",
    dayfirst=True,
)


# Convert amounts into numbers.
cleaned_df["Parsed Amount"] = pd.to_numeric(
    cleaned_df["Amount"],
    errors="coerce",
)


# Standardise currencies.
cleaned_df["Currency"] = (
    cleaned_df["Currency"]
    .replace("", "EUR")
    .str.upper()
)


# Add a default payment method.
cleaned_df["Payment Method"] = (
    cleaned_df["Payment Method"]
    .replace("", "Bank Statement")
)


# Assign a default category when it is missing.
def assign_default_category(row):
    """
    Select a category when the uploaded category is blank.
    """

    if row["Category"]:
        return row["Category"]

    if row["Type"] == "Income":
        return "Other Income"

    return "Other Expense"


cleaned_df["Category"] = cleaned_df.apply(
    assign_default_category,
    axis=1,
)


# Explain why a row is invalid.
def identify_validation_error(row):
    """
    Return the first validation problem found in a row.
    """

    if pd.isna(row["Parsed Date"]):
        return "Invalid or missing date"

    if row["Type"] not in ["Income", "Expense"]:
        return "Type must be Income or Expense"

    if pd.isna(row["Parsed Amount"]):
        return "Amount is not numeric"

    if row["Parsed Amount"] <= 0:
        return "Amount must be greater than zero"

    if not row["Description"]:
        return "Description is missing"

    return ""


cleaned_df["Validation Error"] = cleaned_df.apply(
    identify_validation_error,
    axis=1,
)


# Separate valid and invalid rows.
valid_df = cleaned_df[
    cleaned_df["Validation Error"] == ""
].copy()


invalid_df = cleaned_df[
    cleaned_df["Validation Error"] != ""
].copy()


st.divider()

st.subheader("Validation Summary")


metric_column1, metric_column2, metric_column3 = st.columns(3)


with metric_column1:
    st.metric(
        label="Rows Uploaded",
        value=len(cleaned_df),
    )


with metric_column2:
    st.metric(
        label="Valid Rows",
        value=len(valid_df),
    )


with metric_column3:
    st.metric(
        label="Invalid Rows",
        value=len(invalid_df),
    )


if not invalid_df.empty:
    st.error(
        f"{len(invalid_df)} row or rows contain invalid data "
        "and will not be imported."
    )

    invalid_display_df = invalid_df[
        [
            "Date",
            "Type",
            "Category",
            "Description",
            "Amount",
            "Validation Error",
        ]
    ]

    st.dataframe(
        invalid_display_df,
        hide_index=True,
        use_container_width=True,
    )


st.subheader("Cleaned Transaction Preview")


if valid_df.empty:
    st.warning(
        "No valid transactions are available for import."
    )

    st.stop()


preview_df = valid_df[
    [
        "Parsed Date",
        "Type",
        "Category",
        "Description",
        "Parsed Amount",
        "Currency",
        "Payment Method",
    ]
].copy()


preview_df["Parsed Date"] = (
    preview_df["Parsed Date"].dt.strftime(
        "%d/%m/%Y"
    )
)


preview_df["Parsed Amount"] = (
    preview_df["Parsed Amount"].apply(
        lambda value: f"€{value:,.2f}"
    )
)


preview_df = preview_df.rename(
    columns={
        "Parsed Date": "Date",
        "Parsed Amount": "Amount",
    }
)


st.dataframe(
    preview_df,
    hide_index=True,
    use_container_width=True,
)


confirm_import = st.checkbox(
    "I reviewed the valid transactions and want to import them."
)


import_button = st.button(
    label="Import Valid Transactions",
    type="primary",
    disabled=not confirm_import,
)


if import_button:
    transaction_rows = []

    for _, row in valid_df.iterrows():
        transaction_rows.append(
            {
                "transaction_date": (
                    row["Parsed Date"].strftime(
                        "%Y-%m-%d"
                    )
                ),
                "transaction_type": row["Type"],
                "category": row["Category"],
                "description": row["Description"],
                "amount": float(
                    row["Parsed Amount"]
                ),
                "currency": row["Currency"],
                "payment_method": (
                    row["Payment Method"]
                ),
            }
        )

    try:
        import_result = import_transactions(
            transaction_rows
        )

        st.success(
            f"{import_result['inserted']} transaction(s) "
            "imported successfully."
        )

        if import_result["skipped"] > 0:
            st.warning(
                f"{import_result['skipped']} duplicate "
                "transaction(s) were skipped."
            )

    except Exception as error:
        st.error(
            f"The transactions could not be imported: {error}"
        )