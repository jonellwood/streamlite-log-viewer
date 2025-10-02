#!/usr/bin/env python3
"""
Log Parser Module
Flexible parser for various log formats with timestamp detection and content extraction.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import concurrent.futures
import pandas as pd

logger = logging.getLogger(__name__)

class LogParser:
    """Handles parsing of log files with flexible timestamp and content extraction."""
    
    def __init__(self, treat_warnings_as_errors: bool = False):
        """Initialize log parser with timestamp patterns and error categories.
        
        Args:
            treat_warnings_as_errors (bool): When True, treat warnings as errors for has_error flag
        """
        self.treat_warnings_as_errors = treat_warnings_as_errors
        
        # Common timestamp patterns (compiled for performance)
        self.timestamp_patterns = [
            # ISO 8601: 2023-10-01T14:30:45.123Z or 2023-10-01 14:30:45
            (re.compile(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:?\d{2})?)', re.IGNORECASE), 
             '%Y-%m-%d %H:%M:%S'),
            
            # Common log formats: Oct 01 14:30:45
            (re.compile(r'([A-Za-z]{3} \d{1,2} \d{2}:\d{2}:\d{2})', re.IGNORECASE), 
             '%b %d %H:%M:%S'),
            
            # Apache/Nginx: [01/Oct/2023:14:30:45 +0000]
            (re.compile(r'\[(\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}(?: [+-]\d{4})?)\]', re.IGNORECASE), 
             '%d/%b/%Y:%H:%M:%S'),
            
            # Syslog format: 2023-10-01 14:30:45
            (re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', re.IGNORECASE), 
             '%Y-%m-%d %H:%M:%S'),
            
            # MM/dd/yyyy format: 10/01/2023 14:30:45
            (re.compile(r'(\d{1,2}/\d{1,2}/\d{4} \d{2}:\d{2}:\d{2})', re.IGNORECASE), 
             '%m/%d/%Y %H:%M:%S'),
            
            # Alternative format with milliseconds: 2023-10-01 14:30:45.123
            (re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})', re.IGNORECASE), 
             '%Y-%m-%d %H:%M:%S.%f'),
        ]
        
        # Log level patterns
        self.log_level_pattern = re.compile(
            r'\b(TRACE|DEBUG|INFO|INFORMATION|WARN|WARNING|ERROR|FATAL|CRITICAL|SEVERE)\b', 
            re.IGNORECASE
        )
        
        # Error classification patterns
        self.error_patterns = {
            'credit_card_errors': [
                re.compile(r'payment\s+gateway', re.IGNORECASE),
                re.compile(r'credit\s+card', re.IGNORECASE),
                re.compile(r'card\s+declined', re.IGNORECASE),
                re.compile(r'payment\s+failed', re.IGNORECASE),
                re.compile(r'transaction\s+timeout', re.IGNORECASE),
                re.compile(r'authorization\s+failed', re.IGNORECASE),
                re.compile(r'invalid\s+card', re.IGNORECASE),
                re.compile(r'payment\s+processor', re.IGNORECASE),
                re.compile(r'merchant\s+account', re.IGNORECASE),
            ],
            'database_errors': [
                re.compile(r'connection\s+refused', re.IGNORECASE),
                re.compile(r'cannot\s+connect', re.IGNORECASE),
                re.compile(r'database\s+error', re.IGNORECASE),
                re.compile(r'sql\s+error', re.IGNORECASE),
                re.compile(r'timeout.*database', re.IGNORECASE),
                re.compile(r'deadlock', re.IGNORECASE),
                re.compile(r'connection\s+lost', re.IGNORECASE),
                re.compile(r'mysql.*error', re.IGNORECASE),
                re.compile(r'postgresql.*error', re.IGNORECASE),
                re.compile(r'oracle.*error', re.IGNORECASE),
            ],
            'server_errors': [
                re.compile(r'http.*50\d', re.IGNORECASE),
                re.compile(r'status.*50\d', re.IGNORECASE),
                re.compile(r'internal\s+server\s+error', re.IGNORECASE),
                re.compile(r'service\s+unavailable', re.IGNORECASE),
                re.compile(r'gateway\s+timeout', re.IGNORECASE),
                re.compile(r'bad\s+gateway', re.IGNORECASE),
                re.compile(r'server\s+error', re.IGNORECASE),
            ],
            'timeout_errors': [
                re.compile(r'timeout', re.IGNORECASE),
                re.compile(r'timed\s+out', re.IGNORECASE),
                re.compile(r'connection\s+timeout', re.IGNORECASE),
                re.compile(r'read\s+timeout', re.IGNORECASE),
                re.compile(r'request\s+timeout', re.IGNORECASE),
            ],
            'authentication_errors': [
                re.compile(r'authentication\s+failed', re.IGNORECASE),
                re.compile(r'unauthorized', re.IGNORECASE),
                re.compile(r'access\s+denied', re.IGNORECASE),
                re.compile(r'forbidden', re.IGNORECASE),
                re.compile(r'invalid\s+credentials', re.IGNORECASE),
                re.compile(r'login\s+failed', re.IGNORECASE),
            ],
            'exception_errors': [
                re.compile(r'exception', re.IGNORECASE),
                re.compile(r'stack\s+trace', re.IGNORECASE),
                re.compile(r'null\s+pointer', re.IGNORECASE),
                re.compile(r'out\s+of\s+memory', re.IGNORECASE),
                re.compile(r'segmentation\s+fault', re.IGNORECASE),
            ]
        }
        
        # Transaction ID patterns (common formats)
        self.transaction_patterns = [
            re.compile(r'transaction[_\s]+id[:\s]+([a-zA-Z0-9\-_]+)', re.IGNORECASE),
            re.compile(r'txn[_\s]+id[:\s]+([a-zA-Z0-9\-_]+)', re.IGNORECASE),
            re.compile(r'order[_\s]+id[:\s]+([a-zA-Z0-9\-_]+)', re.IGNORECASE),
            re.compile(r'ref[_\s]+id[:\s]+([a-zA-Z0-9\-_]+)', re.IGNORECASE),
        ]
        
        # Warning detection patterns (e.g., PHP warnings/notices)
        self.warning_patterns = [
            re.compile(r'\bphp\s+warning\b', re.IGNORECASE),
            re.compile(r'\bphp\s+notice\b', re.IGNORECASE),
            re.compile(r'\bdeprecated\b', re.IGNORECASE),
            re.compile(r'\bE_WARNING\b'),
            re.compile(r'\bE_NOTICE\b'),
        ]
    
    def detect_timestamp(self, line: str) -> Tuple[Optional[datetime], str]:
        """
        Extract timestamp from a log line.
        
        Args:
            line (str): Log line to parse
            
        Returns:
            tuple: (datetime object or None, remaining line after timestamp removal)
        """
        for pattern, date_format in self.timestamp_patterns:
            match = pattern.search(line)
            if match:
                timestamp_str = match.group(1)
                try:
                    # Handle special cases
                    if 'T' in timestamp_str:
                        timestamp_str = timestamp_str.replace('T', ' ').rstrip('Z')
                    
                    # Try parsing with the matched format
                    if date_format == '%b %d %H:%M:%S':
                        # Add current year for syslog format
                        current_year = datetime.now().year
                        timestamp_str = f"{current_year} {timestamp_str}"
                        date_format = '%Y %b %d %H:%M:%S'
                    
                    timestamp = datetime.strptime(timestamp_str[:19], date_format[:19])
                    
                    # Remove timestamp from line
                    remaining_line = line[match.end():].strip()
                    
                    return timestamp, remaining_line
                    
                except ValueError as e:
                    logger.debug(f"Failed to parse timestamp '{timestamp_str}' with format '{date_format}': {e}")
                    continue
        
        return None, line
    
    def extract_log_level(self, line: str) -> Tuple[Optional[str], str]:
        """
        Extract log level from a log line.
        
        Args:
            line (str): Log line to parse
            
        Returns:
            tuple: (log level string or None, remaining line after level removal)
        """
        match = self.log_level_pattern.search(line)
        if match:
            level = match.group(1).upper()
            # Remove the matched level from line
            remaining_line = line[:match.start()] + line[match.end():]
            remaining_line = remaining_line.strip()
            return level, remaining_line
        
        return None, line
    
    def classify_error(self, line: str) -> List[str]:
        """
        Classify errors in a log line based on predefined patterns.
        
        Args:
            line (str): Log line to classify
            
        Returns:
            list: List of error categories that match the line
        """
        categories = []
        
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern.search(line):
                    categories.append(category)
                    break  # Only add category once
        
        return categories
    
    def extract_transaction_id(self, line: str) -> Optional[str]:
        """
        Extract transaction ID from a log line.
        
        Args:
            line (str): Log line to parse
            
        Returns:
            str or None: Transaction ID if found
        """
        for pattern in self.transaction_patterns:
            match = pattern.search(line)
            if match:
                return match.group(1)
        
        return None
    
    def parse_line(self, line: str, file_path: str = "", line_number: int = 0) -> Dict:
        """
        Parse a single log line and extract all relevant information.
        
        Args:
            line (str): Log line to parse
            file_path (str): Path to the source file
            line_number (int): Line number in the source file
            
        Returns:
            dict: Parsed line information
        """
        original_line = line.strip()
        
        if not original_line:
            return None
        
        # Extract timestamp
        timestamp, line_after_ts = self.detect_timestamp(original_line)
        
        # Extract log level
        log_level, line_after_level = self.extract_log_level(line_after_ts)
        
        # Classify errors
        error_categories = self.classify_error(original_line)
        
        # Determine warnings
        is_warning_level = (log_level in ['WARN', 'WARNING']) if log_level else False
        is_warning_phrase = any(p.search(original_line) for p in self.warning_patterns)
        is_warning = bool(is_warning_level or is_warning_phrase)
        
        # Strict errors (do not include warnings)
        is_error_strict = bool(len(error_categories) > 0 or (log_level in ['ERROR', 'FATAL', 'CRITICAL']) if log_level else len(error_categories) > 0)
        
        # Final has_error depends on configuration
        has_error = bool(is_error_strict or (is_warning and self.treat_warnings_as_errors))
        
        # Extract transaction ID
        transaction_id = self.extract_transaction_id(original_line)
        
        return {
            'timestamp': timestamp,
            'log_level': log_level,
            'message': line_after_level,
            'original_line': original_line,
            'error_categories': error_categories,
            'transaction_id': transaction_id,
            'file_path': file_path,
            'line_number': line_number,
            'is_warning': is_warning,
            'is_error_strict': is_error_strict,
            'has_error': has_error
        }
    
    def parse_file(self, file_path: str, max_lines: int = None) -> List[Dict]:
        """
        Parse an entire log file.
        
        Args:
            file_path (str): Path to the log file
            max_lines (int): Maximum number of lines to parse (None for all)
            
        Returns:
            list: List of parsed line dictionaries
        """
        parsed_lines = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_number, line in enumerate(file, 1):
                    if max_lines and line_number > max_lines:
                        break
                    
                    parsed_line = self.parse_line(line, file_path, line_number)
                    if parsed_line:
                        parsed_lines.append(parsed_line)
                    
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
        
        logger.info(f"Parsed {len(parsed_lines)} lines from {file_path}")
        return parsed_lines
    
    def parse_files_parallel(self, file_paths: List[str], max_workers: int = 4, max_lines_per_file: int = None) -> List[Dict]:
        """
        Parse multiple files in parallel.
        
        Args:
            file_paths (list): List of file paths to parse
            max_workers (int): Maximum number of worker threads
            max_lines_per_file (int): Optional cap on number of lines to parse from each file
            
        Returns:
            list: Combined list of all parsed lines
        """
        all_parsed_lines = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all file parsing jobs
            future_to_file = {
                executor.submit(self.parse_file, file_path, max_lines=max_lines_per_file): file_path 
                for file_path in file_paths
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    parsed_lines = future.result()
                    all_parsed_lines.extend(parsed_lines)
                except Exception as e:
                    logger.error(f"Error parsing file {file_path}: {e}")
        
        logger.info(f"Parsed total of {len(all_parsed_lines)} lines from {len(file_paths)} files")
        return all_parsed_lines
    
    def to_dataframe(self, parsed_lines: List[Dict]) -> pd.DataFrame:
        """
        Convert parsed lines to a pandas DataFrame.
        
        Args:
            parsed_lines (list): List of parsed line dictionaries
            
        Returns:
            pd.DataFrame: DataFrame with parsed log data
        """
        if not parsed_lines:
            return pd.DataFrame()
        
        df = pd.DataFrame(parsed_lines)
        
        # Convert timestamp to datetime if not None
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Expand error_categories into separate boolean columns
        all_categories = set()
        for categories in df['error_categories']:
            all_categories.update(categories)
        
        for category in all_categories:
            df[f'is_{category}'] = df['error_categories'].apply(lambda x: category in x)
        
        return df


def main():
    """Test function for the parser."""
    logging.basicConfig(level=logging.INFO)
    
    # Test parser with sample log lines
    parser = LogParser()
    
    test_lines = [
        "2023-10-01 14:30:45 ERROR Payment gateway timeout for transaction ID: TXN123456",
        "[01/Oct/2023:14:35:22 +0000] WARN Cannot connect to database",
        "Oct 01 14:40:15 CRITICAL HTTP/1.1 500 Internal Server Error",
        "2023-10-01T15:15:30.123Z INFO User login successful",
    ]
    
    print("Testing log parser with sample lines:")
    for i, line in enumerate(test_lines, 1):
        parsed = parser.parse_line(line, "test.log", i)
        print(f"Line {i}: {parsed['timestamp']} [{parsed['log_level']}] Categories: {parsed['error_categories']}")


if __name__ == "__main__":
    main()