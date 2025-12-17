# Asset Returns Analyzer

A Python tool for computing historical asset returns using Shiller data, FRED 3-month Treasury rates (TB3MS), and World Bank gold prices. This project provides clean, unified data processing for investment research and portfolio analysis.

## Features
- **Data Integration**: Merges Shiller S&P 500 data with Treasury rates and gold prices
- **Return Calculations**: Computes total returns for stocks, bonds, gold, and T-bills
- **Inflation Adjustment**: Includes CPI-based inflation calculations
- **Automated Pipeline**: From raw data download to processed CSV output

## Installation
```bash
pip install pandas numpy
```

## Data Sources
- Robert Shiller's U.S. Stock Market Data
- FRED 3-Month Treasury Bill Secondary Market Rate (TB3MS)
- World Bank Gold Prices

## Output
The script produces a CSV file with columns for S&P 500, dividends, earnings, CPI, bond total returns, equity total returns, gold returns, T-bill returns, and inflation-adjusted returns.
