"""
Financial Assessment Tools

This module provides financial analysis functions for company assessments,
including ratio calculation, financial health scoring, and anomaly detection.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Union, Any

# ==================== DATA PREPARATION FUNCTIONS ====================

def prepare_financial_data(financials: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare and clean financial data for analysis.
    
    Args:
        financials: Raw financial data DataFrame
        
    Returns:
        Cleaned financial data
    """
    if financials is None or financials.empty:
        return pd.DataFrame()
    
    # Create a copy to avoid modifying the original
    cleaned = financials.copy()
    
    # Ensure date column is datetime
    if 'date' in cleaned.columns and not pd.api.types.is_datetime64_any_dtype(cleaned['date']):
        cleaned['date'] = pd.to_datetime(cleaned['date'])
    
    # Replace infinite values with NaN
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)
    
    return cleaned

def get_statement_data(financials: pd.DataFrame, statement_type: str, period_type: str) -> pd.DataFrame:
    """
    Extract specific statement type data from financial dataset.
    
    Args:
        financials: Financial data DataFrame
        statement_type: Type of statement ('Income Statement', 'Balance Sheet', 'Cash Flow')
        period_type: Period type ('quarterly', 'annual')
        
    Returns:
        Filtered statement data
    """
    if financials is None or financials.empty:
        return pd.DataFrame()
    
    # Filter data for the specific statement type and period
    filtered_data = financials[
        (financials['statement_type'] == statement_type) & 
        (financials['period_type'] == period_type)
    ]
    
    # Make sure data is sorted by date (descending)
    if 'date' in filtered_data.columns:
        filtered_data = filtered_data.sort_values('date', ascending=False)
    
    return filtered_data

# ==================== RATIO CALCULATION FUNCTIONS ====================

def calculate_financial_ratios(financials: pd.DataFrame, statement_type: str, period_type: str) -> pd.DataFrame:
    """
    Calculate key financial ratios from financial data.
    
    Args:
        financials: Financial data DataFrame
        statement_type: Statement type to use
        period_type: Period type ('quarterly', 'annual')
        
    Returns:
        DataFrame with calculated ratios
    """
    # Get income statement data
    income_data = get_statement_data(financials, 'Income Statement', period_type)
    
    # Get balance sheet data
    balance_data = get_statement_data(financials, 'Balance Sheet', period_type)
    
    # Get cash flow data
    cashflow_data = get_statement_data(financials, 'Cash Flow', period_type)
    
    # If any data is missing, return empty DataFrame
    if income_data.empty or balance_data.empty:
        return pd.DataFrame()
    
    # Initialize ratios DataFrame with dates
    ratios = pd.DataFrame()
    ratios['date'] = income_data['date']
    
    # Calculate profitability ratios
    if all(col in income_data.columns for col in ['revenue', 'grossProfit']):
        ratios['gross_margin'] = income_data['grossProfit'] / income_data['revenue'].replace(0, np.nan)
    
    if all(col in income_data.columns for col in ['revenue', 'operatingIncome']):
        ratios['operating_margin'] = income_data['operatingIncome'] / income_data['revenue'].replace(0, np.nan)
    
    if all(col in income_data.columns for col in ['revenue', 'netIncome']):
        ratios['net_margin'] = income_data['netIncome'] / income_data['revenue'].replace(0, np.nan)
    
    if all(col in income_data.columns for col in ['netIncome']) and all(col in balance_data.columns for col in ['totalEquity']):
        # Match dates between datasets
        for date in ratios['date']:
            income_row = income_data[income_data['date'] == date]
            balance_row = balance_data[balance_data['date'] == date]
            
            if not income_row.empty and not balance_row.empty:
                net_income = income_row['netIncome'].values[0]
                total_equity = balance_row['totalEquity'].values[0]
                
                if not pd.isna(net_income) and not pd.isna(total_equity) and total_equity != 0:
                    idx = ratios[ratios['date'] == date].index
                    ratios.loc[idx, 'return_on_equity'] = net_income / total_equity
    
    # Calculate liquidity ratios
    if all(col in balance_data.columns for col in ['totalCurrentAssets', 'totalCurrentLiabilities']):
        ratios['current_ratio'] = balance_data['totalCurrentAssets'] / balance_data['totalCurrentLiabilities'].replace(0, np.nan)
    
    if all(col in balance_data.columns for col in ['totalCurrentAssets', 'inventory', 'totalCurrentLiabilities']):
        ratios['quick_ratio'] = (balance_data['totalCurrentAssets'] - balance_data['inventory']) / balance_data['totalCurrentLiabilities'].replace(0, np.nan)
    
    # Calculate solvency ratios
    if all(col in balance_data.columns for col in ['totalDebt', 'totalEquity']):
        ratios['debt_to_equity'] = balance_data['totalDebt'] / balance_data['totalEquity'].replace(0, np.nan)
    
    if all(col in balance_data.columns for col in ['totalDebt']) and all(col in income_data.columns for col in ['ebitda']):
        # Match dates between datasets
        for date in ratios['date']:
            income_row = income_data[income_data['date'] == date]
            balance_row = balance_data[balance_data['date'] == date]
            
            if not income_row.empty and not balance_row.empty:
                ebitda = income_row['ebitda'].values[0] if 'ebitda' in income_row.columns else np.nan
                total_debt = balance_row['totalDebt'].values[0]
                
                if not pd.isna(ebitda) and not pd.isna(total_debt) and ebitda != 0:
                    idx = ratios[ratios['date'] == date].index
                    ratios.loc[idx, 'debt_to_ebitda'] = total_debt / ebitda
    
    # Calculate efficiency ratios
    if all(col in income_data.columns for col in ['revenue']) and all(col in balance_data.columns for col in ['totalAssets']):
        # Match dates between datasets
        for date in ratios['date']:
            income_row = income_data[income_data['date'] == date]
            balance_row = balance_data[balance_data['date'] == date]
            
            if not income_row.empty and not balance_row.empty:
                revenue = income_row['revenue'].values[0]
                total_assets = balance_row['totalAssets'].values[0]
                
                if not pd.isna(revenue) and not pd.isna(total_assets) and total_assets != 0:
                    idx = ratios[ratios['date'] == date].index
                    ratios.loc[idx, 'asset_turnover'] = revenue / total_assets
    
    # Calculate cash flow metrics
    if not cashflow_data.empty:
        if all(col in cashflow_data.columns for col in ['operatingCashFlow']) and all(col in income_data.columns for col in ['netIncome']):
            # Match dates between datasets
            for date in ratios['date']:
                income_row = income_data[income_data['date'] == date]
                cashflow_row = cashflow_data[cashflow_data['date'] == date]
                
                if not income_row.empty and not cashflow_row.empty:
                    operating_cash_flow = cashflow_row['operatingCashFlow'].values[0]
                    net_income = income_row['netIncome'].values[0]
                    
                    if not pd.isna(operating_cash_flow) and not pd.isna(net_income) and net_income != 0:
                        idx = ratios[ratios['date'] == date].index
                        ratios.loc[idx, 'cash_flow_to_income'] = operating_cash_flow / net_income
        
        if all(col in cashflow_data.columns for col in ['operatingCashFlow', 'capitalExpenditure']):
            # Free Cash Flow
            for date in ratios['date']:
                cashflow_row = cashflow_data[cashflow_data['date'] == date]
                
                if not cashflow_row.empty:
                    operating_cash_flow = cashflow_row['operatingCashFlow'].values[0]
                    capital_expenditure = cashflow_row['capitalExpenditure'].values[0]
                    
                    if not pd.isna(operating_cash_flow) and not pd.isna(capital_expenditure):
                        idx = ratios[ratios['date'] == date].index
                        ratios.loc[idx, 'free_cash_flow'] = operating_cash_flow + capital_expenditure  # Note: capex is typically negative
    
    return ratios

def calculate_growth_rates(financials: pd.DataFrame, statement_type: str, period_type: str) -> pd.DataFrame:
    """
    Calculate period-over-period growth rates for key financial metrics.
    
    Args:
        financials: Financial data DataFrame
        statement_type: Statement type to use (usually 'Income Statement')
        period_type: Period type ('quarterly', 'annual')
        
    Returns:
        DataFrame with growth rates
    """
    # Get statement data
    statement_data = get_statement_data(financials, statement_type, period_type)
    
    if statement_data.empty or len(statement_data) < 2:
        return pd.DataFrame()
    
    # Define metrics to calculate growth for
    growth_metrics = [
        'revenue', 
        'grossProfit', 
        'operatingIncome', 
        'netIncome',
        'eps'
    ]
    
    # Initialize growth DataFrame with dates
    growth_df = pd.DataFrame()
    growth_df['date'] = statement_data['date'].iloc[:-1]  # Exclude last period
    
    # Calculate year-over-year or sequential growth
    for metric in growth_metrics:
        if metric in statement_data.columns:
            values = statement_data[metric].values
            
            growth_rates = []
            for i in range(len(values) - 1):
                current = values[i]
                previous = values[i + 1]
                
                if pd.notna(current) and pd.notna(previous) and previous != 0:
                    growth_rate = (current - previous) / abs(previous)
                else:
                    growth_rate = np.nan
                    
                growth_rates.append(growth_rate)
            
            # Add to DataFrame
            growth_df[f'{metric}_growth'] = growth_rates
    
    return growth_df

# ==================== EVALUATION FUNCTIONS ====================

def evaluate_ratio(ratio_name: str, value: float, trend: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Evaluate a financial ratio and return an indicator and assessment.
    
    Args:
        ratio_name: Name of the ratio
        value: Current value of the ratio
        trend: Optional trend direction ('up', 'down', or None)
        
    Returns:
        Tuple of (indicator, status, description)
        where indicator is '🟢', '🟡', or '🔴'
    """
    # Define thresholds for common ratios
    thresholds = {
        'gross_margin': {'good': 0.30, 'concern': 0.15, 'higher_is_better': True},
        'operating_margin': {'good': 0.15, 'concern': 0.05, 'higher_is_better': True},
        'net_margin': {'good': 0.10, 'concern': 0.03, 'higher_is_better': True},
        'return_on_equity': {'good': 0.15, 'concern': 0.05, 'higher_is_better': True},
        'current_ratio': {'good': 1.5, 'concern': 1.0, 'higher_is_better': True},
        'quick_ratio': {'good': 1.0, 'concern': 0.7, 'higher_is_better': True},
        'debt_to_equity': {'good': 1.0, 'concern': 2.0, 'higher_is_better': False},
        'debt_to_ebitda': {'good': 3.0, 'concern': 5.0, 'higher_is_better': False},
        'asset_turnover': {'good': 0.5, 'concern': 0.3, 'higher_is_better': True},
        'cash_flow_to_income': {'good': 1.0, 'concern': 0.5, 'higher_is_better': True}
    }
    
    # Default assessment
    indicator = '🟡'
    status = 'Neutral'
    description = 'No evaluation criteria available.'
    
    # Evaluate based on thresholds if available
    if ratio_name in thresholds:
        threshold = thresholds[ratio_name]
        higher_is_better = threshold['higher_is_better']
        
        if higher_is_better:
            if value >= threshold['good']:
                indicator = '🟢'
                status = 'Strong'
                description = f'Value is above the recommended threshold of {threshold["good"]}'
            elif value <= threshold['concern']:
                indicator = '🔴'
                status = 'Concern'
                description = f'Value is below the concern threshold of {threshold["concern"]}'
            else:
                indicator = '🟡'
                status = 'Adequate'
                description = f'Value is between concern ({threshold["concern"]}) and good ({threshold["good"]}) thresholds'
        else:
            if value <= threshold['good']:
                indicator = '🟢'
                status = 'Strong'
                description = f'Value is below the recommended threshold of {threshold["good"]}'
            elif value >= threshold['concern']:
                indicator = '🔴'
                status = 'Concern'
                description = f'Value is above the concern threshold of {threshold["concern"]}'
            else:
                indicator = '🟡'
                status = 'Adequate'
                description = f'Value is between good ({threshold["good"]}) and concern ({threshold["concern"]}) thresholds'
    
    # Consider trend if provided
    if trend:
        if higher_is_better and trend == 'up' and indicator != '🟢':
            description += ' with a positive trend'
        elif higher_is_better and trend == 'down':
            description += ' with a concerning downward trend'
        elif not higher_is_better and trend == 'down' and indicator != '🟢':
            description += ' with a positive trend'
        elif not higher_is_better and trend == 'up':
            description += ' with a concerning upward trend'
    
    return (indicator, status, description)

def determine_ratio_trend(ratios_df: pd.DataFrame, ratio_name: str, periods: int = 2) -> Optional[str]:
    """
    Determine the trend direction for a specific ratio.
    
    Args:
        ratios_df: DataFrame containing ratio history
        ratio_name: Name of the ratio to evaluate
        periods: Number of periods to consider
        
    Returns:
        Trend direction ('up', 'down', or None)
    """
    if ratios_df.empty or ratio_name not in ratios_df.columns or len(ratios_df) < periods:
        return None
    
    # Get most recent periods
    recent_values = ratios_df[ratio_name].head(periods).values
    
    # Check if all values are valid
    if any(pd.isna(recent_values)):
        return None
    
    # Determine trend
    if recent_values[0] > recent_values[-1]:
        return 'up'
    elif recent_values[0] < recent_values[-1]:
        return 'down'
    else:
        return None

def calculate_financial_health_score(ratios_df: pd.DataFrame) -> Tuple[float, str]:
    """
    Calculate a financial health score (0-100) based on key ratios.
    
    Args:
        ratios_df: DataFrame containing financial ratios
        
    Returns:
        Score (0-100) and assessment category
    """
    if ratios_df.empty or len(ratios_df) < 2:
        return 50, "Insufficient Data"
    
    # Get most recent ratios
    latest_ratios = ratios_df.iloc[0]
    previous_ratios = ratios_df.iloc[1] if len(ratios_df) > 1 else None
    
    # Define weights for each ratio (total = 100)
    weights = {
        'gross_margin': 15,
        'operating_margin': 15,
        'net_margin': 10,
        'return_on_equity': 10,
        'current_ratio': 15,
        'quick_ratio': 5,
        'debt_to_equity': 15,
        'debt_to_ebitda': 5,
        'asset_turnover': 5,
        'cash_flow_to_income': 5
    }
    
    # Initialize score components
    score = 0
    total_weight = 0
    
    # Calculate score components for each ratio
    for ratio_name, weight in weights.items():
        if ratio_name in latest_ratios:
            value = latest_ratios[ratio_name]
            
            # Skip if value is NaN or invalid
            if pd.isna(value) or value == 0 or not np.isfinite(value):
                continue
                
            # Determine trend if previous data available
            trend = None
            if previous_ratios is not None and ratio_name in previous_ratios:
                prev_value = previous_ratios[ratio_name]
                if not pd.isna(prev_value) and np.isfinite(prev_value):
                    trend = 'up' if value > prev_value else 'down'
            
            # Get evaluation
            indicator, _, _ = evaluate_ratio(ratio_name, value, trend)
            
            # Convert indicator to score component
            if indicator == '🟢':
                component_score = 100
            elif indicator == '🟡':
                component_score = 50
            else:  # 🔴
                component_score = 0
            
            # Add weighted component to total score
            score += component_score * weight
            total_weight += weight
    
    # Calculate final score
    if total_weight > 0:
        final_score = score / total_weight
    else:
        return 50, "Insufficient Data"
    
    # Determine assessment category
    if final_score >= 80:
        category = "Strong"
    elif final_score >= 60:
        category = "Healthy"
    elif final_score >= 40:
        category = "Adequate"
    elif final_score >= 20:
        category = "Vulnerable"
    else:
        category = "Distressed"
    
    return final_score, category

def detect_financial_anomalies(financials: pd.DataFrame, ratios_df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Detect potential financial anomalies in the data.
    
    Args:
        financials: DataFrame of financial statements
        ratios_df: DataFrame of calculated ratios
        
    Returns:
        List of dictionaries with anomaly details
    """
    anomalies = []
    
    # Check for sufficient data
    if ratios_df.empty or len(ratios_df) < 3:
        return [{"title": "Insufficient Data", "description": "Not enough historical data to detect anomalies", "severity": "info"}]
    
    # Make sure data is sorted by date (newest first)
    ratios_df = ratios_df.sort_values('date', ascending=False)
    
    # 1. Check for significant margin deterioration
    for margin in ['gross_margin', 'operating_margin', 'net_margin']:
        if margin in ratios_df.columns:
            current = ratios_df[margin].iloc[0]
            previous = ratios_df[margin].iloc[1]
            
            if not pd.isna(current) and not pd.isna(previous) and previous > 0:
                percent_change = (current - previous) / previous
                
                if percent_change < -0.15:  # 15% or more deterioration
                    anomalies.append({
                        "title": f"Significant {margin.replace('_', ' ').title()} Deterioration",
                        "description": f"Decreased by {abs(percent_change)*100:.1f}% from previous period",
                        "severity": "high"
                    })
    
    # 2. Check for liquidity issues
    if 'current_ratio' in ratios_df.columns:
        current_ratio = ratios_df['current_ratio'].iloc[0]
        if not pd.isna(current_ratio) and current_ratio < 1.0:
            anomalies.append({
                "title": "Liquidity Concern",
                "description": f"Current ratio of {current_ratio:.2f} indicates potential short-term liquidity issues",
                "severity": "medium" if current_ratio >= 0.8 else "high"
            })
    
    # 3. Check for increasing leverage
    if 'debt_to_equity' in ratios_df.columns:
        current = ratios_df['debt_to_equity'].iloc[0]
        previous = ratios_df['debt_to_equity'].iloc[1]
        
        if not pd.isna(current) and not pd.isna(previous) and previous > 0:
            percent_change = (current - previous) / previous
            
            if percent_change > 0.25 and current > 1.5:  # 25% or more increase and already high
                anomalies.append({
                    "title": "Rising Leverage",
                    "description": f"Debt-to-equity increased by {percent_change*100:.1f}% to {current:.2f}",
                    "severity": "medium" if current < 2.5 else "high"
                })
    
    # 4. Check for revenue vs. income divergence
    income_stmt = get_statement_data(financials, 'Income Statement', 'quarterly')
    
    if not income_stmt.empty and len(income_stmt) >= 2 and 'revenue' in income_stmt.columns and 'netIncome' in income_stmt.columns:
        current_rev = income_stmt['revenue'].iloc[0]
        prev_rev = income_stmt['revenue'].iloc[1]
        current_income = income_stmt['netIncome'].iloc[0]
        prev_income = income_stmt['netIncome'].iloc[1]
        
        if (not pd.isna(current_rev) and not pd.isna(prev_rev) and 
            not pd.isna(current_income) and not pd.isna(prev_income) and
            prev_rev > 0 and prev_income > 0):
            
            rev_growth = (current_rev - prev_rev) / prev_rev
            income_growth = (current_income - prev_income) / prev_income
            
            # Revenue growing but income falling significantly
            if rev_growth > 0.05 and income_growth < -0.15:
                anomalies.append({
                    "title": "Profitability Pressure",
                    "description": f"Revenue grew by {rev_growth*100:.1f}% but net income fell by {abs(income_growth)*100:.1f}%",
                    "severity": "high"
                })
    
    # 5. Check for cash flow vs. income divergence
    if 'cash_flow_to_income' in ratios_df.columns:
        cf_to_income = ratios_df['cash_flow_to_income'].iloc[0]
        
        if not pd.isna(cf_to_income) and cf_to_income < 0.6:
            anomalies.append({
                "title": "Cash Flow Quality Concern",
                "description": f"Operating cash flow is only {cf_to_income:.1%} of net income, suggesting potential earnings quality issues",
                "severity": "medium" if cf_to_income >= 0.4 else "high"
            })
    
    return anomalies

def analyze_trend_direction(data: pd.DataFrame, metric: str, periods: int = 3) -> Dict[str, Any]:
    """
    Analyze the trend direction and strength for a specific metric.
    
    Args:
        data: DataFrame containing the metric
        metric: Name of the metric to analyze
        periods: Number of recent periods to consider
        
    Returns:
        Dictionary with trend analysis results
    """
    if data.empty or metric not in data.columns or len(data) < periods:
        return {
            "direction": "insufficient_data",
            "icon": "❓",
            "description": "Insufficient data",
            "strength": 0.0,
            "values": []
        }
    
    # Get the most recent periods
    recent_data = data.head(periods)
    
    # Extract values for the specified metric
    values = recent_data[metric].values
    
    # Check if we have enough valid values
    if pd.isna(values).all():
        return {
            "direction": "insufficient_data",
            "icon": "❓",
            "description": "Insufficient data",
            "strength": 0.0,
            "values": []
        }
    
    # Calculate period-over-period changes
    changes = []
    for i in range(len(values) - 1):
        if not pd.isna(values[i]) and not pd.isna(values[i+1]) and values[i+1] != 0:
            changes.append((values[i] - values[i+1]) / abs(values[i+1]))
        else:
            changes.append(np.nan)
    
    # Filter out NaN values
    valid_changes = [c for c in changes if not pd.isna(c)]
    
    if not valid_changes:
        return {
            "direction": "insufficient_data",
            "icon": "❓",
            "description": "Insufficient data",
            "strength": 0.0,
            "values": values.tolist()
        }
    
    # Calculate average change
    avg_change = np.mean(valid_changes)
    
    # Determine direction
    if all(c > 0 for c in valid_changes):
        if avg_change > 0.10:
            direction = "strong_up"
            icon = "📈"
            description = "Strong Upward Trend"
        else:
            direction = "moderate_up"
            icon = "↗️"
            description = "Moderate Upward Trend"
    elif all(c < 0 for c in valid_changes):
        if avg_change < -0.10:
            direction = "strong_down"
            icon = "📉"
            description = "Strong Downward Trend"
        else:
            direction = "moderate_down"
            icon = "↘️"
            description = "Moderate Downward Trend"
    else:
        # Mixed direction - check last 2 periods for recent direction
        if len(valid_changes) >= 2:
            recent_avg = np.mean(valid_changes[:2])
            if recent_avg > 0:
                direction = "recent_up"
                icon = "↗️"
                description = "Recent Upward Trend"
            elif recent_avg < 0:
                direction = "recent_down"
                icon = "↘️"
                description = "Recent Downward Trend"
            else:
                direction = "stable"
                icon = "↔️"
                description = "Stable Trend"
        else:
            direction = "volatile"
            icon = "↔️"
            description = "Volatile Trend"
    
    return {
        "direction": direction,
        "icon": icon,
        "description": description,
        "strength": abs(avg_change),
        "values": values.tolist()
    }

# ==================== COMPARISON FUNCTIONS ====================

def compare_companies(company_data: Dict[str, pd.DataFrame], metric: str, periods: int = 4) -> pd.DataFrame:
    """
    Compare multiple companies based on a specific metric.
    
    Args:
        company_data: Dictionary of company data DataFrames (ticker -> DataFrame)
        metric: Metric to compare
        periods: Number of recent periods to include
        
    Returns:
        DataFrame with comparative data
    """
    comparison = pd.DataFrame()
    
    # Process each company
    for ticker, data in company_data.items():
        if data.empty or metric not in data.columns or len(data) < 1:
            continue
        
        # Get the required periods
        recent_data = data.head(min(periods, len(data))).sort_values('date')
        
        if recent_data.empty:
            continue
        
        # Add data to comparison DataFrame
        for i, row in recent_data.iterrows():
            if pd.isna(row[metric]):
                continue
                
            comparison = comparison.append({
                'ticker': ticker,
                'date': row['date'],
                'value': row[metric]
            }, ignore_index=True)
    
    return comparison

def rank_companies(ratios_data: Dict[str, pd.DataFrame], ratio_name: str) -> pd.DataFrame:
    """
    Rank companies based on a specific financial ratio.
    
    Args:
        ratios_data: Dictionary of company ratios DataFrames (ticker -> DataFrame)
        ratio_name: Name of the ratio to rank by
        
    Returns:
        DataFrame with company rankings
    """
    rankings = []
    
    # Process each company
    for ticker, ratios in ratios_data.items():
        if ratios.empty or ratio_name not in ratios.columns or len(ratios) < 1:
            continue
        
        # Get the most recent value
        latest_value = ratios[ratio_name].iloc[0]
        
        if pd.isna(latest_value):
            continue
        
        # Get the evaluation of this ratio
        indicator, status, _ = evaluate_ratio(ratio_name, latest_value)
        
        # Determine if higher values are better for this ratio
        thresholds = {
            'gross_margin': {'higher_is_better': True},
            'operating_margin': {'higher_is_better': True},
            'net_margin': {'higher_is_better': True},
            'return_on_equity': {'higher_is_better': True},
            'current_ratio': {'higher_is_better': True},
            'quick_ratio': {'higher_is_better': True},
            'debt_to_equity': {'higher_is_better': False},
            'debt_to_ebitda': {'higher_is_better': False},
            'asset_turnover': {'higher_is_better': True},
            'cash_flow_to_income': {'higher_is_better': True}
        }
        
        higher_is_better = thresholds.get(ratio_name, {}).get('higher_is_better', True)
        
        # Add to rankings
        rankings.append({
            'ticker': ticker,
            'value': latest_value,
            'indicator': indicator,
            'status': status
        })
    
    # Create DataFrame and sort
    if rankings:
        df = pd.DataFrame(rankings)
        df = df.sort_values('value', ascending=not higher_is_better)
        
        # Add rank
        df['rank'] = range(1, len(df) + 1)
        
        return df
    
    return pd.DataFrame()

def calculate_industry_metrics(ratios_data: Dict[str, pd.DataFrame], ratio_name: str) -> Dict[str, float]:
    """
    Calculate industry average metrics based on a group of companies.
    
    Args:
        ratios_data: Dictionary of company ratios DataFrames (ticker -> DataFrame)
        ratio_name: Name of the ratio to analyze
        
    Returns:
        Dictionary with industry metrics
    """
    values = []
    
    # Collect the most recent value from each company
    for ticker, ratios in ratios_data.items():
        if ratios.empty or ratio_name not in ratios.columns or len(ratios) < 1:
            continue
        
        # Get the most recent value
        latest_value = ratios[ratio_name].iloc[0]
        
        if pd.isna(latest_value) or not np.isfinite(latest_value):
            continue
        
        values.append(latest_value)
    
    # Calculate metrics if we have enough data
    if len(values) >= 3:
        return {
            'average': np.mean(values),
            'median': np.median(values),
            'min': np.min(values),
            'max': np.max(values),
            'count': len(values)
        }
    
    return {
        'average': np.nan,
        'median': np.nan,
        'min': np.nan,
        'max': np.nan,
        'count': len(values)
    }

# ==================== FORMATTING FUNCTIONS ====================

def format_large_number(num: Union[int, float, None]) -> str:
    """
    Format large numbers with K, M, B suffixes.
    
    Args:
        num: Number to format
        
    Returns:
        Formatted string
    """
    if num is None:
        return "N/A"
    
    if not isinstance(num, (int, float)):
        return str(num)
    
    if abs(num) >= 1_000_000_000:
        return f"${num / 1_000_000_000:.2f}B"
    elif abs(num) >= 1_000_000:
        return f"${num / 1_000_000:.2f}M"
    elif abs(num) >= 1_000:
        return f"${num / 1_000:.2f}K"
    else:
        return f"${num:.2f}"