# Agentic Explorer DataStore Plan

This document outlines the phased approach for building and expanding our financial data repository for the Agentic Explorer project.

## Phase 1: Core Financial Data 

In this initial phase, we'll focus on data readily available through the Financial Modeling Prep (FMP) API to build a functional foundation.

### Companies for Initial Implementation
- NVDA (NVIDIA)
- MSFT (Microsoft)
- AAPL (Apple)
- TSLA (Tesla)
- AMZN (Amazon)

### Phase 1 Data Components

#### Stock Price Data
- [x] Daily stock prices (5 years)
- [x] Major index data (S&P 500, NASDAQ, Dow Jones)
- [x] Basic peer comparison data

#### Financial Statements
- [x] Quarterly income statements (5 years)
- [x] Quarterly balance sheets (5 years)
- [x] Quarterly cash flow statements (5 years)
- [x] Annual financial statements (5 years)

#### SEC Filings
- [x] 10-K annual reports (5 years)
- [x] 10-Q quarterly reports (5 years)
- [x] 8-K significant event reports (selective, last 2 years)

#### Earnings Information
- [x] Earnings call transcripts (8 quarters)
- [x] Earnings surprises and estimates

#### News and Sentiment
- [x] Company-specific news articles (FMP News by Ticker API)
- [x] Basic sentiment data (FMP Sentiment API)

#### Analyst Coverage
- [x] Analyst ratings history
- [x] Price targets
- [x] Consensus estimates

## Phase 2: Enhanced Financial Context

Building on the foundation, Phase 2 adds more contextual data and extends the historical range.

#### Stock Price Data (Extensions)
- [ ] Extended history (10 years)
- [ ] More detailed peer comparison (5-7 competitors per company)
- [ ] Sector-specific indices
- [ ] VIX correlation data

#### Financial Analysis
- [ ] Pre-calculated financial ratios
- [ ] Growth rate calculations
- [ ] Peer comparative analysis
- [ ] Industry average benchmarks

#### SEC Filings (Extensions)
- [ ] Proxy statements (DEF 14A)
- [ ] Insider trading reports (Forms 3, 4, 5)
- [ ] Full 8-K coverage (5 years)

#### News and Sentiment (Extensions)
- [ ] Curated significant event timeline
- [ ] Topic categorization of news
- [ ] Extended sentiment analysis
- [ ] Industry news that impacts target companies

#### Macro Context
- [ ] Interest rate data
- [ ] Inflation data
- [ ] Industry-specific economic indicators
- [ ] Market sector rotation data

## Phase 3: Advanced and Alternative Data

The final phase incorporates alternative data sources and advanced analytics to provide deeper insights.

#### Alternative Data
- [ ] Google Trends data for product interest
- [ ] Web traffic data (if publicly available)
- [ ] Social media sentiment trends
- [ ] App download statistics (for relevant companies)
- [ ] Patent filing activity

#### Advanced Analytics
- [ ] Pre-calculated technical indicators
- [ ] Volatility measures
- [ ] Correlation matrices
- [ ] Factor analysis results

#### Enhanced News Analysis
- [ ] Event impact modeling
- [ ] News classification by materiality
- [ ] Supply chain news mapping
- [ ] Competitive landscape mapping

#### Strategic Context
- [ ] Product launch timeline
- [ ] Executive change history
- [ ] Competitive product comparison
- [ ] Market share evolution data

## Implementation Notes

### Data Collection Automation

We'll create scripts to automate the collection and organization of data:

```python
# Example script structure
def fetch_and_organize_company_data(ticker, years=5):
    """
    Fetch and organize all Phase 1 data for a given company
    """
    # Create necessary directories
    os.makedirs(f"dataStore/{ticker}/price_data", exist_ok=True)
    os.makedirs(f"dataStore/{ticker}/financials/quarterly", exist_ok=True)
    os.makedirs(f"dataStore/{ticker}/financials/annual", exist_ok=True)
    os.makedirs(f"dataStore/{ticker}/filings", exist_ok=True)
    os.makedirs(f"dataStore/{ticker}/earnings_calls", exist_ok=True)
    os.makedirs(f"dataStore/{ticker}/news", exist_ok=True)
    os.makedirs(f"dataStore/{ticker}/analyst", exist_ok=True)
    
    # Fetch daily prices
    fetch_daily_prices(ticker, years)
    
    # Fetch financial statements
    fetch_financial_statements(ticker, years)
    
    # Fetch SEC filings
    fetch_sec_filings(ticker, years)
    
    # Fetch earnings data
    fetch_earnings_data(ticker, years)
    
    # Fetch news and sentiment
    fetch_news_and_sentiment(ticker, years)
    
    # Fetch analyst coverage
    fetch_analyst_coverage(ticker, years)
```

### Data Quality Considerations

For each phase, we'll implement quality checks and enrichment:

1. **Completeness Check**: Ensure no significant gaps in time series data
2. **Consistency Check**: Validate data formats and units across sources
3. **Deduplication**: Remove redundant information, especially in news
4. **Normalization**: Standardize formats for easier agent consumption
5. **Metadata Enrichment**: Add contextual tags to improve searchability

### File Naming Conventions

We'll adopt consistent naming conventions for all files:

- Stock data: `{ticker}_daily_prices_{start_date}_{end_date}.csv`
- Financials: `{ticker}_{statement_type}_{period}_{year}{quarter}.json`
- Filings: `{ticker}_{filing_type}_{date}.txt`
- News: `{ticker}_news_{date}_{id}.txt`
- Sentiment: `{ticker}_sentiment_{start_date}_{end_date}.csv`

## Data Storage Requirements

### Phase 1 Estimates
- Stock price data: ~10MB per company
- Financial statements: ~50MB per company
- SEC filings: ~100MB per company
- Earnings data: ~20MB per company
- News articles: ~200MB per company
- Analyst data: ~5MB per company

**Total per company**: ~385MB
**Total for 5 companies**: ~1.9GB

### Phase 2-3 Estimates
- Approximately 3x Phase 1 requirements
- **Projected total at Phase 3**: ~6GB

## FMP API Endpoints Reference

For Phase 1 implementation, we'll use these primary FMP API endpoints:

- Historical Stock Prices: `/historical-price-full/{ticker}`
- Financial Statements: `/income-statement/{ticker}`, `/balance-sheet-statement/{ticker}`, `/cash-flow-statement/{ticker}`
- SEC Filings: `/sec_filings/{ticker}`
- Earnings: `/earnings-call-transcript/{ticker}`, `/earnings-surprises/{ticker}`
- News: `/stock_news?tickers={ticker}`, `/stock-news-sentiments/{ticker}`
- Analyst: `/analyst-estimates/{ticker}`, `/upgrades-downgrades?symbol={ticker}`

## Next Steps

1. Create the data collection script for Phase 1
2. Implement quality checks and validation
3. Document the structure of each data file 
4. Build basic agent interactions using Phase 1 data
5. Evaluate data gaps and prioritize Phase 2 additions

## Notes on Future Data Sources

As we move to Phases 2 and 3, we'll likely need to incorporate additional data sources beyond FMP:

- Yahoo Finance API for alternative market data
- Alpha Vantage for additional financial metrics
- SEC EDGAR direct access for fuller filing coverage
- Google Trends API for product interest data
- News APIs for broader coverage