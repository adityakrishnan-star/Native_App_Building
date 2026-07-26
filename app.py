import streamlit as st
import pandas as pd

st.title("📊 Retail Sales Intelligence Dashboard")

# Upload widgets in sidebar
st.sidebar.header("📁 Data Upload Options")
sales_file = st.sidebar.file_uploader("Upload Weekly Sales (.xlsx)", type=['xlsx'])
store_file = st.sidebar.file_uploader("Upload Store Master (.xlsx)", type=['xlsx'])

# Load Sales Data (Upload or Fallback)
if sales_file is not None:
    df_sales = pd.read_excel(sales_file)
    st.sidebar.success("Sales Data Uploaded!")
else:
    try:
        df_sales = pd.read_excel('retail_weekly_sales.xlsx')
        st.sidebar.info("ℹ️ Loaded default sales data from repo.")
    except Exception as e:
        st.error("Please upload sales data.")

# Load Store Master Data (Upload or Fallback)
if store_file is not None:
    df_stores = pd.read_excel(store_file)
    st.sidebar.success("Store Master Uploaded!")
else:
    try:
        df_stores = pd.read_excel('store_master.xlsx')
        st.sidebar.info("ℹ️ Loaded default store master from repo.")
    except Exception as e:
        st.error("Please upload store master data.")
