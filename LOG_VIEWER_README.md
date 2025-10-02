# Log Analyzer Data Viewer

This directory contains two interactive UI tools for exploring your log analysis data:

## 🌐 HTML/JavaScript Version (log_viewer.html)

**Best for**: Quick viewing, sharing, no dependencies required

### How to use

1. Copy your CSV file to this directory and rename it to `data.csv`
2. Open `log_viewer.html` in any modern web browser
3. Click "Choose File" and select your `data.csv` file
4. Use the filters to explore your data

### Features

- ✅ File-based filtering (multi-select)
- ✅ Log level filtering (ERROR, WARNING, INFO, DEBUG)
- ✅ Date/time range filtering
- ✅ Message search functionality
- ✅ Error type filtering
- ✅ Real-time statistics
- ✅ Paginated results (100 entries per page)
- ✅ No installation required - runs in browser

## 🐍 Python Streamlit Version (streamlit_log_viewer.py)

**Best for**: Advanced analysis, interactive visualizations, data export

### How to use

1. Copy your CSV file to this directory and rename it to `data.csv`
2. Run: `streamlit run streamlit_log_viewer.py`
3. Upload your CSV file through the web interface
4. Explore with advanced filters and visualizations

### Features

- ✅ All HTML version features plus:
- 📊 Interactive charts and visualizations
- 📈 Error timeline analysis
- 🥧 Log level distribution pie charts
- 📁 Top files by entry count
- 💾 Download filtered data as CSV
- 🎨 Advanced styling and highlighting
- 📱 Responsive design

## 📋 Quick Start Commands

### For HTML Version

```bash
# 1. Copy and rename your CSV file
cp output/detailed_log_analysis_20251002_132200.csv data.csv

# 2. Open in browser (macOS)
open log_viewer.html
```

### For Streamlit Version

```bash
# 1. Copy and rename your CSV file  
cp output/detailed_log_analysis_20251002_132200.csv data.csv

# 2. Run Streamlit app
/Users/jonathanellwood/log-analyzer/.venv/bin/python -m streamlit run streamlit_log_viewer.py
```

## 📊 Expected CSV Columns

Both viewers expect these columns in your CSV:

- `timestamp` - Log entry timestamp
- `log_level` - ERROR, WARNING, INFO, DEBUG
- `file_name` - Source log file name  
- `message` - Log message content
- `has_error` - Boolean error flag
- `is_warning` - Boolean warning flag
- `error_categories` - Error classification
- `line_number` - Line number in source file

## 🔍 Filter Options

Both tools provide these filtering capabilities:

1. **File Filter**: Select specific log files to view
2. **Log Level Filter**: Filter by ERROR, WARNING, INFO, DEBUG
3. **Error Type Filter**: Show only errors, only non-errors, or all
4. **Date Range Filter**: Filter by timestamp range
5. **Message Search**: Search within log messages
6. **Real-time Statistics**: Live count updates as you filter

## 💡 Tips

- **Large Files**: The HTML version handles large CSV files well in modern browsers
- **Performance**: Use filters to reduce the dataset for better performance
- **Sharing**: HTML version is perfect for sharing - just send the HTML file
- **Analysis**: Streamlit version offers more advanced analytical features
- **Mobile**: Both versions work on mobile devices with responsive design
