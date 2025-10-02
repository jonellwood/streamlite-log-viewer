#!/usr/bin/env python3
"""
Log Analyzer - Main Application
Root cause analysis tool for log files with focus on ticket selling and credit card processing failures.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from file_scanner import LogFileScanner
from log_parser import LogParser
from data_analyzer import DataAnalyzer
from report_generator import ReportGenerator

class LogAnalyzerApp:
    """Main application class that orchestrates the complete log analysis workflow."""
    
    def __init__(self, logs_dir: str = None, output_dir: str = None, target_date: datetime = None,
                 max_file_size_mb: int = 200, max_lines_per_file: int = None,
                 warnings_as_errors: bool = False, no_time_filter: bool = False):
        """
        Initialize the log analyzer application.
        
        Args:
            logs_dir (str): Directory containing log files
            output_dir (str): Directory to save results
            target_date (datetime): Date to analyze (defaults to yesterday)
            max_file_size_mb (int): Skip files larger than this size in MB (default: 200MB)
            max_lines_per_file (int): Optional cap on lines parsed from each file
            warnings_as_errors (bool): Count warnings as errors in totals
            no_time_filter (bool): Process all data without timeframe filtering
        """
        # Set up paths
        self.base_dir = Path(__file__).parent
        self.logs_dir = Path(logs_dir) if logs_dir else self.base_dir / 'logs'
        self.output_dir = Path(output_dir) if output_dir else self.base_dir / 'output'
        
        # Set target date (defaults to yesterday)
        self.target_date = target_date if target_date else datetime.now() - timedelta(days=1)
        
        # Limits for parsing
        self.max_file_size_mb = max_file_size_mb
        self.max_lines_per_file = max_lines_per_file
        self.warnings_as_errors = warnings_as_errors
        self.no_time_filter = no_time_filter
        
        # Initialize components
        self.scanner = LogFileScanner(str(self.logs_dir))
        self.parser = LogParser(treat_warnings_as_errors=self.warnings_as_errors)
        self.analyzer = DataAnalyzer(target_date=self.target_date, time_filter_enabled=not self.no_time_filter)
        self.report_generator = ReportGenerator(str(self.output_dir))
        
        # Set up logging
        self.setup_logging()
        
        logger = logging.getLogger(__name__)
        logger.info(f"Log Analyzer initialized")
        logger.info(f"Logs directory: {self.logs_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Analysis date: {self.target_date.strftime('%Y-%m-%d')}")
        logger.info(f"Max file size (MB): {self.max_file_size_mb}")
        logger.info(f"Max lines per file: {self.max_lines_per_file if self.max_lines_per_file else 'No limit'}")
        logger.info(f"Warnings as errors: {self.warnings_as_errors}")
        logger.info(f"Time filter enabled: {not self.no_time_filter}")
    
    def setup_logging(self):
        """Set up logging configuration."""
        # Create logs directory if it doesn't exist
        log_dir = self.output_dir / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_file = log_dir / f"log_analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(log_file)),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_analysis(self, max_workers: int = 4) -> dict:
        """
        Run the complete log analysis workflow.
        
        Args:
            max_workers (int): Number of worker threads for parallel processing
            
        Returns:
            dict: Analysis results and file paths
        """
        logger = logging.getLogger(__name__)
        
        try:
            logger.info("=" * 80)
            logger.info("Starting Log Analysis Workflow")
            logger.info("=" * 80)
            
            # Step 1: Scan for log files
            logger.info("Step 1: Scanning for log files...")
            log_files = self.scanner.scan_directory()
            
            if not log_files:
                logger.error("No log files found in the specified directory!")
                logger.error(f"Please ensure log files (.log, .txt) are placed in: {self.logs_dir}")
                return {'success': False, 'error': 'No log files found'}
            
            file_summary = self.scanner.get_file_summary(log_files)
            logger.info(f"Found {file_summary['total_files']} files ({file_summary['total_size_mb']} MB)")
            
            # Optional: Filter out very large files to avoid long parse times
            if self.max_file_size_mb and self.max_file_size_mb > 0:
                max_bytes = self.max_file_size_mb * 1024 * 1024
                before_count = len(log_files)
                log_files = self.scanner.filter_by_size(log_files, max_size=max_bytes)
                after_count = len(log_files)
                skipped = before_count - after_count
                if skipped > 0:
                    logger.warning(f"Skipping {skipped} file(s) larger than {self.max_file_size_mb} MB")
            
            # Step 2: Parse log files
            logger.info("Step 2: Parsing log files...")
            file_paths = [f['file_path'] for f in log_files]
            
            parsed_lines = self.parser.parse_files_parallel(
                file_paths, max_workers=max_workers, max_lines_per_file=self.max_lines_per_file
            )
            
            if not parsed_lines:
                logger.error("No parseable log entries found!")
                return {'success': False, 'error': 'No parseable log entries found'}
            
            logger.info(f"Parsed {len(parsed_lines):,} log entries")
            
            # Convert to DataFrame
            df = self.parser.to_dataframe(parsed_lines)
            logger.info(f"Created DataFrame with {len(df)} rows, {len(df.columns)} columns")
            
            # Step 3: Filter by timeframe (or skip if disabled)
            if self.no_time_filter:
                logger.info("Step 3: Skipping timeframe filter (processing ALL data)...")
                filtered_df = df
            else:
                logger.info("Step 3: Filtering by timeframe (9 AM - 2 PM)...")
                filtered_df = self.analyzer.filter_by_timeframe(df)
                
                if filtered_df.empty:
                    logger.warning("No log entries found in the target timeframe!")
                    logger.warning(f"Target: {self.analyzer.start_time} to {self.analyzer.end_time}")
                    return {'success': False, 'error': 'No data in target timeframe'}
                
                logger.info(f"Filtered to {len(filtered_df)} entries in target timeframe")
            
            # Step 4: Analyze data
            logger.info("Step 4: Analyzing error patterns...")
            analysis = self.analyzer.analyze_error_patterns(filtered_df)
            peak_periods = self.analyzer.identify_peak_periods(filtered_df)
            timeline_df = self.analyzer.generate_timeline(filtered_df)
            summary_stats = self.analyzer.create_summary_stats(filtered_df, analysis)
            
            logger.info(f"Analysis complete: {analysis['total_errors']} errors found ({analysis['error_rate']:.1%} rate)")
            if 'total_warnings' in analysis:
                logger.info(f" - Strict errors: {analysis.get('total_errors_strict', 0)}")
                logger.info(f" - Warnings: {analysis.get('total_warnings', 0)}")
                logger.info(f" - Inclusive errors (errors + warnings if enabled): {analysis.get('total_errors', 0)}")
            
            # Step 5: Generate reports
            logger.info("Step 5: Generating reports...")
            
            # CSV export
            csv_path = self.report_generator.export_detailed_csv(filtered_df)
            
            # Executive summary
            summary_path = self.report_generator.create_executive_summary(
                summary_stats, analysis, peak_periods
            )
            
            # Visualizations
            visualization_paths = self.report_generator.create_visualizations(
                filtered_df, analysis, timeline_df
            )
            
            # Interactive dashboard
            dashboard_path = self.report_generator.create_interactive_dashboard(
                filtered_df, analysis, timeline_df
            )
            
            # Step 6: Summary
            logger.info("=" * 80)
            logger.info("ANALYSIS COMPLETE!")
            logger.info("=" * 80)
            logger.info(f"📊 Log entries analyzed: {len(df):,}")
            logger.info(f"🎯 Entries in target window: {len(filtered_df):,}")
            logger.info(f"❌ Total errors found: {analysis['total_errors']:,}")
            logger.info(f"📈 Error rate: {analysis['error_rate']:.1%}")
            logger.info(f"⏰ Peak error period: {summary_stats.get('peak_error_hour', 'Not identified')}")
            logger.info(f"💥 Error bursts: {summary_stats.get('error_bursts', 0)}")
            logger.info(f"🔗 Cascading failures: {summary_stats.get('cascading_failures', 0)}")
            
            if analysis.get('error_categories'):
                logger.info("🏷️  Top error categories:")
                for category, count in list(analysis['error_categories'].items())[:5]:
                    logger.info(f"   • {category}: {count}")
            
            logger.info("=" * 80)
            logger.info("OUTPUT FILES:")
            logger.info("=" * 80)
            logger.info(f"📋 Executive Summary: {summary_path}")
            logger.info(f"📊 Detailed CSV: {csv_path}")
            logger.info(f"🌐 Interactive Dashboard: {dashboard_path}")
            
            for viz_path in visualization_paths:
                logger.info(f"📈 Chart: {viz_path}")
            
            return {
                'success': True,
                'summary_stats': summary_stats,
                'analysis': analysis,
                'peak_periods': peak_periods,
                'files': {
                    'csv': csv_path,
                    'summary': summary_path,
                    'dashboard': dashboard_path,
                    'visualizations': visualization_paths
                },
                'data': {
                    'total_files': len(log_files),
                    'total_entries': len(df),
                    'filtered_entries': len(filtered_df),
                    'total_errors': analysis['total_errors'],
                    'error_rate': analysis['error_rate']
                }
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Log Analyzer - Root Cause Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Analyze logs in ./logs/ directory for yesterday 9AM-2PM
  python main.py --date 2023-10-01  # Analyze specific date
  python main.py --logs /path/to/logs --output /path/to/results
        """
    )
    
    parser.add_argument(
        '--logs', 
        type=str, 
        help='Directory containing log files (default: ./logs/)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        help='Output directory for results (default: ./output/)'
    )
    
    parser.add_argument(
        '--date', 
        type=str, 
        help='Target date for analysis (YYYY-MM-DD format, default: yesterday)'
    )
    
    parser.add_argument(
        '--workers', 
        type=int, 
        default=4, 
        help='Number of worker threads for parallel processing (default: 4)'
    )

    parser.add_argument(
        '--max-file-size-mb',
        type=int,
        default=200,
        help='Skip files larger than this size in MB (default: 200)'
    )

    parser.add_argument(
        '--max-lines-per-file',
        type=int,
        default=None,
        help='Maximum number of lines to parse from each file (default: no limit)'
    )

    parser.add_argument(
        '--warnings-as-errors',
        action='store_true',
        help='Count warnings as errors (delineated in output)'
    )

    parser.add_argument(
        '--no-time-filter',
        action='store_true',
        help='Process all data without applying the 9:00-14:00 timeframe filter'
    )
    
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true', 
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Parse target date
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD format.")
            sys.exit(1)
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("=" * 80)
    print("🔍 LOG ANALYZER - ROOT CAUSE ANALYSIS TOOL")
    print("=" * 80)
    print(f"Target date: {(target_date or datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}")
    print(f"Time window: 09:00 - 14:00")
    print(f"Logs directory: {args.logs or './logs/'}")
    print(f"Output directory: {args.output or './output/'}")
    print("=" * 80)
    
    # Initialize and run analysis
    app = LogAnalyzerApp(
        logs_dir=args.logs,
        output_dir=args.output,
        target_date=target_date,
        max_file_size_mb=args.max_file_size_mb,
        max_lines_per_file=args.max_lines_per_file,
        warnings_as_errors=args.warnings_as_errors,
        no_time_filter=args.no_time_filter
    )
    
    results = app.run_analysis(max_workers=args.workers)
    
    if results['success']:
        print("\n🎉 Analysis completed successfully!")
        print(f"\n📋 Executive Summary: {results['files']['summary']}")
        print(f"📊 Detailed Data: {results['files']['csv']}")
        print(f"🌐 Interactive Dashboard: {results['files']['dashboard']}")
        print("\n✅ Ready for your 2:00 PM deadline!")
    else:
        print(f"\n❌ Analysis failed: {results['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()