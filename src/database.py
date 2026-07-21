from pathlib import Path
import sqlite3


# Main FinanceCanvas project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Database location
DATA_FOLDER = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_FOLDER / "FinanceCanvas.db"


def get_connection():
    """Create and return a connection to the database."""

    DATA_FOLDER.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialise_database():
    """Create the transactions table."""

    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'EUR',
                payment_method TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_month TEXT NOT NULL,
                category TEXT NOT NULL,
                budget_amount REAL NOT NULL
                    CHECK(budget_amount >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(budget_month, category)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS investments (
                investment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_name TEXT NOT NULL,
                ticker TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                purchase_date TEXT NOT NULL,
                quantity REAL NOT NULL CHECK(quantity > 0),
                purchase_price REAL NOT NULL CHECK(purchase_price >= 0),
                current_price REAL NOT NULL CHECK(current_price >= 0),
                fees REAL NOT NULL DEFAULT 0 CHECK(fees >= 0),
                currency TEXT NOT NULL DEFAULT 'EUR',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS financial_profile (
                profile_id INTEGER PRIMARY KEY
                    CHECK(profile_id = 1),

                cash_savings REAL NOT NULL DEFAULT 0
                    CHECK(cash_savings >= 0),

                outstanding_debt REAL NOT NULL DEFAULT 0
                    CHECK(outstanding_debt >= 0),

                monthly_debt_payment REAL NOT NULL DEFAULT 0
                    CHECK(monthly_debt_payment >= 0),

                emergency_target_months INTEGER NOT NULL DEFAULT 6
                    CHECK(emergency_target_months BETWEEN 1 AND 24),

                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


def add_transaction(
    transaction_date,
    transaction_type,
    category,
    description,
    amount,
    currency,
    payment_method,
):
    """Save one transaction."""

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO transactions (
                transaction_date,
                transaction_type,
                category,
                description,
                amount,
                currency,
                payment_method
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_date,
                transaction_type,
                category,
                description,
                amount,
                currency,
                payment_method,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def get_transaction_count():
    """Return the number of stored transactions."""

    connection = get_connection()

    try:
        result = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM transactions
            """
        ).fetchone()

        return result["total"]

    finally:
        connection.close()

from datetime import date

def get_monthly_summary():
    """
    Calculate income, expenses and savings for the current month.
    """

    # Create a value such as 2026-07.
    current_month = date.today().strftime("%Y-%m")

    connection = get_connection()

    try:
        result = connection.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'Income'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_income,

                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'Expense'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_expenses

            FROM transactions

            WHERE substr(transaction_date, 1, 7) = ?
            """,
            (current_month,),
        ).fetchone()

        income = float(result["total_income"])
        expenses = float(result["total_expenses"])
        savings = income - expenses

        return {
            "income": income,
            "expenses": expenses,
            "savings": savings,
        }

    finally:
        connection.close()


def get_recent_transactions(limit=5):
    """
    Return the most recently entered transactions.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                transaction_date,
                transaction_type,
                category,
                description,
                amount,
                payment_method

            FROM transactions

            ORDER BY
                transaction_date DESC,
                transaction_id DESC

            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        # Convert SQLite rows into normal Python dictionaries.
        return [dict(row) for row in rows]

    finally:
        connection.close()

def get_all_transactions():
    """
    Return every transaction stored in the database.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                transaction_id,
                transaction_date,
                transaction_type,
                category,
                description,
                amount,
                currency,
                payment_method,
                created_at

            FROM transactions

            ORDER BY
                transaction_date DESC,
                transaction_id DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()
def save_budget(
    budget_month,
    category,
    budget_amount,
):
    """
    Create a new monthly budget or update an existing one.
    """

    if budget_amount < 0:
        raise ValueError(
            "Budget amount cannot be negative."
        )

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO budgets (
                budget_month,
                category,
                budget_amount
            )
            VALUES (?, ?, ?)

            ON CONFLICT(budget_month, category)
            DO UPDATE SET
                budget_amount = excluded.budget_amount,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                budget_month,
                category,
                budget_amount,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def get_budgets_for_month(budget_month):
    """
    Return all budgets saved for a selected month.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                category,
                budget_amount

            FROM budgets

            WHERE budget_month = ?

            ORDER BY category
            """,
            (budget_month,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_expenses_by_category(budget_month):
    """
    Calculate actual expenses by category for a selected month.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                category,
                SUM(amount) AS actual_spending

            FROM transactions

            WHERE
                transaction_type = 'Expense'
                AND substr(transaction_date, 1, 7) = ?

            GROUP BY category

            ORDER BY category
            """,
            (budget_month,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()   

def import_transactions(transaction_rows):
    """
    Import multiple transactions into the database.

    Existing matching transactions are skipped to reduce
    accidental duplicate imports.
    """

    connection = get_connection()

    inserted_count = 0
    skipped_count = 0

    try:
        for row in transaction_rows:
            transaction_date = row["transaction_date"]
            transaction_type = row["transaction_type"]
            category = row["category"]
            description = row["description"]
            amount = round(float(row["amount"]), 2)
            currency = row["currency"]
            payment_method = row["payment_method"]

            # Check whether an identical transaction already exists.
            existing_transaction = connection.execute(
                """
                SELECT transaction_id
                FROM transactions
                WHERE
                    transaction_date = ?
                    AND transaction_type = ?
                    AND category = ?
                    AND description = ?
                    AND amount = ?
                    AND currency = ?
                    AND payment_method = ?
                LIMIT 1
                """,
                (
                    transaction_date,
                    transaction_type,
                    category,
                    description,
                    amount,
                    currency,
                    payment_method,
                ),
            ).fetchone()

            if existing_transaction:
                skipped_count += 1
                continue

            connection.execute(
                """
                INSERT INTO transactions (
                    transaction_date,
                    transaction_type,
                    category,
                    description,
                    amount,
                    currency,
                    payment_method
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_date,
                    transaction_type,
                    category,
                    description,
                    amount,
                    currency,
                    payment_method,
                ),
            )

            inserted_count += 1

        connection.commit()

        return {
            "inserted": inserted_count,
            "skipped": skipped_count,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()            

def import_transactions(transaction_rows):
    """
    Import multiple transactions into the database.

    Matching transactions are skipped to prevent
    accidental duplicate imports.
    """

    connection = get_connection()

    inserted_count = 0
    skipped_count = 0

    try:
        for row in transaction_rows:
            transaction_date = row["transaction_date"]
            transaction_type = row["transaction_type"]
            category = row["category"]
            description = row["description"]
            amount = round(float(row["amount"]), 2)
            currency = row["currency"]
            payment_method = row["payment_method"]

            existing_transaction = connection.execute(
                """
                SELECT transaction_id
                FROM transactions
                WHERE transaction_date = ?
                  AND transaction_type = ?
                  AND category = ?
                  AND description = ?
                  AND amount = ?
                  AND currency = ?
                  AND payment_method = ?
                LIMIT 1
                """,
                (
                    transaction_date,
                    transaction_type,
                    category,
                    description,
                    amount,
                    currency,
                    payment_method,
                ),
            ).fetchone()

            if existing_transaction:
                skipped_count += 1
                continue

            connection.execute(
                """
                INSERT INTO transactions (
                    transaction_date,
                    transaction_type,
                    category,
                    description,
                    amount,
                    currency,
                    payment_method
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_date,
                    transaction_type,
                    category,
                    description,
                    amount,
                    currency,
                    payment_method,
                ),
            )

            inserted_count += 1

        connection.commit()

        return {
            "inserted": inserted_count,
            "skipped": skipped_count,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()  

def add_investment(
    asset_name,
    ticker,
    asset_type,
    purchase_date,
    quantity,
    purchase_price,
    current_price,
    fees,
    currency,
):
    """
    Save one investment purchase in the database.
    """

    if not asset_name.strip():
        raise ValueError("Asset name is required.")

    if not ticker.strip():
        raise ValueError("Ticker or investment code is required.")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    if purchase_price < 0:
        raise ValueError("Purchase price cannot be negative.")

    if current_price < 0:
        raise ValueError("Current price cannot be negative.")

    if fees < 0:
        raise ValueError("Fees cannot be negative.")

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO investments (
                asset_name,
                ticker,
                asset_type,
                purchase_date,
                quantity,
                purchase_price,
                current_price,
                fees,
                currency
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_name.strip(),
                ticker.strip().upper(),
                asset_type,
                purchase_date,
                float(quantity),
                float(purchase_price),
                float(current_price),
                float(fees),
                currency,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def get_all_investments():
    """
    Return every investment stored in the database.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                investment_id,
                asset_name,
                ticker,
                asset_type,
                purchase_date,
                quantity,
                purchase_price,
                current_price,
                fees,
                currency,
                created_at,
                updated_at

            FROM investments

            ORDER BY
                purchase_date DESC,
                investment_id DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def update_investment_price(
    investment_id,
    current_price,
):
    """
    Update the current price of one investment.
    """

    if current_price < 0:
        raise ValueError(
            "Current price cannot be negative."
        )

    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE investments

            SET
                current_price = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE investment_id = ?
            """,
            (
                float(current_price),
                int(investment_id),
            ),
        )

        connection.commit()

    finally:
        connection.close()
def save_financial_profile(
    cash_savings,
    outstanding_debt,
    monthly_debt_payment,
    emergency_target_months,
):
    """
    Save or update the user's financial profile.
    """

    if cash_savings < 0:
        raise ValueError(
            "Cash savings cannot be negative."
        )

    if outstanding_debt < 0:
        raise ValueError(
            "Outstanding debt cannot be negative."
        )

    if monthly_debt_payment < 0:
        raise ValueError(
            "Monthly debt payment cannot be negative."
        )

    if not 1 <= emergency_target_months <= 24:
        raise ValueError(
            "Emergency-fund target must be between "
            "1 and 24 months."
        )

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO financial_profile (
                profile_id,
                cash_savings,
                outstanding_debt,
                monthly_debt_payment,
                emergency_target_months
            )
            VALUES (1, ?, ?, ?, ?)

            ON CONFLICT(profile_id)
            DO UPDATE SET
                cash_savings = excluded.cash_savings,
                outstanding_debt = excluded.outstanding_debt,
                monthly_debt_payment = excluded.monthly_debt_payment,
                emergency_target_months =
                    excluded.emergency_target_months,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                float(cash_savings),
                float(outstanding_debt),
                float(monthly_debt_payment),
                int(emergency_target_months),
            ),
        )

        connection.commit()

    finally:
        connection.close()


def get_financial_profile():
    """
    Return the saved financial profile.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                cash_savings,
                outstanding_debt,
                monthly_debt_payment,
                emergency_target_months,
                updated_at

            FROM financial_profile

            WHERE profile_id = 1
            """
        ).fetchone()

        if row:
            return dict(row)

        return {
            "cash_savings": 0.0,
            "outstanding_debt": 0.0,
            "monthly_debt_payment": 0.0,
            "emergency_target_months": 6,
            "updated_at": None,
        }

    finally:
        connection.close()   

def update_transaction(
    transaction_id,
    transaction_date,
    transaction_type,
    category,
    description,
    amount,
    currency,
    payment_method,
):
    """Update an existing transaction."""

    if transaction_type not in ["Income", "Expense"]:
        raise ValueError(
            "Transaction type must be Income or Expense."
        )

    if not category.strip():
        raise ValueError("Category is required.")

    if amount <= 0:
        raise ValueError(
            "Amount must be greater than zero."
        )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE transactions
            SET
                transaction_date = ?,
                transaction_type = ?,
                category = ?,
                description = ?,
                amount = ?,
                currency = ?,
                payment_method = ?
            WHERE transaction_id = ?
            """,
            (
                transaction_date,
                transaction_type,
                category.strip(),
                description.strip(),
                float(amount),
                currency,
                payment_method,
                int(transaction_id),
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "The selected transaction could not be found."
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_transaction(transaction_id):
    """Delete one transaction from the database."""

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM transactions
            WHERE transaction_id = ?
            """,
            (int(transaction_id),),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "The selected transaction could not be found."
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()