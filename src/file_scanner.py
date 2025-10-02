#!/usr/bin/env python3
"""
Log File Scanner Module
Recursively scans directories for .log and .txt files, collecting metadata.
"""

import os
import glob
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class LogFileScanner:
    """Handles discovery and metadata collection of log files."""
    
    def __init__(self, root_directory):
        """
        Initialize scanner with root directory path.
        
        Args:
            root_directory (str): Path to root directory containing log files
        """
        self.root_directory = Path(root_directory)
        self.supported_extensions = ['.log', '.txt']
        
    def scan_directory(self):
        """
        Recursively scan directory for log and text files.
        
        Returns:
            list: List of dictionaries containing file metadata
        """
        log_files = []
        
        if not self.root_directory.exists():
            logger.warning(f"Root directory {self.root_directory} does not exist")
            return log_files
            
        logger.info(f"Scanning directory: {self.root_directory}")
        
        # Use os.walk for recursive directory traversal
        for root, dirs, files in os.walk(self.root_directory):
            for file in files:
                file_path = Path(root) / file
                
                # Check if file has supported extension
                if file_path.suffix.lower() in self.supported_extensions:
                    try:
                        stat_info = file_path.stat()
                        file_metadata = {
                            'file_path': str(file_path),
                            'file_name': file_path.name,
                            'file_size': stat_info.st_size,
                            'modified_time': datetime.fromtimestamp(stat_info.st_mtime),
                            'created_time': datetime.fromtimestamp(stat_info.st_ctime),
                            'relative_path': str(file_path.relative_to(self.root_directory)),
                            'extension': file_path.suffix.lower(),
                            'directory': str(file_path.parent)
                        }
                        log_files.append(file_metadata)
                        logger.debug(f"Found log file: {file_path}")
                        
                    except (OSError, IOError) as e:
                        logger.warning(f"Could not read metadata for {file_path}: {e}")
                        continue
        
        logger.info(f"Found {len(log_files)} log files")
        return log_files
    
    def filter_by_size(self, file_list, min_size=0, max_size=None):
        """
        Filter files by size range.
        
        Args:
            file_list (list): List of file metadata dictionaries
            min_size (int): Minimum file size in bytes
            max_size (int): Maximum file size in bytes (None for no limit)
            
        Returns:
            list: Filtered list of file metadata
        """
        filtered = []
        for file_info in file_list:
            size = file_info['file_size']
            if size >= min_size and (max_size is None or size <= max_size):
                filtered.append(file_info)
        
        logger.info(f"Size filter: {len(file_list)} -> {len(filtered)} files")
        return filtered
    
    def filter_by_modified_date(self, file_list, start_date=None, end_date=None):
        """
        Filter files by modification date range.
        
        Args:
            file_list (list): List of file metadata dictionaries
            start_date (datetime): Start date (inclusive)
            end_date (datetime): End date (inclusive)
            
        Returns:
            list: Filtered list of file metadata
        """
        if start_date is None and end_date is None:
            return file_list
            
        filtered = []
        for file_info in file_list:
            mod_time = file_info['modified_time']
            
            include_file = True
            if start_date and mod_time < start_date:
                include_file = False
            if end_date and mod_time > end_date:
                include_file = False
                
            if include_file:
                filtered.append(file_info)
        
        logger.info(f"Date filter: {len(file_list)} -> {len(filtered)} files")
        return filtered
    
    def get_file_summary(self, file_list):
        """
        Generate summary statistics for discovered files.
        
        Args:
            file_list (list): List of file metadata dictionaries
            
        Returns:
            dict: Summary statistics
        """
        if not file_list:
            return {'total_files': 0, 'total_size': 0, 'extensions': {}}
        
        total_size = sum(f['file_size'] for f in file_list)
        extensions = {}
        
        for file_info in file_list:
            ext = file_info['extension']
            extensions[ext] = extensions.get(ext, 0) + 1
        
        oldest_file = min(file_list, key=lambda x: x['modified_time'])
        newest_file = max(file_list, key=lambda x: x['modified_time'])
        
        return {
            'total_files': len(file_list),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'extensions': extensions,
            'oldest_file': {
                'path': oldest_file['file_path'],
                'modified': oldest_file['modified_time']
            },
            'newest_file': {
                'path': newest_file['file_path'],
                'modified': newest_file['modified_time']
            }
        }


def main():
    """Test function for the scanner."""
    logging.basicConfig(level=logging.INFO)
    
    # Test with logs directory
    scanner = LogFileScanner("/Users/jonathanellwood/log-analyzer/logs")
    files = scanner.scan_directory()
    
    if files:
        summary = scanner.get_file_summary(files)
        print(f"Scanner found {summary['total_files']} files ({summary['total_size_mb']} MB)")
        print(f"Extensions: {summary['extensions']}")
    else:
        print("No log files found. Make sure to place log files in the 'logs' directory.")


if __name__ == "__main__":
    main()