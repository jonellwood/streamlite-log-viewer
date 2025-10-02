#!/usr/bin/env python3
"""
Data Analysis Module
Handles timeframe filtering, error analysis, and metrics generation.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from collections import Counter

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """Handles analysis of parsed log data with filtering and aggregation."""
    
    def __init__(self, target_date: datetime = None, time_filter_enabled: bool = True):
        """
        Initialize analyzer with target analysis date.
        
        Args:
            target_date (datetime): The date to analyze (defaults to yesterday)
            time_filter_enabled (bool): Whether to apply the 9 AM - 2 PM timeframe filter
        """
        if target_date is None:
            self.target_date = datetime.now() - timedelta(days=1)
        else:
            self.target_date = target_date
        
        self.time_filter_enabled = time_filter_enabled
        
        # Define the critical time window (9 AM - 2 PM)
        self.start_time = self.target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        self.end_time = self.target_date.replace(hour=14, minute=0, second=0, microsecond=0)
        
        logger.info(f"Analysis window: {self.start_time} to {self.end_time}")
    
    def filter_by_timeframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter DataFrame to only include logs within the target timeframe.
        
        Args:
            df (pd.DataFrame): Input DataFrame with timestamp column
            
        Returns:
            pd.DataFrame: Filtered DataFrame
        """
        if df.empty or 'timestamp' not in df.columns:
            logger.warning("DataFrame is empty or missing timestamp column")
            return df
        
        # Convert timestamp to datetime if not already
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Remove rows with invalid timestamps
        df = df.dropna(subset=['timestamp'])
        
        # Filter by time window
        mask = (df['timestamp'] >= self.start_time) & (df['timestamp'] <= self.end_time)
        filtered_df = df[mask].copy()
        
        logger.info(f"Timeframe filter: {len(df)} -> {len(filtered_df)} rows "
                   f"({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})")
        
        return filtered_df
    
    def calculate_error_frequencies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate error frequencies by category and time intervals.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            
        Returns:
            pd.DataFrame: Error frequency summary
        """
        if df.empty:
            return pd.DataFrame()
        
        # Create time bins (5-minute intervals)
        df['time_bin'] = df['timestamp'].dt.floor('5T')
        
        # Flatten error categories and count them
        error_data = []
        for _, row in df.iterrows():
            if row['error_categories']:
                for category in row['error_categories']:
                    error_data.append({
                        'timestamp': row['timestamp'],
                        'time_bin': row['time_bin'],
                        'category': category,
                        'file_path': row['file_path'],
                        'transaction_id': row.get('transaction_id'),
                        'log_level': row['log_level']
                    })
        
        if not error_data:
            logger.info("No errors found in the timeframe")
            return pd.DataFrame()
        
        error_df = pd.DataFrame(error_data)
        
        # Calculate frequencies
        frequency_summary = error_df.groupby(['category', 'time_bin']).agg({
            'category': 'count',
            'transaction_id': 'nunique',
            'file_path': lambda x: list(set(x))
        }).rename(columns={'category': 'count', 'transaction_id': 'unique_transactions'})
        
        return frequency_summary.reset_index()
    
    def identify_peak_periods(self, df: pd.DataFrame, window_minutes: int = 5) -> List[Dict]:
        """
        Identify time periods with highest error activity.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            window_minutes (int): Time window size in minutes
            
        Returns:
            list: List of peak period information
        """
        if df.empty or 'timestamp' not in df.columns:
            return []
        
        # Create time bins
        df['time_bin'] = df['timestamp'].dt.floor(f'{window_minutes}T')
        
        # Count errors per time bin
        error_counts = df[df['has_error'] == True].groupby('time_bin').agg({
            'has_error': 'count',
            'error_categories': lambda x: [cat for sublist in x for cat in sublist],
            'file_path': lambda x: list(set(x)),
            'transaction_id': lambda x: list(set([tid for tid in x if tid is not None]))
        }).rename(columns={'has_error': 'error_count'})
        
        if error_counts.empty:
            return []
        
        # Find top 5 peak periods
        top_periods = error_counts.nlargest(5, 'error_count')
        
        peak_periods = []
        for time_bin, data in top_periods.iterrows():
            category_counts = Counter(data['error_categories'])
            
            peak_periods.append({
                'time_period': f"{time_bin.strftime('%H:%M')} - {(time_bin + timedelta(minutes=window_minutes)).strftime('%H:%M')}",
                'start_time': time_bin,
                'error_count': data['error_count'],
                'top_error_categories': dict(category_counts.most_common(3)),
                'affected_files': len(data['file_path']),
                'unique_transactions': len([t for t in data['transaction_id'] if t])
            })
        
        return peak_periods
    
    def analyze_error_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze patterns in error data.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            
        Returns:
            dict: Pattern analysis results
        """
        if df.empty:
            return {'total_errors': 0, 'error_categories': {}, 'patterns': [], 'total_warnings': 0, 'total_errors_strict': 0}
        
        error_df = df[df['has_error'] == True]
        
        # Count errors by category
        all_categories = [cat for cats in error_df['error_categories'] for cat in cats]
        category_counts = Counter(all_categories)
        
        # Count errors by log level
        level_counts = error_df['log_level'].value_counts().to_dict()
        
        # Count errors by file
        file_counts = error_df['file_path'].value_counts().head(10).to_dict()
        
        # Totals for delineation
        total_warnings = int(df['is_warning'].sum()) if 'is_warning' in df.columns else 0
        total_errors_strict = int(df['is_error_strict'].sum()) if 'is_error_strict' in df.columns else len(error_df)
        
        # Analyze temporal patterns
        hourly_counts = error_df.set_index('timestamp').resample('H')['has_error'].count()
        peak_hour = hourly_counts.idxmax() if not hourly_counts.empty else None
        
        # Transaction analysis
        transaction_errors = error_df[error_df['transaction_id'].notna()]
        transaction_counts = transaction_errors['transaction_id'].value_counts().head(10)
        
        patterns = []
        
        # Identify cascading failures (same transaction ID with multiple errors)
        if not transaction_counts.empty:
            for txn_id, count in transaction_counts.items():
                if count > 1:
                    txn_errors = transaction_errors[transaction_errors['transaction_id'] == txn_id]
                    patterns.append({
                        'type': 'cascading_failure',
                        'transaction_id': txn_id,
                        'error_count': count,
                        'time_span': f"{txn_errors['timestamp'].min()} to {txn_errors['timestamp'].max()}",
                        'categories': list(set([cat for cats in txn_errors['error_categories'] for cat in cats]))
                    })
        
        # Identify error bursts (>5 errors in 1 minute)
        df_with_minute = error_df.copy()
        df_with_minute['minute_bin'] = df_with_minute['timestamp'].dt.floor('1T')
        minute_counts = df_with_minute.groupby('minute_bin')['has_error'].count()
        
        for minute, count in minute_counts[minute_counts > 5].items():
            patterns.append({
                'type': 'error_burst',
                'time': minute,
                'error_count': count,
                'description': f"{count} errors in 1 minute starting at {minute.strftime('%H:%M:%S')}"
            })
        
        return {
            'total_errors': len(error_df),
            'total_log_entries': len(df),
            'error_rate': len(error_df) / len(df) if len(df) > 0 else 0,
            'error_categories': dict(category_counts),
            'error_levels': level_counts,
            'top_error_files': file_counts,
            'peak_hour': peak_hour.strftime('%H:%M') if peak_hour else None,
            'unique_transactions_with_errors': transaction_errors['transaction_id'].nunique() if not transaction_errors.empty else 0,
            'patterns': patterns,
            'total_warnings': total_warnings,
            'total_errors_strict': total_errors_strict
        }
    
    def generate_timeline(self, df: pd.DataFrame, interval_minutes: int = 15) -> pd.DataFrame:
        """
        Generate a timeline of events for visualization.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            interval_minutes (int): Timeline interval in minutes
            
        Returns:
            pd.DataFrame: Timeline data
        """
        if df.empty:
            return pd.DataFrame()
        
        # Create time bins
        df['time_bin'] = df['timestamp'].dt.floor(f'{interval_minutes}T')
        
        timeline = df.groupby('time_bin').agg({
            'has_error': ['count', 'sum'],
            'log_level': lambda x: x.value_counts().to_dict(),
            'error_categories': lambda x: [cat for sublist in x for cat in sublist if sublist],
        }).reset_index()
        
        # Flatten column names
        timeline.columns = ['time_bin', 'total_logs', 'total_errors', 'level_distribution', 'error_categories']
        
        # Calculate error categories distribution
        timeline['category_counts'] = timeline['error_categories'].apply(lambda x: dict(Counter(x)) if x else {})
        
        return timeline
    
    def create_summary_stats(self, df: pd.DataFrame, analysis: Dict) -> Dict:
        """
        Create comprehensive summary statistics.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            analysis (dict): Analysis results from analyze_error_patterns
            
        Returns:
            dict: Summary statistics
        """
        if df.empty:
            return {
                'timeframe': f"{self.start_time} - {self.end_time}",
                'total_logs': 0,
                'total_errors': 0,
                'error_rate': 0,
                'summary': "No data found in the specified timeframe",
                'time_filter_enabled': self.time_filter_enabled,
                'total_warnings': 0,
                'total_errors_strict': 0,
                'total_errors_inclusive': 0
            }
        
        error_df = df[df['has_error'] == True]
        
        # Time-based stats
        first_log = df['timestamp'].min()
        last_log = df['timestamp'].max()
        duration = last_log - first_log
        
        # Top error categories
        top_categories = []
        if analysis['error_categories']:
            for cat, count in sorted(analysis['error_categories'].items(), key=lambda x: x[1], reverse=True)[:5]:
                top_categories.append(f"{cat}: {count}")
        
        # Critical periods
        peak_periods = self.identify_peak_periods(df)
        
        analysis_timeframe = (
            f"{self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"
            if self.time_filter_enabled else "All data (no time filter)"
        )
        
        summary = {
            'analysis_timeframe': analysis_timeframe,
            'log_coverage': f"{first_log.strftime('%Y-%m-%d %H:%M')} - {last_log.strftime('%H:%M')}" if first_log and last_log else "N/A",
            'total_log_entries': len(df),
            'total_errors': analysis['total_errors'],
            'error_rate_percent': round(analysis['error_rate'] * 100, 2),
            'unique_files_analyzed': df['file_path'].nunique(),
            'unique_transactions_with_errors': analysis['unique_transactions_with_errors'],
            'top_error_categories': top_categories,
            'peak_periods_count': len(peak_periods),
            'cascading_failures': len([p for p in analysis['patterns'] if p['type'] == 'cascading_failure']),
            'error_bursts': len([p for p in analysis['patterns'] if p['type'] == 'error_burst']),
            'peak_error_hour': analysis['peak_hour'],
            'time_filter_enabled': self.time_filter_enabled,
            'total_warnings': analysis.get('total_warnings', 0),
            'total_errors_strict': analysis.get('total_errors_strict', analysis.get('total_errors', 0)),
            'total_errors_inclusive': analysis.get('total_errors', 0)
        }
        
        return summary


def main():
    """Test function for the analyzer."""
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data for testing
    import datetime as dt
    
    sample_data = []
    base_time = dt.datetime(2023, 10, 1, 10, 0, 0)  # Yesterday 10 AM
    
    for i in range(100):
        sample_data.append({
            'timestamp': base_time + dt.timedelta(minutes=i*2),
            'log_level': 'ERROR' if i % 10 == 0 else 'INFO',
            'has_error': i % 10 == 0,
            'error_categories': ['credit_card_errors'] if i % 10 == 0 else [],
            'file_path': f'/path/to/log{i%3}.log',
            'transaction_id': f'TXN{i}' if i % 5 == 0 else None
        })
    
    df = pd.DataFrame(sample_data)
    
    analyzer = DataAnalyzer(target_date=dt.datetime(2023, 10, 1))
    filtered_df = analyzer.filter_by_timeframe(df)
    
    if not filtered_df.empty:
        analysis = analyzer.analyze_error_patterns(filtered_df)
        summary = analyzer.create_summary_stats(filtered_df, analysis)
        
        print(f"Analysis completed:")
        print(f"Total errors: {analysis['total_errors']}")
        print(f"Error rate: {analysis['error_rate']:.2%}")
        print(f"Peak periods: {len(analyzer.identify_peak_periods(filtered_df))}")


if __name__ == "__main__":
    main()