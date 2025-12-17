import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Load the historical data
with open('historical_data.json', 'r') as f:
    data = json.load(f)

# Convert to DataFrame for easier analysis
df = pd.DataFrame(data)

# Basic info about the dataset
print(f"Data spans from {df['date'].min()} to {df['date'].max()}")
print(f"Total records: {len(df)}")

# Convert date to datetime for proper sorting and plotting
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

# Show basic statistics
print("\nBasic Statistics:")
numeric_columns = df.select_dtypes(include=['number']).columns
print(df[numeric_columns].describe())

# Extract the most recent data point
latest = df.iloc[-1]
print("\nMost Recent Data Point:")
for col in df.columns:
    print(f"{col}: {latest[col]}")

# Print the first few rows to see structure
print("\nSample Data (First 5 Rows):")
print(df.head())

# Check for missing values
missing = df.isnull().sum()
print("\nMissing Values Per Column:")
print(missing[missing > 0])

# Time series analysis of key metrics
print("\nMonthly Average Metrics:")
monthly_avg = df.set_index('date').resample('M').mean()
print(monthly_avg[['validators', 'entry_wait', 'exit_wait', 'staked_percent', 'apr']].tail())

# Check for columns that have changed their meaning or structure over time
print("\nUnique values in select columns:")
for col in ['current_entry_churn', 'current_exit_churn']:
    if col in df.columns:
        print(f"{col}: {df[col].unique()[:5]}...")

# Optional: Visualize trends
# Uncomment these lines if you want to visualize the data
'''
plt.figure(figsize=(12, 8))
plt.subplot(2, 2, 1)
plt.plot(df['date'], df['validators'])
plt.title('Validator Count Over Time')

plt.subplot(2, 2, 2)
plt.plot(df['date'], df['entry_wait'], label='Entry Wait (days)')
plt.plot(df['date'], df['exit_wait'], label='Exit Wait (days)')
plt.title('Wait Times')
plt.legend()

plt.subplot(2, 2, 3)
plt.plot(df['date'], df['staked_percent'])
plt.title('Percent ETH Staked')

plt.subplot(2, 2, 4)
plt.plot(df['date'], df['apr'])
plt.title('Staking APR')

plt.tight_layout()
plt.show()
'''

# Generate summary insights
print("\nKey Insights:")
validator_growth = df['validators'].iloc[-1] - df['validators'].iloc[0]
validator_growth_pct = (validator_growth / df['validators'].iloc[0]) * 100
print(f"Validator Growth: {validator_growth} ({validator_growth_pct:.2f}%)")

if 'apr' in df.columns and not df['apr'].isnull().all():
    apr_change = df['apr'].iloc[-1] - df['apr'].dropna().iloc[0]
    print(f"APR Change: {apr_change:.2f}%")

entry_wait_change = df['entry_wait'].iloc[-1] - df['entry_wait'].iloc[0]
print(f"Entry Wait Time Change: {entry_wait_change:.2f} days")

# Optional: Save processed data to CSV for further analysis
# df.to_csv('processed_historical_data.csv', index=False)