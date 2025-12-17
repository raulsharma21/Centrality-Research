# Ethereum Validator Centrality Research

Research analyzing the relationship between Ethereum validator centralization and market dynamics, including volatility, returns, and trading patterns.

## Project Structure

```
├── data/
│   ├── raw/                    # Original data files (not tracked in git)
│   └── processed/              # Generated regression datasets (not tracked in git)
├── notebooks/                  # Jupyter notebooks for analysis
├── scripts/                    # Python scripts for data processing and visualization
├── archive/                    # Reference R scripts
├── results/                    # Generated plots and outputs (not tracked in git)
└── FILE_DEPENDENCIES.md        # Documentation of data flow and dependencies
```

## Data Files

### Raw Data (place in `data/raw/`)
- `ethereum.xlsx` - Ethereum price and market data
- `crypto_market.xlsx` - Broader crypto market data
- `ETH_Block_Data_Processed.csv` - Processed Ethereum block data
- `ETH_Block_Data_Cleaned.csv` - Cleaned Ethereum block data

### Processed Data (generated in `data/processed/`)
- `eth_regression_data.csv` - Block-level regression dataset
- `daily_regression_data.csv` - Daily aggregated regression dataset
- `ETH_daily_yf_data.csv` - Yahoo Finance ETH data
- `var_model_data.xlsx` - VAR model input data

## Key Notebooks

### Data Processing
- `ETH_analysis.ipynb` - Processes raw block data → generates `eth_regression_data.csv`
- `ETH_daily_analysis.ipynb` - Aggregates daily data → generates `daily_regression_data.csv`

### Analysis
- `VAR.ipynb`, `ETH_VAR.ipynb`, `Daily_VAR.ipynb` - Vector autoregression models
- `2SLS.ipynb` - Two-stage least squares instrumental variable analysis
- `event_study_basic.ipynb`, `event_study_regression.ipynb` - Event study analysis
- `Sharpe.ipynb` - Sharpe ratio analysis by centralization periods

## Scripts

### Python Scripts (in `scripts/`)
- `preprocess.py` - Data preprocessing utilities
- `sharpe_comparison.py` - Generate Sharpe ratio comparison plots
- `explore_data.py` - Data exploration utilities
- `dynamodb.py`, `bulk_upload.py` - AWS DynamoDB upload tools

### R Scripts (in `archive/`)
- Reference implementations (not actively maintained)

## Setup

1. Install Python dependencies:
```bash
pip install pandas numpy matplotlib seaborn yfinance scipy statsmodels jupyter boto3 python-dotenv
```

2. Place raw data files in `data/raw/`

3. Run data processing notebooks:
   - First: `ETH_analysis.ipynb`
   - Then: `ETH_daily_analysis.ipynb`

4. Run analysis notebooks as needed

## Environment Variables

For AWS DynamoDB scripts, create a `.env` file:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

## Results

Analysis outputs (plots, CSV results) are saved to `results/` directory.

## Research Focus

- Measuring validator centralization using various metrics (top-N validators, HHI, Gini coefficient)
- Analyzing impact on ETH price volatility and returns
- Comparing ETH performance vs market benchmarks during high/low centralization periods
- Causal inference using instrumental variables and event studies

