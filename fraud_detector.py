import pandas as pd
from sqlalchemy import create_engine

# Database Connection
engine = create_engine('postgresql://admin:fraud_detection@localhost:5432/fraud_detection')


def analyze_behavior():
    # 1. Pull data
    df = pd.read_sql('raw_transactions', engine)
    df['txn_time'] = pd.to_datetime(df['txn_time'])
    df = df.sort_values(['user_id', 'txn_time'])

    # 2. Behavioral Calculations
    # Average spend per user
    user_avg = df.groupby('user_id')['amount'].transform('mean')

    # 3. Apply Heuristics (The "Manual" Learning)
    df['risk_score'] = 0

    # Rule 1: Amount Outliers
    df.loc[df['amount'] > (user_avg * 3), 'risk_score'] += 30

    # Rule 2: Night Owl (1 AM - 5 AM)
    df.loc[df['txn_time'].dt.hour.isin([1, 2, 3, 4, 5]), 'risk_score'] += 20

    # Rule 3: City Hopping (Check if city changed from previous txn)
    df['prev_city'] = df.groupby('user_id')['city'].shift(1)
    df.loc[(df['city'] != df['prev_city']) & (df['prev_city'].notnull()), 'risk_score'] += 50

    # 4. Final Flagging
    df['is_fraud'] = df['risk_score'] >= 70

    # 5. Push to Postgres
    df.to_sql('analyzed_transactions', engine, if_exists='replace', index=False)
    print("Behavioral analysis complete. Table 'analyzed_transactions' created.")


if __name__ == "__main__":
    analyze_behavior()
