#!/usr/bin/env python3
"""
Report Generator Module
Creates comprehensive reports, CSV exports, and visualizations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Handles generation of reports, exports, and visualizations."""
    
    def __init__(self, output_dir: str):
        """
        Initialize report generator with output directory.
        
        Args:
            output_dir (str): Directory to save generated reports
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def export_detailed_csv(self, df: pd.DataFrame, filename: str = None) -> str:
        """
        Export detailed log data to CSV.
        
        Args:
            df (pd.DataFrame): DataFrame with log data
            filename (str): Custom filename (optional)
            
        Returns:
            str: Path to saved CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detailed_log_analysis_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Prepare DataFrame for export
        export_df = df.copy()
        
        # Convert lists to strings for CSV compatibility
        if 'error_categories' in export_df.columns:
            export_df['error_categories'] = export_df['error_categories'].apply(
                lambda x: ', '.join(x) if isinstance(x, list) and x else ''
            )
        
        # Format timestamp
        if 'timestamp' in export_df.columns:
            export_df['timestamp'] = export_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add derived columns
        export_df['has_any_error'] = export_df['has_error']
        export_df['file_name'] = export_df['file_path'].apply(lambda x: os.path.basename(x) if x else '')
        
        # Reorder columns for better readability
        column_order = ['timestamp', 'log_level', 'has_any_error', 'is_error_strict', 'is_warning', 'error_categories', 
                       'transaction_id', 'message', 'file_name', 'file_path', 'line_number']
        
        # Only include columns that exist
        available_columns = [col for col in column_order if col in export_df.columns]
        remaining_columns = [col for col in export_df.columns if col not in available_columns]
        final_columns = available_columns + remaining_columns
        
        export_df = export_df[final_columns]
        
        # Save to CSV
        export_df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"Detailed CSV exported to: {filepath}")
        
        return filepath
    
    def create_executive_summary(self, summary_stats: Dict, analysis: Dict, 
                               peak_periods: List[Dict], filename: str = None) -> str:
        """
        Create executive summary text report.
        
        Args:
            summary_stats (dict): Summary statistics
            analysis (dict): Detailed analysis results
            peak_periods (list): Peak period information
            filename (str): Custom filename (optional)
            
        Returns:
            str: Path to saved summary file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"executive_summary_{timestamp}.txt"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Create the summary content
        summary_content = f"""
# ROOT CAUSE ANALYSIS - EXECUTIVE SUMMARY
Generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}

## ANALYSIS OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analysis Period: {summary_stats.get('analysis_timeframe', 'N/A')}
Log Data Coverage: {summary_stats.get('log_coverage', 'N/A')}
Files Analyzed: {summary_stats.get('unique_files_analyzed', 0)} log files

## KEY FINDINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Total Log Entries Analyzed: {summary_stats.get('total_log_entries', 0):,}
✗ Total Errors Identified: {summary_stats.get('total_errors', 0):,}
📊 Error Rate: {summary_stats.get('error_rate_percent', 0)}%
🔥 Peak Error Period: {summary_stats.get('peak_error_hour', 'Not identified')}
⚠️  Cascading Failures: {summary_stats.get('cascading_failures', 0)}
💥 Error Bursts Detected: {summary_stats.get('error_bursts', 0)}

— Breakdown —
Errors (strict): {summary_stats.get('total_errors_strict', 'N/A')}
Warnings: {summary_stats.get('total_warnings', 'N/A')}
Errors incl. warnings: {summary_stats.get('total_errors_inclusive', summary_stats.get('total_errors', 0))}

## TOP ERROR CATEGORIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Add top error categories
        if summary_stats.get('top_error_categories'):
            for i, category in enumerate(summary_stats['top_error_categories'], 1):
                summary_content += f"{i}. {category}\n"
        else:
            summary_content += "No error categories identified.\n"
        
        # Add peak periods section
        summary_content += f"""
## CRITICAL TIME PERIODS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if peak_periods:
            for i, period in enumerate(peak_periods[:5], 1):
                summary_content += f"""
{i}. TIME: {period['time_period']}
   Errors: {period['error_count']} errors
   Files: {period['affected_files']} affected files
   Transactions: {period.get('unique_transactions', 0)} unique transactions
   Top Categories: {', '.join([f"{k}({v})" for k,v in period.get('top_error_categories', {}).items()][:3])}
"""
        else:
            summary_content += "No significant peak periods identified.\n"
        
        # Add patterns section
        summary_content += f"""
## ERROR PATTERNS DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        patterns = analysis.get('patterns', [])
        if patterns:
            cascading = [p for p in patterns if p['type'] == 'cascading_failure']
            bursts = [p for p in patterns if p['type'] == 'error_burst']
            
            if cascading:
                summary_content += f"\n🔗 CASCADING FAILURES ({len(cascading)} detected):\n"
                for pattern in cascading[:5]:
                    summary_content += f"   • Transaction {pattern['transaction_id']}: {pattern['error_count']} errors\n"
                    summary_content += f"     Time: {pattern['time_span']}\n"
                    summary_content += f"     Categories: {', '.join(pattern['categories'])}\n\n"
            
            if bursts:
                summary_content += f"💥 ERROR BURSTS ({len(bursts)} detected):\n"
                for pattern in bursts[:5]:
                    summary_content += f"   • {pattern['description']}\n"
                    
        else:
            summary_content += "No specific error patterns detected.\n"
        
        # Add transaction analysis
        summary_content += f"""
## TRANSACTION IMPACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Unique Transactions with Errors: {summary_stats.get('unique_transactions_with_errors', 0)}
"""
        
        # Add file-based analysis
        if analysis.get('top_error_files'):
            summary_content += f"""
## TOP ERROR FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            for file_path, count in list(analysis['top_error_files'].items())[:10]:
                file_name = os.path.basename(file_path)
                summary_content += f"{count:3d} errors - {file_name}\n"
        
        # Add recommendations
        summary_content += f"""
## RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # Generate recommendations based on findings
        recommendations = []
        
        if analysis.get('error_categories', {}).get('credit_card_errors', 0) > 0:
            recommendations.append("1. PAYMENT PROCESSING: Review payment gateway configuration and timeout settings")
        
        if analysis.get('error_categories', {}).get('database_errors', 0) > 0:
            recommendations.append("2. DATABASE: Investigate database connection pool and timeout configurations")
        
        if analysis.get('error_categories', {}).get('server_errors', 0) > 0:
            recommendations.append("3. SERVER INFRASTRUCTURE: Review server capacity and load balancing")
        
        if summary_stats.get('error_bursts', 0) > 0:
            recommendations.append("4. MONITORING: Implement real-time alerting for error burst detection")
        
        if summary_stats.get('cascading_failures', 0) > 0:
            recommendations.append("5. RESILIENCE: Review circuit breaker patterns and failure isolation")
        
        if not recommendations:
            recommendations.append("1. Continue monitoring for similar patterns in future incidents")
        
        for rec in recommendations:
            summary_content += f"{rec}\n"
        
        summary_content += f"""
## NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Review detailed CSV data for specific error messages and affected transactions
2. Correlate findings with deployment and infrastructure changes during the incident window
3. Implement recommended monitoring and alerting improvements
4. Schedule follow-up review to track improvement metrics

Report generated by Log Analyzer v1.0
For detailed data, see accompanying CSV file.
"""
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        logger.info(f"Executive summary saved to: {filepath}")
        return filepath
    
    def create_visualizations(self, df: pd.DataFrame, analysis: Dict, 
                            timeline_df: pd.DataFrame) -> List[str]:
        """
        Create visualizations and save as PNG files.
        
        Args:
            df (pd.DataFrame): Main log DataFrame
            analysis (dict): Analysis results
            timeline_df (pd.DataFrame): Timeline data
            
        Returns:
            list: List of paths to saved visualization files
        """
        saved_files = []
        
        if df.empty:
            logger.warning("No data available for visualizations")
            return saved_files
        
        # 1. Error Categories Bar Chart
        if analysis.get('error_categories'):
            fig, ax = plt.subplots(figsize=(12, 6))
            categories = list(analysis['error_categories'].keys())
            counts = list(analysis['error_categories'].values())
            
            bars = ax.bar(categories, counts, color='red', alpha=0.7)
            ax.set_title('Error Categories Distribution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Error Category')
            ax.set_ylabel('Number of Errors')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            chart_path = os.path.join(self.output_dir, 'error_categories_chart.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            saved_files.append(chart_path)
            logger.info(f"Error categories chart saved to: {chart_path}")
        
        # 2. Timeline Chart
        if not timeline_df.empty:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # Total logs over time
            ax1.plot(timeline_df['time_bin'], timeline_df['total_logs'], 
                    marker='o', linestyle='-', linewidth=2, label='Total Logs')
            ax1.set_title('Log Volume Timeline', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Number of Log Entries')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Errors over time
            ax2.plot(timeline_df['time_bin'], timeline_df['total_errors'], 
                    marker='o', linestyle='-', linewidth=2, color='red', label='Errors')
            ax2.set_title('Error Timeline', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Time')
            ax2.set_ylabel('Number of Errors')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Format x-axis
            for ax in [ax1, ax2]:
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            timeline_path = os.path.join(self.output_dir, 'timeline_chart.png')
            plt.savefig(timeline_path, dpi=300, bbox_inches='tight')
            plt.close()
            saved_files.append(timeline_path)
            logger.info(f"Timeline chart saved to: {timeline_path}")
        
        # 3. Log Levels Pie Chart
        if analysis.get('error_levels'):
            fig, ax = plt.subplots(figsize=(8, 8))
            levels = list(analysis['error_levels'].keys())
            counts = list(analysis['error_levels'].values())
            
            colors = ['red', 'orange', 'yellow', 'green', 'blue']
            wedges, texts, autotexts = ax.pie(counts, labels=levels, autopct='%1.1f%%', 
                                            colors=colors[:len(levels)], startangle=90)
            
            ax.set_title('Error Distribution by Log Level', fontsize=14, fontweight='bold')
            
            pie_path = os.path.join(self.output_dir, 'log_levels_pie_chart.png')
            plt.savefig(pie_path, dpi=300, bbox_inches='tight')
            plt.close()
            saved_files.append(pie_path)
            logger.info(f"Log levels pie chart saved to: {pie_path}")
        
        return saved_files
    
    def create_interactive_dashboard(self, df: pd.DataFrame, analysis: Dict, 
                                   timeline_df: pd.DataFrame) -> str:
        """
        Create an interactive HTML dashboard using Plotly.
        
        Args:
            df (pd.DataFrame): Main log DataFrame
            analysis (dict): Analysis results
            timeline_df (pd.DataFrame): Timeline data
            
        Returns:
            str: Path to saved HTML file
        """
        if df.empty:
            logger.warning("No data available for dashboard")
            return ""
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=('Error Categories', 'Timeline - Log Volume', 
                           'Timeline - Errors', 'Log Levels', 
                           'Files with Most Errors', 'Error Rate Over Time'),
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # 1. Error Categories Bar Chart
        if analysis.get('error_categories'):
            categories = list(analysis['error_categories'].keys())
            counts = list(analysis['error_categories'].values())
            
            fig.add_trace(
                go.Bar(x=categories, y=counts, name="Error Categories",
                      marker_color='red', opacity=0.7),
                row=1, col=1
            )
        
        # 2. & 3. Timeline Charts
        if not timeline_df.empty:
            fig.add_trace(
                go.Scatter(x=timeline_df['time_bin'], y=timeline_df['total_logs'],
                          mode='lines+markers', name='Total Logs'),
                row=1, col=2
            )
            
            fig.add_trace(
                go.Scatter(x=timeline_df['time_bin'], y=timeline_df['total_errors'],
                          mode='lines+markers', name='Errors', line=dict(color='red')),
                row=2, col=1
            )
        
        # 4. Log Levels Pie Chart
        if analysis.get('error_levels'):
            fig.add_trace(
                go.Pie(labels=list(analysis['error_levels'].keys()),
                      values=list(analysis['error_levels'].values()),
                      name="Log Levels"),
                row=2, col=2
            )
        
        # 5. Top Error Files
        if analysis.get('top_error_files'):
            files = [os.path.basename(f) for f in list(analysis['top_error_files'].keys())[:10]]
            counts = list(analysis['top_error_files'].values())[:10]
            
            fig.add_trace(
                go.Bar(x=files, y=counts, name="Error Files",
                      marker_color='orange', opacity=0.7),
                row=3, col=1
            )
        
        # 6. Error Rate Over Time
        if not timeline_df.empty:
            error_rate = (timeline_df['total_errors'] / timeline_df['total_logs']) * 100
            
            fig.add_trace(
                go.Scatter(x=timeline_df['time_bin'], y=error_rate,
                          mode='lines+markers', name='Error Rate (%)',
                          line=dict(color='darkred')),
                row=3, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=1200,
            title_text=f"Log Analysis Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            title_font_size=20,
            showlegend=False
        )
        
        # Update x-axes for timeline charts
        for row, col in [(1, 2), (2, 1), (3, 2)]:
            fig.update_xaxes(tickangle=45, row=row, col=col)
        
        # Save interactive HTML
        dashboard_path = os.path.join(self.output_dir, 'interactive_dashboard.html')
        fig.write_html(dashboard_path)
        
        logger.info(f"Interactive dashboard saved to: {dashboard_path}")
        return dashboard_path


def main():
    """Test function for the report generator."""
    logging.basicConfig(level=logging.INFO)
    
    # Create sample data for testing
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Generate test data
    base_time = datetime(2023, 10, 1, 10, 0, 0)
    sample_data = []
    
    for i in range(50):
        sample_data.append({
            'timestamp': base_time + timedelta(minutes=i*2),
            'log_level': 'ERROR' if i % 5 == 0 else 'INFO',
            'has_error': i % 5 == 0,
            'error_categories': ['credit_card_errors'] if i % 5 == 0 else [],
            'file_path': f'/test/log{i%3}.log',
            'line_number': i + 1,
            'message': f'Test message {i}',
            'transaction_id': f'TXN{i}' if i % 10 == 0 else None
        })
    
    df = pd.DataFrame(sample_data)
    
    # Test report generation
    output_dir = '/tmp/log_analyzer_test'
    generator = ReportGenerator(output_dir)
    
    # Test CSV export
    csv_path = generator.export_detailed_csv(df)
    print(f"Test CSV created at: {csv_path}")


if __name__ == "__main__":
    main()