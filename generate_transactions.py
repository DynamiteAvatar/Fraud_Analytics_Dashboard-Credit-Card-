import pandas as pd
import random
from faker import Faker
from sqlalchemy import create_engine
from datetime import datetime, timedelta

fake = Faker(['en_IN'])  # Indian names and locations
engine = create_engine('postgresql://admin:fraud_detection@localhost:5432/fraud_detection')


def generate_data(n=1000):
    data = []
    users = [f"USER_{i}" for i in range(101, 110)]

    for _ in range(n):
        user = random.choice(users)
        timestamp = datetime.now() - timedelta(minutes=random.randint(0, 10000))
        amount = round(random.uniform(10, 50000), 2)
        city = fake.city()

        # Adding a "Hidden" Fraud Pattern: Impossible Geography
        if random.random() < 0.05:  # 5% chance of a "teleportation" fraud
            city = "MUMBAI"
            amount = 99999  # Suspiciously high

        data.append([user, timestamp, amount, city])

    df = pd.DataFrame(data, columns=['user_id', 'txn_time', 'amount', 'city'])
    df.to_sql('raw_transactions', engine, if_exists='replace', index=False)
    print(f"Successfully loaded {n} unlabeled transactions into Postgres!")


if __name__ == "__main__":
    generate_data(2000)
