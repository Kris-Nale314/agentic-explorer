# Agentic Explorer DataStore Plan - Updated

This document outlines the current state and future directions for the financial data repository that powers the Agentic Explorer project's multi-agent intelligence systems.

## Current Implementation Status

The Agentic Explorer DataStore currently contains comprehensive financial data for the following companies:

- NVDA (NVIDIA)
- F (Ford)
- BA (Boeing)
- DELL (Dell Technologies)
- MSFT (Microsoft)
- TSLA (Tesla)
- TSM (TSMC)
- ACN (Accenture)

This provides a diverse cross-section of technology, manufacturing, and consulting sectors for our agent-based analysis.

### Current Data Components

#### Company-Specific Data
- ✅ Company profiles and basic information
- ✅ Financial statements (income, balance sheet, cash flow)
- ✅ Stock price histories 
- ✅ Earnings call transcripts
- ✅ SEC filing metadata
- ✅ Company-specific news articles

#### Market-Wide Data
- ✅ Economic indicators
- ✅ Treasury rates
- ✅ Market indexes (S&P 500, Dow Jones, NASDAQ)
- ✅ Sector P/E ratios

#### Event-Based Data
- ✅ Material events (8-K filings)
- ✅ Insider trading data

#### Relationship Data
- ✅ Peer relationships
- ✅ Supply chain relationships

## Data Handling Behavior

**Important Note about Data Collection Process:**
- The current data collection scripts **will overwrite existing files** when run again
- Each data collection function uses standard file writing modes that replace content
- Examples include `json.dump(data, f, indent=2)` using the `"w"` mode and `df.to_parquet()` without append options

For adding new companies or updating existing ones:
1. Running `collect_company_data(ticker, years)` for a new ticker will create and populate a new company directory
2. Running it for an existing ticker will replace that company's data files with fresh data
3. Running `collect_all_data(tickers, years)` will refresh all specified companies and shared data

## Phase 2: Enhanced Data Scope

Building on our solid foundation, we plan to expand along the following dimensions:

### New Companies to Add
- AMZN (Amazon)
- AAPL (Apple)
- INTC (Intel)
- GOOG (Alphabet/Google)
- JPM (JPMorgan Chase)
- UNH (UnitedHealth Group)
- PFE (Pfizer)
- XOM (Exxon Mobil)

This expansion will provide broader sector coverage including consumer tech, finance, healthcare, and energy.

### Extended Historical Range
- Increase historical data range from 3 to 5 years where appropriate
- Provide agents with longer-term patterns for trend analysis

### Enhanced Financial Context
- Add pre-calculated financial ratios for easier agent analysis
- Include industry average benchmarks for comparative analysis
- Incorporate sector-specific economic indicators

### Improved Relationship Mapping
- Expand peer comparison data (5-7 competitors per company)
- Enhance supply chain mapping with deeper upstream/downstream connections
- Add cross-industry relationship data to identify hidden correlations

## Phase 3: Advanced Data Integration

Our long-term vision includes integrating more sophisticated data sources:

### Alternative Data Sources
- Google Trends data for product interest (via PyTrends)
- Social media sentiment aggregates (if publicly available)
- Patent filing activity (via USPTO public data)

### Advanced Analytics
- Technical indicators pre-calculation
- Cross-asset correlation matrices
- Market sentiment indices

### Strategic Context Enhancement
- Executive change history
- Product launch timeline integration
- Competitive product mapping

## Implementation Plan

### Short-Term Actions (Next 2 Weeks)
1. **Backup Current DataStore**:
   ```bash
   # Create a timestamped backup before major changes
   cp -r dataStore dataStore_backup_$(date +%Y%m%d)
   ```

2. **Add New Companies Individually**:
   ```bash
   # Run for each new company to avoid disrupting existing data
   python -m utils.run_data_collector --single AMZN --years 3
   python -m utils.run_data_collector --single AAPL --years 3
   # ... and so on for other new companies
   ```

3. **Update Market-Wide Data**:
   ```bash
   # Refresh shared data without touching company data
   python -m utils.run_data_collector --market --years 3
   ```

### Mid-Term Enhancements (Next Month)
1. **Modify Collector Scripts**:
   - Add options to preserve/merge existing data
   - Implement incremental updates for efficiency
   - Add data validation and gap detection

2. **Create Data Quality Reports**:
   - Develop scripts to check data completeness
   - Identify missing periods or anomalies
   - Generate coverage statistics for agent evaluation

### Long-Term Strategy (Next Quarter)
1. **Data Integration Framework**:
   - Design systems to integrate alternative data sources
   - Build connectors for additional APIs
   - Implement data normalization for cross-source analysis

2. **Signal Index Foundations**:
   - Begin preliminary calculation of signal indices
   - Store pre-computed metrics for agent efficiency
   - Create benchmark values for comparison

## Usage with Agentic Explorer

The DataStore is designed to support all key application modules:

1. **Company Deep Dive Analysis**: Leverages company-specific data
2. **News Impact Validator**: Uses news and price correlation data
3. **Prediction Challenge Simulator**: Relies on historical patterns
4. **Agent Resilience Tester**: Tests with complete and partial data
5. **Multi-Company Comparative Analysis**: Utilizes relationship mapping

## Data Storage Considerations

Current storage requirements are approximately 350-400MB per company, with market-wide data adding another 250MB. As we expand to include more companies and extend historical ranges, we anticipate the following:

- **Current DataStore**: ~3-4GB
- **Phase 2 Expansion**: ~8-10GB
- **Phase 3 (with Alternative Data)**: ~15-20GB

This remains well within reasonable limits for local development and exploration.

## Notes on API Usage

Our data collection relies primarily on the Financial Modeling Prep (FMP) API. Be mindful of rate limits when collecting data for multiple companies:

- Basic API plan: 250-300 requests per day
- Collecting full data for a single company requires ~25-30 API calls
- Consider spreading large collection jobs across multiple days

## Next Steps

1. Backup current DataStore before any major updates
2. Add priority new companies one at a time
3. Consider modifying collection scripts to support incremental updates
4. Expand historical range for key companies once core coverage is complete