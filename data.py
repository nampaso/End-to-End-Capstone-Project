import os
import numpy as np
import pandas as pd


def generate_dataset(seed: int = 42, output_dir: str = "data") -> None:
    rng = np.random.default_rng(seed)
    os.makedirs(output_dir, exist_ok=True)

    products = pd.DataFrame([
        ("PRD-001", "ProBook 14 Laptop", "Laptops", 62000, 85000),
        ("PRD-002", "UltraSlim X15 Laptop", "Laptops", 88000, 120000),
        ("PRD-003", "StudentMate 13 Laptop", "Laptops", 41000, 56000),
        ("PRD-004", "WorkStation Pro 16", "Laptops", 115000, 155000),
        ("PRD-005", "Galaxy A55 5G", "Smartphones", 34000, 46000),
        ("PRD-006", "iPhone 15 128GB", "Smartphones", 89000, 118000),
        ("PRD-007", "Redmi Note 13 Pro", "Smartphones", 24000, 33000),
        ("PRD-008", "Pixel 8a", "Smartphones", 48000, 65000),
        ("PRD-009", "27-inch IPS Monitor", "Monitors & Audio", 19000, 28000),
        ("PRD-010", "NoiseCancel ANC Headphones", "Monitors & Audio", 8500, 14500),
        ("PRD-011", "Bluetooth Soundbar", "Monitors & Audio", 11000, 18000),
        ("PRD-012", "USB-C Multiport Hub", "Accessories", 2200, 4200),
        ("PRD-013", "Wireless Ergonomic Mouse", "Accessories", 1500, 2800),
        ("PRD-014", "65W GaN Fast Charger", "Accessories", 1800, 3400),
        ("PRD-015", "Laptop Backpack 15.6", "Accessories", 2500, 4500),
    ], columns=["product_id", "product_name", "category", "unit_cost_kes", "list_price_kes"])

    n_customers = 850
    cities = ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"]
    tiers = ["Bronze", "Silver", "Gold"]
    signup_dates = pd.date_range("2024-01-01", "2026-06-25", freq="D")

    customers = pd.DataFrame({
        "customer_id": [f"CUST-{1000 + i}" for i in range(n_customers)],
        "full_name": [f"Customer {i}" for i in range(n_customers)],
        "email": [f"customer{i}@example.co.ke" for i in range(n_customers)],
        "phone_number": [f"+2547{rng.integers(10000000, 99999999)}" for _ in range(n_customers)],
        "national_id": [str(rng.integers(20000000, 39999999)) for _ in range(n_customers)],
        "city": rng.choice(cities, size=n_customers, p=[0.38, 0.20, 0.14, 0.15, 0.13]),
        "signup_date": rng.choice(signup_dates, size=n_customers),
        "loyalty_tier": rng.choice(tiers, size=n_customers, p=[0.55, 0.30, 0.15]),
    })

    n_tx = 4200
    h1_dates = pd.date_range("2026-01-01", "2026-06-30", freq="D")
    branches = ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"]

    tx_rows = []
    for i in range(n_tx):
        dt = pd.Timestamp(rng.choice(h1_dates))
        is_q2 = dt.month >= 4
        b_probs = [0.40, 0.17, 0.15, 0.13, 0.15] if is_q2 else [0.36, 0.23, 0.14, 0.17, 0.10]
        branch = rng.choice(branches, p=b_probs)
        cust = customers.iloc[rng.integers(0, n_customers)]

        if cust["loyalty_tier"] == "Gold":
            p_probs = [0.13, 0.12, 0.06, 0.08, 0.08, 0.10, 0.04, 0.06, 0.07, 0.06, 0.04, 0.04, 0.04, 0.04, 0.04]
        else:
            p_probs = [0.05, 0.03, 0.07, 0.02, 0.08, 0.04, 0.11, 0.06, 0.06, 0.07, 0.06, 0.09, 0.10, 0.08, 0.08]

        prod = products.iloc[rng.choice(len(products), p=p_probs)]
        qty = int(rng.choice([1, 2, 3], p=[0.78, 0.17, 0.05]))
        disc = float(rng.choice([0.0, 0.05, 0.10, 0.15], p=[0.55, 0.25, 0.15, 0.05]))
        pay = rng.choice(["M-Pesa", "Card", "Bank Transfer", "Cash"], p=[0.58, 0.24, 0.12, 0.06])
        status = rng.choice(["Completed", "Returned"], p=[0.95, 0.05])

        tx_rows.append({
            "transaction_id": f"TX-{10000 + i}",
            "order_date": dt.strftime("%Y-%m-%d"),
            "branch": branch,
            "customer_id": cust["customer_id"],
            "product_id": prod["product_id"],
            "quantity": qty,
            "unit_price_kes": float(prod["list_price_kes"]),
            "discount_pct": disc,
            "payment_method": pay,
            "order_status": status,
        })

    tx_df = pd.DataFrame(tx_rows)

    # Inject realistic quality anomalies for audit & cleaning pipeline
    dups = tx_df.sample(35, random_state=seed)
    tx_df = pd.concat([tx_df, dups], ignore_index=True)

    tx_df.loc[0:25, "branch"] = " nairobi "
    tx_df.loc[26:45, "branch"] = "MOMBASA"
    tx_df.loc[46:65, "payment_method"] = "mpesa"

    tx_df.loc[100:139, "discount_pct"] = np.nan
    tx_df.loc[140:154, "unit_price_kes"] = np.nan

    tx_df.loc[200:211, "quantity"] = -1
    tx_df.loc[220:227, "order_date"] = "2027-01-15"
    tx_df.loc[250:254, "customer_id"] = "CUST-9999"

    products.to_csv(os.path.join(output_dir, "raw_products.csv"), index=False)
    customers.to_csv(os.path.join(output_dir, "raw_customers.csv"), index=False)
    tx_df.to_csv(os.path.join(output_dir, "raw_transactions.csv"), index=False)


if __name__ == "__main__":
    generate_dataset()
