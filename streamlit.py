import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go

# Data Loading and Preprocessing
@st.cache_data
def load_and_preprocess_data(file_path):
    # Read first sheet (Financial Data)
    financial_df = pd.read_excel(file_path, sheet_name=0)
    
    # Read second sheet (Sector Data)
    sector_df = pd.read_excel(file_path, sheet_name=1, header=None)
    sector_df.columns = ['Ticker', 'Sector']
    
    # Merge financial and sector data
    financial_df = financial_df.merge(sector_df, left_on='Exchange:Ticker', right_on='Ticker', how='left')
    
    return financial_df

# Growth Rate Calculation Function
def calculate_growth_rates(df):
    metrics = {
        'Total_Revenue': ['Total Revenue [LTM - 16]', 'Total Revenue [LTM - 12]', 
                          'Total Revenue [LTM - 8]', 'Total Revenue [LTM - 4]', 'Total Revenue [LTM]'],
        'Net_Income': ['Net Income [LTM - 16]', 'Net Income [LTM - 12]', 
                       'Net Income [LTM - 8]', 'Net Income [LTM - 4]', 'Net Income [LTM]'],
        'EBITDA': ['EBITDA [LTM - 16]', 'EBITDA [LTM - 12]', 
                   'EBITDA [LTM - 8]', 'EBITDA [LTM - 4]', 'EBITDA [LTM]']
    }
    
    company_growth_data = []
    
    for _, row in df.iterrows():
        company_growth = {
            'Ticker': row['Exchange:Ticker'], 
            'Company_Name': row['Company Name'], 
            'Sector': row['Sector']
        }
        
        for metric_name, columns in metrics.items():
            growth_rates = []
            for i in range(1, len(columns)):
                try:
                    current_value = row[columns[i]]
                    previous_value = row[columns[i-1]]
                    
                    # Skip if either value is zero or NaN
                    if pd.isna(current_value) or pd.isna(previous_value) or previous_value == 0:
                        growth_rates.append(None)
                    else:
                        growth_rate = ((current_value - previous_value) / previous_value) * 100
                        growth_rates.append(growth_rate)
                except Exception as e:
                    growth_rates.append(None)
            
            # Calculate average growth rate, skipping None values
            avg_growth = np.mean([g for g in growth_rates if g is not None])
            
            company_growth[f'{metric_name}_Growth_Rates'] = growth_rates
            company_growth[f'{metric_name}_Avg_Growth'] = avg_growth
        
        company_growth_data.append(company_growth)
    
    return pd.DataFrame(company_growth_data)

# Sector-wise Growth Calculation
def calculate_sector_growth(growth_df):
    sector_growth = growth_df.groupby('Sector').agg({
        'Total_Revenue_Avg_Growth': 'median',
        'Net_Income_Avg_Growth': 'median',
        'EBITDA_Avg_Growth': 'median'
    }).reset_index()
    return sector_growth

# Streamlit Dashboard
def main():
    st.set_page_config(layout="wide", page_title="Indian Companies Growth Dashboard")
    
    st.title("🚀 Indian Companies Growth Dashboard")
    
    # File Upload
    uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'])
    
    if uploaded_file is not None:
        # Load Data
        financial_df = load_and_preprocess_data(uploaded_file)
        
        # Calculate Growth Rates
        growth_df = calculate_growth_rates(financial_df)
        sector_growth_df = calculate_sector_growth(growth_df)
        
        # Sidebar Filters
        st.sidebar.header("Dashboard Filters")
        selected_metrics = st.sidebar.multiselect(
            "Select Metrics", 
            ['Total Revenue', 'Net Income', 'EBITDA'], 
            default=['Total Revenue']
        )
        
        selected_sectors = st.sidebar.multiselect(
            "Select Sectors", 
            growth_df['Sector'].unique(), 
            default=growth_df['Sector'].unique()
        )
        
        # Filter Data
        filtered_growth_df = growth_df[growth_df['Sector'].isin(selected_sectors)]
        filtered_sector_growth_df = sector_growth_df[sector_growth_df['Sector'].isin(selected_sectors)]
        
        # Tabs for Different Views
        tab1, tab2, tab3 = st.tabs(["Company Growth", "Sector Comparison", "Detailed Insights"])
        
        with tab1:
            st.header("Company Growth Metrics")
            
            for metric in selected_metrics:
                metric_key = f"{metric.replace(' ', '_')}_Avg_Growth"
                
                fig = px.bar(
                    filtered_growth_df, 
                    x='Ticker', 
                    y=metric_key, 
                    color='Sector',
                    title=f"{metric} Growth Rates by Company",
                    labels={'y': 'Average Growth Rate (%)'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.header("Sector Comparison")
            
            for metric in selected_metrics:
                metric_key = f"{metric.replace(' ', '_')}_Avg_Growth"
                
                fig = px.bar(
                    filtered_sector_growth_df, 
                    x='Sector', 
                    y=metric_key,
                    title=f"Median {metric} Growth by Sector",
                    labels={'y': 'Median Growth Rate (%)'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.header("Detailed Growth Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Company Growth Summary")
                st.dataframe(filtered_growth_df[['Ticker', 'Sector'] + 
                                                [f'{m.replace(" ", "_")}_Avg_Growth' for m in selected_metrics]])
            
            with col2:
                st.subheader("Sector Growth Summary")
                st.dataframe(filtered_sector_growth_df)

if __name__ == '__main__':
    main()
