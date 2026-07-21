import streamlit as st


def apply_global_styles():
    """
    Apply consistent visual styling across FinanceCanvas.
    """

    st.markdown(
        """
        <style>

        /* Main page width and spacing */
        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* Main page headings */
        h1 {
            font-size: 2.2rem !important;
            font-weight: 750 !important;
            letter-spacing: -0.03em;
        }

        h2, h3 {
            letter-spacing: -0.02em;
        }

        /* Dashboard metric cards */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 18px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
        }

        div[data-testid="stMetricLabel"] {
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            font-weight: 750;
        }

        /* Form containers */
        div[data-testid="stForm"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 20px;
        }

        /* Dataframes and charts */
        div[data-testid="stDataFrame"] {
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            overflow: hidden;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            border-right: 1px solid #E2E8F0;
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {
            border-radius: 9px;
            font-weight: 600;
        }

        /* Reduce excessive divider spacing */
        hr {
            margin-top: 1.7rem;
            margin-bottom: 1.7rem;
        }

        /* Custom FinanceCanvas brand block */
        .FinanceCanvas-brand {
            background:
                linear-gradient(
                    135deg,
                    #0F172A 0%,
                    #1E3A8A 55%,
                    #2563EB 100%
                );
            border-radius: 18px;
            padding: 28px;
            margin-bottom: 24px;
            color: white;
            box-shadow: 0 12px 30px rgba(37, 99, 235, 0.18);
        }

        .FinanceCanvas-brand h1 {
            color: white !important;
            margin: 0;
            font-size: 2.4rem !important;
        }

        .FinanceCanvas-brand p {
            color: #DBEAFE;
            margin-top: 8px;
            margin-bottom: 0;
            font-size: 1.05rem;
        }

        /* Feature cards */
        .feature-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 20px;
            min-height: 145px;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        }

        .feature-card h4 {
            margin-top: 0;
            margin-bottom: 8px;
            color: #0F172A;
        }

        .feature-card p {
            color: #475569;
            margin-bottom: 0;
            line-height: 1.55;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header(
    title="FinanceCanvas",
    subtitle=(
        "Investment and Expense Intelligence Platform"
    ),
):
    """
    Display the FinanceCanvas branded page header.
    """

    st.markdown(
        f"""
        <div class="FinanceCanvas-brand">
            <h1>💶 {title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_intro(
    title,
    description,
    icon="",
):
    """
    Display a consistent heading for secondary pages.
    """

    if icon:
        st.title(f"{icon} {title}")
    else:
        st.title(title)

    st.write(description)