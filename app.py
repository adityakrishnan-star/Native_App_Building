import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="Executive Retail Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.05); background: white; }
    .css-10trblm { color: #1c2b46; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA PROCESSING FUNCTION ---
def load_and_clean_data(sales_file, master_file):
    df_sales = pd.read_excel(sales_file)
    df_master = pd.read_excel(master_file)
    
    # Join datasets
    df = pd.merge(df_sales, df_master, on='store_id', how='left')
    
    # Data Cleaning: Net Sales = Gross - Discount (if Net is missing)
    df['net_sales'] = df['net_sales'].fillna(df['gross_sales'] - df['discount_amount'])
    
    # Ensure date format
    df['week_start_date'] = pd.to_datetime(df['week_start_date'])
    
    return df

# --- HEADER ---
st.title("📊 Retail Sales Intelligence Dashboard")
st.subheader("Executive Performance Overview")

# --- SIDEBAR: DATA INPUT & FILTERS ---
with st.sidebar:
    st.header("📂 Data Integration")
    sales_upload = st.file_uploader("Upload Weekly Sales (.xlsx)", type="xlsx")
    master_upload = st.file_uploader("Upload Store Master (.xlsx)", type="xlsx")
    
    if sales_upload and master_upload:
        raw_df = load_and_clean_data(sales_upload, master_upload)
        
        st.header("🔍 Global Filters")
        
        # Multi-select filters
        weeks = st.multiselect("Week Start Date", options=sorted(raw_df['week_start_date'].unique()), default=[])
        regions = st.multiselect("Region", options=raw_df['region'].unique())
        cities = st.multiselect("City", options=raw_df['city'].unique())
        formats = st.multiselect("Store Format", options=raw_df['store_format'].unique())
        categories = st.multiselect("Product Category", options=raw_df['category'].unique())
        
        # Filtering logic
        df = raw_df.copy()
        if weeks: df = df[df['week_start_date'].isin(weeks)]
        if regions: df = df[df['region'].isin(regions)]
        if cities: df = df[df['city'].isin(cities)]
        if formats: df = df[df['store_format'].isin(formats)]
        if categories: df = df[df['category'].isin(categories)]
        
        ready = True
    else:
        st.info("Please upload both Excel files to initialize the dashboard.")
        ready = False

# --- MAIN DASHBOARD ---
if ready:
    # --- KPI CALCULATIONS ---
    total_net_sales = df['net_sales'].sum()
    total_target = df['sales_target'].sum()
    target_achievement = (total_net_sales / total_target) * 100 if total_target != 0 else 0
    atv = total_net_sales / df['transactions'].sum() if df['transactions'].sum() != 0 else 0
    return_rate = (df['returns_amount'].sum() / total_net_sales) * 100 if total_net_sales != 0 else 0
    discount_rate = (df['discount_amount'].sum() / df['gross_sales'].sum()) * 100 if df['gross_sales'].sum() != 0 else 0
    conv_rate = (df['transactions'].sum() / df['footfall'].sum()) * 100 if df['footfall'].sum() != 0 else 0
    total_stockouts = df['stockout_flag'].sum()

    # --- KPI DISPLAY ---
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Net Sales", f"${total_net_sales:,.0f}")
    col2.metric("Target Achievement", f"{target_achievement:.1f}%", delta=f"{target_achievement-100:.1f}%")
    col3.metric("ATV", f"${atv:.2f}")
    col4.metric("Return Rate", f"{return_rate:.1f}%")
    col5.metric("Conv. Rate", f"{conv_rate:.1f}%")
    col6.metric("Stockouts", f"{total_stockouts:,.0f}")

    st.markdown("---")

    # --- VISUALIZATION ROW 1 ---
    row1_col1, row1_col2 = st.columns([2, 1])

    with row1_col1:
        st.subheader("Weekly Sales Trend")
        trend_df = df.groupby('week_start_date')['net_sales'].sum().reset_index()
        fig_trend = px.line(trend_df, x='week_start_date', y='net_sales', template="plotly_white", 
                            line_shape="spline", color_discrete_sequence=['#1f77b4'])
        st.plotly_chart(fig_trend, use_container_width=True)

    with row1_col2:
        st.subheader("Regional Achievement")
        reg_df = df.groupby('region')[['net_sales', 'sales_target']].sum().reset_index()
        fig_reg = go.Figure(data=[
            go.Bar(name='Sales', x=reg_df['region'], y=reg_df['net_sales'], marker_color='#1f77b4'),
            go.Bar(name='Target', x=reg_df['region'], y=reg_df['sales_target'], marker_color='#ced4da')
        ])
        fig_reg.update_layout(barmode='group', template="plotly_white", margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_reg, use_container_width=True)

    # --- VISUALIZATION ROW 2 ---
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("Category Performance & Returns")
        cat_df = df.groupby('category').agg({'net_sales':'sum', 'returns_amount':'sum'}).reset_index()
        cat_df['ret_rate'] = (cat_df['returns_amount'] / cat_df['net_sales']) * 100
        fig_cat = px.bar(cat_df, x='category', y='net_sales', color='ret_rate',
                         color_continuous_scale='RdYlGn_r', title="Color by Return Rate %")
        st.plotly_chart(fig_cat, use_container_width=True)

    with row2_col2:
        st.subheader("Store Target Leaderboard")
        store_df = df.groupby('store_name')[['net_sales', 'sales_target']].sum().reset_index()
        store_df['ach_pct'] = (store_df['net_sales'] / store_df['sales_target']) * 100
        top_stores = store_df.sort_values('ach_pct', ascending=False).head(10)
        fig_store = px.bar(top_stores, x='ach_pct', y='store_name', orientation='h',
                           color='ach_pct', color_continuous_scale='Blues')
        st.plotly_chart(fig_store, use_container_width=True)

    # --- VISUALIZATION ROW 3 ---
    st.subheader("Stockout Risk Heatmap (Category vs Region)")
    stock_df = df.groupby(['region', 'category'])['stockout_flag'].sum().reset_index()
    fig_heat = px.density_heatmap(stock_df, x='category', y='region', z='stockout_flag', 
                                  text_auto=True, color_continuous_scale='YlOrRd')
    st.plotly_chart(fig_heat, use_container_width=True)

    # --- AUTOMATED BUSINESS INSIGHTS ---
    st.markdown("---")
    st.header("💡 Dynamic Business Insights")
    
    # Logic for insights
    top_region = reg_df.loc[reg_df['net_sales'].idxmax(), 'region']
    bottom_region = reg_df.loc[reg_df['net_sales'].idxmin(), 'region']
    high_return_cats = cat_df[cat_df['ret_rate'] > 10]['category'].tolist()
    underperforming_stores = store_df[store_df['ach_pct'] < 90]['store_name'].count()

    insight_text = f"""
    * **Market Leadership:** The **{top_region}** region is currently leading in total volume, while **{bottom_region}** requires strategic intervention.
    * **Operational Alerts:** There are **{underperforming_stores} stores** performing below 90% of their sales target.
    * **Quality Control:** High return rates (>10%) detected in: **{", ".join(high_return_cats) if high_return_cats else "None"}**.
    * **Inventory Risk:** A total of **{total_stockouts} stockout incidents** were recorded this period, primarily in the **{stock_df.loc[stock_df['stockout_flag'].idxmax(), 'category']}** category.
    """
    st.info(insight_text)

    # --- EXPORT FEATURE ---
    st.sidebar.markdown("---")
    st.sidebar.header("📤 Export Report")
    
    # CSV Export
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("Export Filtered Data (CSV)", data=csv, file_name="filtered_retail_data.csv", mime="text/csv")
    
    # Summary Export (Text)
    report_text = f"Retail Executive Summary\nTotal Sales: ${total_net_sales:,.2f}\nAvg Achievement: {target_achievement:.2f}%\n\nInsights:\n" + insight_text.replace('*', '-')
    st.sidebar.download_button("Download Insights (TXT)", data=report_text, file_name="executive_summary.txt")

else:
    # Display landing instructions
    st.warning("Waiting for data upload... Please provide the Retail Weekly Sales and Store Master files.")
    
    # Sample Data Format for User Reference
    with st.expander("View Expected Data Schema"):
        st.write("**retail_weekly_sales.xlsx columns:** store_id, week_start_date, gross_sales, net_sales, discount_amount, returns_amount, transactions, footfall, category, stockout_flag, sales_target")
        st.write("**store_master.xlsx columns:** store_id, store_name, region, city, store_format")
