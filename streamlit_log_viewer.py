import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

# Configure Streamlit page
st.set_page_config(
    page_title="Log Analyzer - Data Viewer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
    }
    
    .stat-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    
    .error-row {
        background-color: #fee;
    }
    
    .warning-row {
        background-color: #fff3cd;
    }
    
    .stDataFrame {
        border: 1px solid #dee2e6;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

def load_data(uploaded_file):
    """Load and process the CSV data"""
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file, low_memory=False)
        
        # Convert timestamp to datetime, handle errors
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        except Exception as e:
            st.warning(f"Warning: Could not parse timestamps properly: {str(e)}")
        
        # Convert boolean columns
        bool_columns = ['has_any_error', 'is_error_strict', 'is_warning', 'has_error', 
                       'is_timeout_errors', 'is_exception_errors', 'is_server_errors']
        
        for col in bool_columns:
            if col in df.columns:
                try:
                    df[col] = df[col].astype(str).str.lower().isin(['true', '1', 'yes'])
                except Exception as e:
                    st.warning(f"Warning: Could not process boolean column {col}: {str(e)}")
        
        return df
    except Exception as e:
        st.error(f"Error loading CSV file: {str(e)}")
        return None

def create_summary_stats(df):
    """Create summary statistics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stat-container">
            <h3>📊 Total Entries</h3>
            <h2>{:,}</h2>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        error_count = df['has_error'].sum() if 'has_error' in df.columns else 0
        st.markdown("""
        <div class="stat-container">
            <h3>❌ Errors</h3>
            <h2>{:,}</h2>
        </div>
        """.format(error_count), unsafe_allow_html=True)
    
    with col3:
        warning_count = df['is_warning'].sum() if 'is_warning' in df.columns else 0
        st.markdown("""
        <div class="stat-container">
            <h3>⚠️ Warnings</h3>
            <h2>{:,}</h2>
        </div>
        """.format(warning_count), unsafe_allow_html=True)
    
    with col4:
        file_count = df['file_name'].nunique() if 'file_name' in df.columns else 0
        st.markdown("""
        <div class="stat-container">
            <h3>📁 Files</h3>
            <h2>{:,}</h2>
        </div>
        """.format(file_count), unsafe_allow_html=True)

def create_visualizations(df):
    """Create visualizations"""
    st.subheader("📈 Data Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'log_level' in df.columns:
            # Log level distribution
            level_counts = df['log_level'].value_counts()
            fig_levels = px.pie(
                values=level_counts.values, 
                names=level_counts.index, 
                title="Log Level Distribution",
                color_discrete_map={
                    'ERROR': '#dc3545',
                    'WARNING': '#ffc107', 
                    'INFO': '#17a2b8',
                    'DEBUG': '#6c757d'
                }
            )
            st.plotly_chart(fig_levels, width='stretch')
    
    with col2:
        if 'file_name' in df.columns:
            # Top files by entry count
            top_files = df['file_name'].value_counts().head(10)
            fig_files = px.bar(
                x=top_files.values,
                y=top_files.index,
                orientation='h',
                title="Top 10 Files by Entry Count",
                labels={'x': 'Entry Count', 'y': 'File Name'}
            )
            fig_files.update_layout(height=400)
            st.plotly_chart(fig_files, width='stretch')
    
    # Timeline of errors
    if 'timestamp' in df.columns and 'has_error' in df.columns:
        st.subheader("🕒 Error Timeline")
        
        # Group by hour and count errors
        df_errors = df[df['has_error'] == True].copy()
        if len(df_errors) > 0:
            df_errors['hour'] = df_errors['timestamp'].dt.floor('h')
            hourly_errors = df_errors.groupby('hour').size().reset_index(name='error_count')
            
            fig_timeline = px.line(
                hourly_errors, 
                x='hour', 
                y='error_count',
                title="Errors Over Time (Hourly)",
                labels={'hour': 'Time', 'error_count': 'Error Count'}
            )
            fig_timeline.update_traces(line_color='#dc3545', line_width=3)
            st.plotly_chart(fig_timeline, width='stretch')

def apply_filters(df):
    """Apply filters based on sidebar inputs"""
    filtered_df = df.copy()
    
    # File filter
    if 'file_name' in df.columns:
        files = sorted(df['file_name'].dropna().unique())
        selected_files = st.sidebar.multiselect(
            "📁 Filter by Files:",
            options=files,
            default=[],
            help="Select one or more files to filter by"
        )
        
        if selected_files:
            filtered_df = filtered_df[filtered_df['file_name'].isin(selected_files)]
    
    # Log level filter
    if 'log_level' in df.columns:
        levels = sorted(df['log_level'].dropna().unique())
        selected_levels = st.sidebar.multiselect(
            "📊 Filter by Log Level:",
            options=levels,
            default=levels,
            help="Select log levels to include"
        )
        
        if selected_levels:
            filtered_df = filtered_df[filtered_df['log_level'].isin(selected_levels)]
    
    # Error type filter
    if 'has_error' in df.columns:
        error_filter = st.sidebar.selectbox(
            "🎯 Error Filter:",
            options=["All", "Errors Only", "Non-Errors Only"],
            help="Filter by error status"
        )
        
        if error_filter == "Errors Only":
            filtered_df = filtered_df[filtered_df['has_error'] == True]
        elif error_filter == "Non-Errors Only":
            filtered_df = filtered_df[filtered_df['has_error'] == False]
    
    # Date range filter
    if 'timestamp' in df.columns:
        st.sidebar.subheader("📅 Date Range Filter")
        
        min_date = df['timestamp'].min().date()
        max_date = df['timestamp'].max().date()
        
        start_date = st.sidebar.date_input(
            "Start Date:",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
        
        end_date = st.sidebar.date_input(
            "End Date:",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
        
        if start_date <= end_date:
            start_datetime = pd.Timestamp(start_date)
            end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1)
            
            filtered_df = filtered_df[
                (filtered_df['timestamp'] >= start_datetime) & 
                (filtered_df['timestamp'] < end_datetime)
            ]
    
    # Search filter
    search_term = st.sidebar.text_input(
        "🔍 Search in Messages:",
        help="Search for specific text in log messages"
    )
    
    if search_term and 'message' in df.columns:
        filtered_df = filtered_df[
            filtered_df['message'].str.contains(search_term, case=False, na=False)
        ]
    
    return filtered_df

def style_dataframe(df):
    """Apply styling to the dataframe"""
    def highlight_errors(row):
        if 'has_error' in row and row['has_error']:
            return ['background-color: #fee'] * len(row)
        elif 'is_warning' in row and row['is_warning']:
            return ['background-color: #fff3cd'] * len(row)
        else:
            return [''] * len(row)
    
    # Select columns to display
    display_columns = []
    available_columns = [
        'timestamp', 'log_level', 'file_name', 'message', 
        'error_categories', 'line_number', 'has_error', 'is_warning'
    ]
    
    for col in available_columns:
        if col in df.columns:
            display_columns.append(col)
    
    display_df = df[display_columns].copy()
    
    # Format timestamp
    if 'timestamp' in display_df.columns:
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Truncate long messages
    if 'message' in display_df.columns:
        display_df['message'] = display_df['message'].astype(str).apply(
            lambda x: x[:200] + '...' if len(x) > 200 else x
        )
    
    return display_df.style.apply(highlight_errors, axis=1)

def main():
    """Main application"""
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Log Analyzer - Data Viewer</h1>
        <p style="color: white; text-align: center; margin: 0;">Interactive log data exploration tool</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("📋 Configuration")
    
    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "📂 Upload CSV File:",
        type=['csv'],
        help="Upload your data.csv file here"
    )
    
    if uploaded_file is not None:
        # Load data
        with st.spinner("Loading data..."):
            df = load_data(uploaded_file)
        
        if df is not None:
            st.success(f"✅ Loaded {len(df):,} log entries from {df['file_name'].nunique() if 'file_name' in df.columns else 'unknown'} files")
            
            # Apply filters
            st.sidebar.header("🎛️ Filters")
            filtered_df = apply_filters(df)
            
            # Show filtered count
            if len(filtered_df) != len(df):
                st.info(f"🔍 Showing {len(filtered_df):,} of {len(df):,} entries after filtering")
            
            # Summary statistics
            create_summary_stats(filtered_df)
            
            # Visualizations
            if len(filtered_df) > 0:
                create_visualizations(filtered_df)
                
                # Data table
                st.subheader("📋 Log Entries")
                
                # Pagination
                entries_per_page = st.selectbox("Entries per page:", [50, 100, 200, 500], index=1)
                
                total_pages = (len(filtered_df) - 1) // entries_per_page + 1
                page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
                
                start_idx = (page - 1) * entries_per_page
                end_idx = min(start_idx + entries_per_page, len(filtered_df))
                
                page_df = filtered_df.iloc[start_idx:end_idx]
                
                # Display styled dataframe
                if len(page_df) > 0:
                    styled_df = style_dataframe(page_df)
                    st.dataframe(
                        styled_df,
                        width='stretch',
                        hide_index=True
                    )
                    
                    st.caption(f"Showing entries {start_idx + 1}-{end_idx} of {len(filtered_df)}")
                    
                    # Download filtered data
                    if st.button("⬬ Download Filtered Data as CSV"):
                        csv_buffer = io.StringIO()
                        filtered_df.to_csv(csv_buffer, index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_buffer.getvalue(),
                            file_name=f"filtered_log_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                else:
                    st.warning("No entries match the current filters.")
            else:
                st.warning("No data to display with current filters.")
    
    else:
        # Instructions
        st.info("""
        ### 📋 Instructions:
        
        1. **Upload your CSV file** using the file uploader in the sidebar
        2. **Apply filters** to focus on specific files, log levels, or time ranges
        3. **Explore the data** using the interactive visualizations and table
        4. **Download filtered results** for further analysis
        
        ### 📁 Expected CSV format:
        Your CSV file should contain columns like:
        - `timestamp` - Log entry timestamp
        - `log_level` - ERROR, WARNING, INFO, DEBUG
        - `file_name` - Source log file name
        - `message` - Log message content
        - `has_error` - Boolean error flag
        - `error_categories` - Error classification
        """)

if __name__ == "__main__":
    main()