#!/usr/bin/env python3
"""
Web Interface for Log Analyzer
Flask-based web application to view analysis results and download reports.
"""

import os
import sys
from flask import Flask, render_template_string, send_file, jsonify, request
from pathlib import Path
import json
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# Global variables to store analysis results
analysis_results = {}
output_dir = None

def load_analysis_results(output_path):
    """Load analysis results from output directory."""
    global analysis_results, output_dir
    output_dir = Path(output_path)
    
    # Look for the most recent analysis results
    # This is a simplified version - in production you'd want better file management
    csv_files = list(output_dir.glob("detailed_log_analysis_*.csv"))
    summary_files = list(output_dir.glob("executive_summary_*.txt"))
    
    if csv_files and summary_files:
        # Get the most recent files
        latest_csv = max(csv_files, key=os.path.getctime)
        latest_summary = max(summary_files, key=os.path.getctime)
        
        analysis_results = {
            'csv_file': str(latest_csv),
            'summary_file': str(latest_summary),
            'dashboard_file': str(output_dir / 'interactive_dashboard.html'),
            'charts': {
                'error_categories': str(output_dir / 'error_categories_chart.png'),
                'timeline': str(output_dir / 'timeline_chart.png'),
                'log_levels': str(output_dir / 'log_levels_pie_chart.png')
            }
        }
        return True
    
    return False

# HTML Templates
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log Analyzer - Root Cause Analysis</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .nav {
            background: #2c3e50;
            padding: 0;
        }
        .nav ul {
            list-style: none;
            margin: 0;
            padding: 0;
            display: flex;
        }
        .nav li {
            flex: 1;
        }
        .nav a {
            display: block;
            padding: 15px 20px;
            color: white;
            text-decoration: none;
            text-align: center;
            transition: background 0.3s;
        }
        .nav a:hover, .nav a.active {
            background: #34495e;
        }
        .content {
            padding: 30px;
        }
        .status-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .status-card h3 {
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-card .value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .status-card.error .value { color: #e74c3c; }
        .status-card.warning .value { color: #f39c12; }
        .status-card.success .value { color: #27ae60; }
        .status-card.info .value { color: #3498db; }
        .downloads {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .downloads h3 {
            margin: 0 0 15px 0;
            color: #2c3e50;
        }
        .download-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .download-btn {
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .download-btn:hover {
            background: #2980b9;
        }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        .chart-container {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            background: white;
        }
        .chart-container img {
            width: 100%;
            height: auto;
            border-radius: 4px;
        }
        .error-message {
            background: #e74c3c;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px;
            text-align: center;
        }
        .instructions {
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin: 20px 0;
        }
        .instructions h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        @media (max-width: 768px) {
            .nav ul {
                flex-direction: column;
            }
            .download-buttons {
                flex-direction: column;
            }
            .charts-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Log Analyzer</h1>
            <p>Root Cause Analysis Dashboard</p>
        </div>
        
        <nav class="nav">
            <ul>
                <li><a href="/" class="active">📊 Overview</a></li>
                <li><a href="/dashboard" target="_blank">📈 Interactive Dashboard</a></li>
                <li><a href="/summary" target="_blank">📋 Executive Summary</a></li>
            </ul>
        </nav>
        
        <div class="content">
            {% if has_results %}
                <div class="status-cards">
                    <div class="status-card info">
                        <h3>Analysis Date</h3>
                        <div class="value">{{ analysis_date }}</div>
                    </div>
                    <div class="status-card info">
                        <h3>Log Entries</h3>
                        <div class="value">{{ total_entries|default("N/A") }}</div>
                    </div>
                    <div class="status-card error">
                        <h3>Errors Found</h3>
                        <div class="value">{{ total_errors|default("0") }}</div>
                    </div>
                    <div class="status-card warning">
                        <h3>Error Rate</h3>
                        <div class="value">{{ error_rate|default("0%") }}</div>
                    </div>
                </div>
                
                <div class="downloads">
                    <h3>📁 Download Reports</h3>
                    <div class="download-buttons">
                        <a href="/download/csv" class="download-btn">📊 Detailed CSV</a>
                        <a href="/download/summary" class="download-btn">📋 Executive Summary</a>
                        <a href="/dashboard" target="_blank" class="download-btn">🌐 Interactive Dashboard</a>
                    </div>
                </div>
                
                <div class="charts-section">
                    <h3>📈 Visualizations</h3>
                    <div class="charts-grid">
                        {% if charts.error_categories %}
                        <div class="chart-container">
                            <h4>Error Categories</h4>
                            <img src="/chart/error_categories" alt="Error Categories Chart">
                        </div>
                        {% endif %}
                        
                        {% if charts.timeline %}
                        <div class="chart-container">
                            <h4>Timeline Analysis</h4>
                            <img src="/chart/timeline" alt="Timeline Chart">
                        </div>
                        {% endif %}
                        
                        {% if charts.log_levels %}
                        <div class="chart-container">
                            <h4>Log Level Distribution</h4>
                            <img src="/chart/log_levels" alt="Log Levels Chart">
                        </div>
                        {% endif %}
                    </div>
                </div>
            {% else %}
                <div class="instructions">
                    <h3>🚀 Getting Started</h3>
                    <p>No analysis results found. To get started:</p>
                    <ol>
                        <li>Place your log files (.log, .txt) in the <code>logs/</code> directory</li>
                        <li>Run the analysis: <code>python main.py</code></li>
                        <li>Start the web server: <code>python web_app.py --output ./output</code></li>
                    </ol>
                    <p>The analyzer will focus on yesterday's logs between 9:00 AM and 2:00 PM, looking for:</p>
                    <ul>
                        <li>Credit card processing errors</li>
                        <li>Database connection issues</li>
                        <li>Server errors (5xx codes)</li>
                        <li>Transaction timeouts</li>
                        <li>Authentication failures</li>
                    </ul>
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main dashboard page."""
    has_results = bool(analysis_results)
    
    if has_results:
        # You would load actual analysis data here
        # For now, we'll use placeholder data
        return render_template_string(MAIN_TEMPLATE, 
                                    has_results=True,
                                    analysis_date="2023-10-01",
                                    total_entries="1,234",
                                    total_errors="56",
                                    error_rate="4.5%",
                                    charts=analysis_results.get('charts', {}))
    else:
        return render_template_string(MAIN_TEMPLATE, has_results=False)

@app.route('/download/<file_type>')
def download_file(file_type):
    """Download report files."""
    if not analysis_results:
        return "No analysis results available", 404
    
    if file_type == 'csv' and 'csv_file' in analysis_results:
        return send_file(analysis_results['csv_file'], as_attachment=True)
    elif file_type == 'summary' and 'summary_file' in analysis_results:
        return send_file(analysis_results['summary_file'], as_attachment=True)
    
    return "File not found", 404

@app.route('/chart/<chart_type>')
def serve_chart(chart_type):
    """Serve chart images."""
    if not analysis_results or 'charts' not in analysis_results:
        return "No charts available", 404
    
    chart_mapping = {
        'error_categories': 'error_categories',
        'timeline': 'timeline',
        'log_levels': 'log_levels'
    }
    
    if chart_type in chart_mapping:
        chart_file = analysis_results['charts'].get(chart_mapping[chart_type])
        if chart_file and os.path.exists(chart_file):
            return send_file(chart_file)
    
    return "Chart not found", 404

@app.route('/dashboard')
def dashboard():
    """Serve interactive dashboard."""
    if not analysis_results or 'dashboard_file' not in analysis_results:
        return "Dashboard not available", 404
    
    dashboard_file = analysis_results['dashboard_file']
    if os.path.exists(dashboard_file):
        return send_file(dashboard_file)
    
    return "Dashboard not found", 404

@app.route('/summary')
def summary():
    """Serve executive summary as HTML."""
    if not analysis_results or 'summary_file' not in analysis_results:
        return "Summary not available", 404
    
    summary_file = analysis_results['summary_file']
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            content = f.read()
        
        # Convert plain text to HTML with basic formatting
        html_content = content.replace('\n', '<br>')
        html_content = html_content.replace('━━━', '<hr>')
        html_content = html_content.replace('#', '<h2>').replace('</h2>', '</h2>')
        
        html_template = f"""
        <html>
        <head>
            <title>Executive Summary</title>
            <style>
                body {{ font-family: monospace; padding: 20px; background: #f5f5f5; }}
                .content {{ background: white; padding: 30px; border-radius: 8px; max-width: 800px; margin: 0 auto; }}
                hr {{ border: 1px solid #ddd; }}
                h2 {{ color: #2c3e50; }}
            </style>
        </head>
        <body>
            <div class="content">
                <pre>{content}</pre>
            </div>
        </body>
        </html>
        """
        return html_template
    
    return "Summary not found", 404

def main():
    """Main entry point for web application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Log Analyzer Web Interface")
    parser.add_argument('--output', type=str, default='./output', 
                       help='Output directory containing analysis results')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to run the web server (default: 5000)')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Host to bind the web server (default: 127.0.0.1)')
    
    args = parser.parse_args()
    
    # Load analysis results
    if load_analysis_results(args.output):
        print(f"✅ Analysis results loaded from: {args.output}")
    else:
        print(f"⚠️  No analysis results found in: {args.output}")
        print("   Run 'python main.py' first to generate analysis results.")
    
    print(f"🌐 Starting web server at http://{args.host}:{args.port}")
    print("   Press Ctrl+C to stop the server")
    
    app.run(host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()