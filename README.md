# 🔍 Log Analyzer - Root Cause Analysis Tool

A comprehensive log analysis application for identifying root causes of ticket selling and credit card processing failures. Built for rapid analysis with a focus on your **2:00 PM deadline**.

## 🚀 Quick Start (For Your Deadline)

### 1. Place Your Log Files
```bash
# Copy your log files (.log, .txt) into the logs directory:
cp /path/to/your/logs/*.log /Users/jonathanellwood/log-analyzer/logs/
cp /path/to/your/logs/*.txt /Users/jonathanellwood/log-analyzer/logs/
```

### 2. Run the Analysis
```bash
cd /Users/jonathanellwood/log-analyzer
python main.py
```

### 3. View Results
The analysis will create:
- **Executive Summary**: `output/executive_summary_YYYYMMDD_HHMMSS.txt`
- **Detailed CSV**: `output/detailed_log_analysis_YYYYMMDD_HHMMSS.csv` 
- **Interactive Dashboard**: `output/interactive_dashboard.html`
- **Charts**: `output/*.png`

### 4. Optional: Start Web Interface
```bash
python web_app.py --output ./output
# Then open http://localhost:5000 in your browser
```

## 📊 What It Analyzes

The tool focuses on **yesterday's logs between 9:00 AM - 2:00 PM** and identifies:

### 🎯 Target Error Categories
- **Credit Card Processing**: Payment gateway failures, timeouts, card declined
- **Database Issues**: Connection refused, timeouts, SQL errors
- **Server Errors**: 5xx HTTP status codes, internal server errors
- **Transaction Problems**: Timeout errors, authentication failures
- **System Exceptions**: Stack traces, memory errors, null pointer exceptions

### 📈 Analysis Features
- **Error Frequency Analysis**: Counts and trends over time
- **Peak Period Detection**: Identifies when errors spiked
- **Cascading Failure Detection**: Same transaction with multiple errors
- **Error Burst Identification**: >5 errors per minute
- **Transaction Impact Assessment**: Affected transaction IDs
- **File-based Error Distribution**: Which logs have the most errors

## 🏗️ Project Structure

```
log-analyzer/
├── main.py                    # Main application entry point
├── web_app.py                # Flask web interface
├── README.md                 # This file
├── src/                      # Source code modules
│   ├── file_scanner.py       # Recursive log file discovery
│   ├── log_parser.py         # Flexible timestamp and error parsing
│   ├── data_analyzer.py      # Data analysis and filtering
│   └── report_generator.py   # CSV, summary, and visualization generation
├── logs/                     # DROP YOUR LOG FILES HERE
├── output/                   # Generated reports and charts
└── output/logs/              # Analysis execution logs
```

## 🔧 Requirements

- **Python 3.9+** ✅ (You have 3.9.6)
- **Required packages**: pandas, matplotlib, seaborn, plotly, flask ✅ (Already installed)

## 📋 Command Line Options

### Main Analysis Tool
```bash
python main.py [OPTIONS]

Options:
  --logs PATH        Directory containing log files (default: ./logs/)
  --output PATH      Output directory for results (default: ./output/)
  --date YYYY-MM-DD  Target date for analysis (default: yesterday)
  --workers N        Number of parallel workers (default: 4)
  --verbose, -v      Enable verbose logging
```

### Web Interface
```bash
python web_app.py [OPTIONS]

Options:
  --output PATH      Directory with analysis results (default: ./output/)
  --port PORT        Web server port (default: 5000)
  --host HOST        Web server host (default: 127.0.0.1)
```

## 📄 Output Files

### Executive Summary (`executive_summary_*.txt`)
- **Analysis Overview**: Time period, files analyzed, key metrics
- **Key Findings**: Total errors, error rate, peak periods
- **Top Error Categories**: Ranked by frequency
- **Critical Time Periods**: 5-minute windows with highest error activity
- **Error Patterns**: Cascading failures and error bursts
- **Recommendations**: Actionable next steps based on findings
- **Top Error Files**: Files with most errors

### Detailed CSV (`detailed_log_analysis_*.csv`)
- **Complete log entries** within the target timeframe
- **Parsed fields**: timestamp, log level, error categories, transaction ID
- **File metadata**: source file, line number
- **Error classification**: boolean flags for each error category

### Interactive Dashboard (`interactive_dashboard.html`)
- **Multi-panel visualization** with error trends, categories, timelines
- **Hover details** and interactive exploration
- **Responsive design** for different screen sizes

### Static Charts (`*.png`)
- **Error Categories Bar Chart**: Distribution by error type
- **Timeline Charts**: Log volume and errors over time  
- **Log Level Pie Chart**: Distribution by severity

## 🕐 Timeline for Your 2 PM Deadline

| Time | Task | Expected Duration |
|------|------|------------------|
| **Now** | Copy log files to `/logs/` directory | 2 minutes |
| **+2 min** | Run `python main.py` | 1-3 minutes |
| **+5 min** | Review executive summary | 5 minutes |
| **+10 min** | Analyze detailed CSV data | 10 minutes |
| **+20 min** | Create presentation slides from findings | 15 minutes |
| **1:45 PM** | Final review and prep | 15 minutes |

## 🔍 How It Works

### 1. **File Discovery**
- Recursively scans `logs/` directory
- Finds all `.log` and `.txt` files
- Collects metadata (size, modification time)

### 2. **Intelligent Parsing**
- **Auto-detects timestamp formats**: ISO 8601, Apache/Nginx, syslog, custom formats
- **Extracts log levels**: ERROR, WARN, INFO, DEBUG, FATAL, CRITICAL
- **Identifies transaction IDs**: Various patterns (transaction_id, txn_id, order_id, ref_id)
- **Classifies errors**: Pattern matching against 30+ error types

### 3. **Timeframe Filtering**
- Converts all timestamps to pandas datetime
- Filters to **yesterday 9:00 AM - 2:00 PM** window
- Handles timezone issues and malformed timestamps

### 4. **Pattern Analysis**
- **Error frequency**: Counts per category per 5-minute window
- **Peak detection**: Identifies top 5 busiest error periods
- **Cascading failures**: Multiple errors for same transaction
- **Error bursts**: >5 errors in 1-minute windows
- **Temporal patterns**: Hourly error distribution

### 5. **Report Generation**
- **Executive summary**: Management-ready text report
- **CSV export**: Complete data for further analysis
- **Visualizations**: Charts and interactive dashboard
- **File optimization**: Proper encoding and formatting

## 🛠️ Customization

### Adding New Error Patterns
Edit `src/log_parser.py`, add to `error_patterns` dictionary:

```python
'your_custom_errors': [
    re.compile(r'your\s+pattern', re.IGNORECASE),
    # Add more patterns...
]
```

### Changing Time Window
Edit `src/data_analyzer.py`, modify `DataAnalyzer.__init__()`:

```python
self.start_time = self.target_date.replace(hour=8, minute=0)  # 8 AM start
self.end_time = self.target_date.replace(hour=16, minute=0)   # 4 PM end
```

### Adding Custom Timestamp Formats
Edit `src/log_parser.py`, add to `timestamp_patterns`:

```python
(re.compile(r'your_timestamp_regex', re.IGNORECASE), 'your_strftime_format')
```

## 🚨 Troubleshooting

### "No log files found"
- Verify files are in `/Users/jonathanellwood/log-analyzer/logs/`
- Check file extensions (only `.log` and `.txt` are scanned)
- Ensure files aren't empty or corrupted

### "No data in target timeframe"
- Check if your logs have timestamps from yesterday 9-2 PM
- Try running with `--date YYYY-MM-DD` for a specific date
- Run with `--verbose` to see timestamp parsing details

### "Analysis failed"
- Check the log file in `output/logs/log_analyzer_*.log`
- Verify Python dependencies are installed
- Try running with fewer workers: `--workers 1`

### Memory Issues (Large Log Files)
- The tool processes files in parallel but loads data into memory
- For very large datasets (>1GB), consider splitting files first
- Monitor memory usage with `python main.py --verbose`

## 🎯 For Your Specific Use Case

Based on your ticket selling and credit card processing failure analysis:

### Key Questions to Answer
1. **What time did errors peak?** → Check "Peak Error Period" in summary
2. **Were payment gateways the issue?** → Look for "credit_card_errors" category
3. **Database connectivity problems?** → Check "database_errors" count  
4. **Which transactions failed?** → Review transaction IDs in CSV
5. **Was it a cascade failure?** → Look for "Cascading Failures" section

### Focus Areas in the CSV
- Filter by `error_categories` containing "credit_card_errors"
- Sort by `timestamp` to see chronological order
- Group by `transaction_id` to see impact per customer
- Check `file_path` to identify problematic system components

## 📞 Quick Help

If you run into issues with your 2 PM deadline:

1. **First**: Run `python main.py --verbose` to see detailed progress
2. **If that fails**: Check `output/logs/log_analyzer_*.log` for error details
3. **For large files**: Try `python main.py --workers 1` to reduce memory usage
4. **Emergency fallback**: Use basic grep commands on your log files to find error patterns

The tool is designed to be resilient and handle various log formats, but if you encounter issues, the verbose logging will help identify the problem quickly.

## 🚀 Success Indicators

You'll know the analysis worked when you see:

```
🎉 Analysis completed successfully!

📋 Executive Summary: /path/to/summary.txt
📊 Detailed Data: /path/to/analysis.csv  
🌐 Interactive Dashboard: /path/to/dashboard.html

✅ Ready for your 2:00 PM deadline!
```

**Good luck with your root cause analysis! 🍀**