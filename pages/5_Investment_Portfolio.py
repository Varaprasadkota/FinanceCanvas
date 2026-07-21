from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


# Locate the main FinanceCanvas project folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


from src.database import (
    add_investment,
    get_all_investments,
    initialise_database,
    update_investment_price,
)
from src.ui import apply_global_styles

st.set_page_config(
    page_title="Investment Portfolio | FinanceCanvas",
    page_icon="📈",
    layout="wide",
)
apply_global_styles()

initialise_database()


st.title("📈 Investment Portfolio")

st.write(
    """
    Record investments, track current values and analyse
    unrealised portfolio performance.
    """
)


asset_types = [
    "Stock",
    "ETF",
    "Mutual Fund",
    "Cryptocurrency",
    "Bond",
    "Cash Investment",
    "Other",
]


st.subheader("Add Investment")


with st.form(
    key="investment_form",
    clear_on_submit=True,
):
    form_column1, form_column2 = st.columns(2)

    with form_column1:
        asset_name = st.text_input(
            label="Asset Name",
            placeholder="Example: Apple Inc.",
        )

        ticker = st.text_input(
            label="Ticker or Code",
            placeholder="Example: AAPL",
        )

        asset_type = st.selectbox(
            label="Asset Type",
            options=asset_types,
        )

        purchase_date = st.date_input(
            label="Purchase Date",
            format="DD/MM/YYYY",
        )

    with form_column2:
        quantity = st.number_input(
            label="Quantity",
            min_value=0.0001,
            value=1.0000,
            step=0.1000,
            format="%.4f",
        )

        purchase_price = st.number_input(
            label="Purchase Price per Unit (€)",
            min_value=0.00,
            value=0.00,
            step=1.00,
            format="%.2f",
        )

        current_price = st.number_input(
            label="Current Price per Unit (€)",
            min_value=0.00,
            value=0.00,
            step=1.00,
            format="%.2f",
        )

        fees = st.number_input(
            label="Purchase Fees (€)",
            min_value=0.00,
            value=0.00,
            step=0.50,
            format="%.2f",
        )

        currency = st.selectbox(
            label="Currency",
            options=["EUR"],
        )

    add_button = st.form_submit_button(
        label="Add Investment",
        type="primary",
    )


if add_button:
    try:
        add_investment(
            asset_name=asset_name,
            ticker=ticker,
            asset_type=asset_type,
            purchase_date=purchase_date.isoformat(),
            quantity=float(quantity),
            purchase_price=float(purchase_price),
            current_price=float(current_price),
            fees=float(fees),
            currency=currency,
        )

        st.success(
            f"{asset_name} was added to your portfolio."
        )

        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            f"The investment could not be saved: {error}"
        )


st.divider()


investment_records = get_all_investments()


if not investment_records:
    st.info(
        "No investments are available. "
        "Use the form above to add your first holding."
    )

    st.stop()


investments_df = pd.DataFrame(
    investment_records
)


numeric_columns = [
    "quantity",
    "purchase_price",
    "current_price",
    "fees",
]


for column in numeric_columns:
    investments_df[column] = pd.to_numeric(
        investments_df[column],
        errors="coerce",
    ).fillna(0)


# Total original cost, including purchase fees.
investments_df["invested_amount"] = (
    investments_df["quantity"]
    * investments_df["purchase_price"]
    + investments_df["fees"]
)


# Current market value.
investments_df["current_value"] = (
    investments_df["quantity"]
    * investments_df["current_price"]
)


# Unrealised gain or loss.
investments_df["gain_loss"] = (
    investments_df["current_value"]
    - investments_df["invested_amount"]
)


def calculate_return_percentage(row):
    """
    Calculate investment return as a percentage.
    """

    if row["invested_amount"] <= 0:
        return 0

    return (
        row["gain_loss"]
        / row["invested_amount"]
        * 100
    )


investments_df["return_percentage"] = (
    investments_df.apply(
        calculate_return_percentage,
        axis=1,
    )
)


total_invested = investments_df[
    "invested_amount"
].sum()

total_current_value = investments_df[
    "current_value"
].sum()

total_gain_loss = investments_df[
    "gain_loss"
].sum()


if total_invested > 0:
    portfolio_return = (
        total_gain_loss / total_invested
    ) * 100
else:
    portfolio_return = 0


st.subheader("Portfolio Summary")


metric_column1, metric_column2, metric_column3, metric_column4 = (
    st.columns(4)
)


with metric_column1:
    st.metric(
        label="Total Invested",
        value=f"€{total_invested:,.2f}",
    )


with metric_column2:
    st.metric(
        label="Current Value",
        value=f"€{total_current_value:,.2f}",
    )


with metric_column3:
    st.metric(
        label="Unrealised Gain/Loss",
        value=f"€{total_gain_loss:,.2f}",
        delta=f"{portfolio_return:.2f}%",
    )


with metric_column4:
    st.metric(
        label="Number of Holdings",
        value=len(investments_df),
    )


# Identify the best and worst performing holdings.
best_investment = investments_df.loc[
    investments_df["return_percentage"].idxmax()
]

worst_investment = investments_df.loc[
    investments_df["return_percentage"].idxmin()
]


information_column1, information_column2 = st.columns(2)


with information_column1:
    st.success(
        f"Best performer: "
        f"{best_investment['ticker']} "
        f"({best_investment['return_percentage']:.2f}%)"
    )


with information_column2:
    st.warning(
        f"Lowest performer: "
        f"{worst_investment['ticker']} "
        f"({worst_investment['return_percentage']:.2f}%)"
    )


st.subheader("Update Current Price")


investment_labels = {
    int(row["investment_id"]): (
        f"{row['ticker']} — "
        f"{row['asset_name']} — "
        f"Current €{row['current_price']:,.2f}"
    )
    for _, row in investments_df.iterrows()
}


selected_investment_id = st.selectbox(
    label="Select Investment",
    options=list(investment_labels.keys()),
    format_func=lambda investment_id: (
        investment_labels[investment_id]
    ),
)


selected_row = investments_df[
    investments_df["investment_id"]
    == selected_investment_id
].iloc[0]


new_current_price = st.number_input(
    label="New Current Price per Unit (€)",
    min_value=0.00,
    value=float(selected_row["current_price"]),
    step=1.00,
    format="%.2f",
)


if st.button(
    label="Update Current Price",
    type="primary",
):
    try:
        update_investment_price(
            investment_id=selected_investment_id,
            current_price=float(new_current_price),
        )

        st.success(
            "The current price was updated successfully."
        )

        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            f"The price could not be updated: {error}"
        )


st.divider()

st.subheader("Holdings")


display_df = investments_df.copy()


display_df["purchase_date"] = pd.to_datetime(
    display_df["purchase_date"],
    errors="coerce",
).dt.strftime("%d/%m/%Y")


currency_columns = [
    "purchase_price",
    "current_price",
    "fees",
    "invested_amount",
    "current_value",
    "gain_loss",
]


for column in currency_columns:
    display_df[column] = display_df[column].apply(
        lambda value: f"€{value:,.2f}"
    )


display_df["quantity"] = (
    display_df["quantity"].apply(
        lambda value: f"{value:,.4f}"
    )
)


display_df["return_percentage"] = (
    display_df["return_percentage"].apply(
        lambda value: f"{value:.2f}%"
    )
)


display_df = display_df[
    [
        "asset_name",
        "ticker",
        "asset_type",
        "purchase_date",
        "quantity",
        "purchase_price",
        "current_price",
        "invested_amount",
        "current_value",
        "gain_loss",
        "return_percentage",
    ]
]


display_df = display_df.rename(
    columns={
        "asset_name": "Asset",
        "ticker": "Ticker",
        "asset_type": "Type",
        "purchase_date": "Purchase Date",
        "quantity": "Quantity",
        "purchase_price": "Purchase Price",
        "current_price": "Current Price",
        "invested_amount": "Invested",
        "current_value": "Current Value",
        "gain_loss": "Gain/Loss",
        "return_percentage": "Return",
    }
)


st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True,
)


st.subheader("Asset Allocation")


allocation_df = (
    investments_df.groupby(
        "asset_type",
        as_index=False,
    )["current_value"]
    .sum()
)


allocation_df = allocation_df.rename(
    columns={
        "asset_type": "Asset Type",
        "current_value": "Current Value",
    }
)


allocation_chart = px.pie(
    allocation_df,
    names="Asset Type",
    values="Current Value",
    title="Portfolio Allocation by Asset Type",
    hole=0.35,
)


st.plotly_chart(
    allocation_chart,
    use_container_width=True,
)


st.subheader("Investment Performance")


performance_df = investments_df[
    [
        "ticker",
        "gain_loss",
    ]
].copy()


performance_df = performance_df.rename(
    columns={
        "ticker": "Ticker",
        "gain_loss": "Unrealised Gain/Loss",
    }
)


performance_chart = px.bar(
    performance_df,
    x="Ticker",
    y="Unrealised Gain/Loss",
    title="Unrealised Gain or Loss by Holding",
    labels={
        "Unrealised Gain/Loss": "Gain/Loss (€)",
    },
)


st.plotly_chart(
    performance_chart,
    use_container_width=True,
)