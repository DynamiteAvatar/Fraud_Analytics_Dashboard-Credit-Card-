import pandas as pd
import time
import random
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime
from sklearn.ensemble import IsolationForest

# 1. Database Connection
engine = create_engine('postgresql://admin:fraud_detection@localhost:5432/fraud_detection')

# 2. Setup ML Model
model = IsolationForest(contamination=0.05, random_state=42)


def run_live_stream():
    cities = ['Chennai', 'Mumbai', 'Bangalore', 'Delhi', 'Hyderabad', 'Kochi']
    # Professional Merchant Categories
    categories = ['Grocery', 'Entertainment', 'Electronics', 'Pharmacy', 'Jewelry', 'Travel', 'Utilities']

    print("🚀 ULTRA-DENSE ANALYTICS STREAM STARTED...")
    print("New Feature: Merchant Category Context & Risk Weighting")

    first_run = True

    while True:
        now = datetime.now()

        # --- GENERATE DATA ---
        amount = random.choice([
            random.uniform(500, 15000),
            random.uniform(100, 5000),
            random.uniform(90000, 150000)
        ])
        city = random.choice(cities)
        merchant = random.choice(categories)
        hour = now.hour

        # --- ANALYTICAL FEATURE ENGINEERING ---

        # 1. Merchant Risk Weighting
        # High-risk categories for money laundering/theft
        cat_weight = 1.8 if merchant in ['Jewelry', 'Electronics', 'Travel'] else 0.6

        # 2. Statistical Deviation
        mean_amt = 5000
        std_dev = 2000
        z_score = (amount - mean_amt) / std_dev

        # 3. Temporal & Spatial Risk
        location_risk = 0.85 if city not in ['Chennai', 'Bangalore'] else 0.15
        time_weight = 1.6 if 1 <= hour <= 4 else 0.4

        # 4. Hybrid Normalized Risk Score
        # Now including cat_weight in the math
        raw_risk = (abs(z_score) * 0.3) + (cat_weight * 0.25) + (location_risk * 0.25) + (time_weight * 0.2)
        normalized_risk = min(1.0, raw_risk / 8)

        is_fraud = normalized_risk > 0.65

        # 5. Automated Mitigation Logic
        if normalized_risk > 0.85:
            action_taken = "BLOCK_CARD_IMMEDIATE"
            priority = "P0 (CRITICAL)"
        elif normalized_risk > 0.65:
            action_taken = "FLAG_FOR_MANUAL_REVIEW"
            priority = "P1 (HIGH)"
        elif normalized_risk > 0.40:
            action_taken = "SEND_SMS_OTP_VERIFICATION"
            priority = "P2 (MEDIUM)"
        else:
            action_taken = "ALLOW_TRANSACTION"
            priority = "P3 (LOW)"

        # --- CONSTRUCTING THE ROW ---
        new_row = pd.DataFrame([{
            'user_id': f"USER_{random.randint(1000, 9999)}",
            'txn_time': now,
            'amount': round(amount, 2),
            'city': city,
            'merchant_category': merchant,  # New Output
            'z_score': round(z_score, 2),
            'location_risk': round(location_risk, 2),
            'merchant_weight': round(cat_weight, 2),  # New Output
            'normalized_risk': round(normalized_risk, 4),
            'priority': priority,
            'action_taken': action_taken,
            'is_fraud': is_fraud
        }])

        # --- DATABASE PUSH ---
        try:
            if first_run:
                new_row.to_sql('analyzed_transactions', engine, if_exists='replace', index=False)
                first_run = False
                print("✅ Schema Expanded: Merchant Category analytics active.")
            else:
                new_row.to_sql('analyzed_transactions', engine, if_exists='append', index=False)

            # --- TERMINAL LOGGING ---
            print(
                f"{now.strftime('%H:%M:%S')} | {merchant:<13} | ₹{round(amount, 2):<9} | Risk: {round(normalized_risk, 2)} | {action_taken}")

        except Exception as e:
            print(f"❌ DB Error: {e}")

        time.sleep(1.2)


if __name__ == "__main__":
    run_live_stream()
