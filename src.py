import hashlib
import numpy as np
import pandas as pd


def _pseudonymise_id(customer_id: str, salt: str = "duka_capstone_salt") -> str:
    if pd.isna(customer_id):
        return customer_id
    digest = hashlib.sha256(f"{salt}:{customer_id}".encode("utf-8")).hexdigest()[:8]
    return f"cust_{digest}"


def audit_data_quality(
    tx_df: pd.DataFrame,
    cust_df: pd.DataFrame,
    prod_df: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        {
            "dimension": "Completeness",
            "issue_count": int(tx_df[["discount_pct", "unit_price_kes"]].isna().sum().sum()),
            "description": "Missing discount_pct or unit_price_kes values in raw_transactions.",
        },
        {
            "dimension": "Uniqueness",
            "issue_count": int(tx_df.duplicated(subset=["transaction_id"]).sum()),
            "description": "Duplicate transaction_id rows in raw_transactions.",
        },
        {
            "dimension": "Validity",
            "issue_count": int(
                (tx_df["quantity"] <= 0).sum()
                + ((tx_df["order_date"] < "2026-01-01") | (tx_df["order_date"] > "2026-06-30")).sum()
            ),
            "description": "Non-positive quantities or order_date outside H1 2026.",
        },
        {
            "dimension": "Consistency",
            "issue_count": int(
                (~tx_df["branch"].isin(["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"])).sum()
                + (~tx_df["payment_method"].isin(["M-Pesa", "Card", "Bank Transfer", "Cash"])).sum()
            ),
            "description": "Inconsistent casing or whitespace in branch and payment_method.",
        },
        {
            "dimension": "Accuracy",
            "issue_count": int(
                tx_df.dropna(subset=["unit_price_kes"])
                .merge(prod_df, on="product_id", how="left")
                .query("unit_price_kes != list_price_kes")
                .shape[0]
            ),
            "description": "unit_price_kes differing from catalog list_price_kes.",
        },
        {
            "dimension": "Integrity",
            "issue_count": int(
                (~tx_df["customer_id"].isin(cust_df["customer_id"])).sum()
                + (~tx_df["product_id"].isin(prod_df["product_id"])).sum()
            ),
            "description": "Orphan customer_id or product_id references in raw_transactions.",
        },
    ]
    return pd.DataFrame(rows)


def clean_data(
    raw_tx: pd.DataFrame,
    raw_cust: pd.DataFrame,
    raw_prod: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    log = []

    def record(table: str, step: str, before: int, after: int, note: str) -> None:
        log.append({
            "table": table,
            "step": step,
            "rows_before": before,
            "rows_after": after,
            "rows_removed": max(0, before - after),
            "note": note,
        })

    # Products
    prod = raw_prod.copy()
    prod["unit_margin_kes"] = prod["list_price_kes"] - prod["unit_cost_kes"]
    prod["margin_pct"] = (prod["unit_margin_kes"] / prod["list_price_kes"]).round(4)
    record("products", "Compute margins", len(raw_prod), len(prod), "Added unit_margin_kes and margin_pct.")

    # Customers (drop PII, pseudonymise ID, generalize signup_date)
    cust = raw_cust.copy()
    drop_pii = [c for c in ["full_name", "email", "phone_number", "national_id"] if c in cust.columns]
    cust = cust.drop(columns=drop_pii)
    cust["customer_id"] = cust["customer_id"].apply(_pseudonymise_id)
    cust["signup_month"] = pd.to_datetime(cust["signup_date"]).dt.to_period("M").astype(str)
    cust = cust.drop(columns=["signup_date"])
    record("customers", "Scrub PII & pseudonymise", len(raw_cust), len(cust), "Dropped PII fields, hashed customer_id, generalized signup_date to month.")

    # Transactions
    tx = raw_tx.copy()

    before = len(tx)
    tx = tx.drop_duplicates(subset=["transaction_id"], keep="first")
    record("transactions", "Deduplicate transaction_id", before, len(tx), "Removed duplicate transaction rows.")

    before = len(tx)
    tx["branch"] = tx["branch"].astype(str).str.strip().str.title()
    tx["payment_method"] = (
        tx["payment_method"]
        .astype(str)
        .str.strip()
        .replace({"mpesa": "M-Pesa", "Mpesa": "M-Pesa", "MPESA": "M-Pesa"})
    )
    record("transactions", "Standardize categories", before, len(tx), "Stripped whitespace and standardized branch and payment_method.")

    before = len(tx)
    tx["discount_pct"] = tx["discount_pct"].fillna(0.0)
    price_lookup = prod.set_index("product_id")["list_price_kes"]
    tx["unit_price_kes"] = tx["unit_price_kes"].fillna(tx["product_id"].map(price_lookup))
    record("transactions", "Impute missing values", before, len(tx), "Filled null discount_pct with 0.0 and null unit_price_kes from catalog.")

    before = len(tx)
    tx["order_date"] = pd.to_datetime(tx["order_date"], errors="coerce")
    tx = tx[
        (tx["quantity"] > 0)
        & (tx["order_date"] >= "2026-01-01")
        & (tx["order_date"] <= "2026-06-30")
    ].copy()
    record("transactions", "Filter invalid records", before, len(tx), "Removed quantity <= 0 and dates outside 2026-01-01 to 2026-06-30.")

    before = len(tx)
    tx["customer_id"] = tx["customer_id"].apply(_pseudonymise_id)
    tx = tx[
        tx["customer_id"].isin(cust["customer_id"])
        & tx["product_id"].isin(prod["product_id"])
    ].copy()
    record("transactions", "Enforce referential integrity", before, len(tx), "Removed orphan foreign keys.")

    tx = tx.merge(prod[["product_id", "unit_cost_kes"]], on="product_id", how="left")
    tx["gross_revenue_kes"] = (tx["quantity"] * tx["unit_price_kes"] * (1.0 - tx["discount_pct"])).round(2)
    tx["cogs_kes"] = (tx["quantity"] * tx["unit_cost_kes"]).round(2)
    tx["gross_profit_kes"] = (tx["gross_revenue_kes"] - tx["cogs_kes"]).round(2)
    tx["order_month"] = tx["order_date"].dt.to_period("M").astype(str)
    tx["quarter"] = np.where(tx["order_date"].dt.month <= 3, "Q1", "Q2")
    tx["order_date"] = tx["order_date"].dt.strftime("%Y-%m-%d")
    tx = tx.drop(columns=["unit_cost_kes"])
    record("transactions", "Engineer metrics", len(tx), len(tx), "Added gross_revenue_kes, cogs_kes, gross_profit_kes, order_month, quarter.")

    clean_tables = {
        "transactions": tx.reset_index(drop=True),
        "customers": cust.reset_index(drop=True),
        "products": prod.reset_index(drop=True),
    }
    return clean_tables, pd.DataFrame(log)
