import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add project root to path to allow styles import
sys.path.append(str(Path(__file__).parent.parent))
from styles import inject_custom_css, render_kpi_card, render_panel, get_plotly_layout

# Inject styling
inject_custom_css()

# Data Paths
RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

# Load data helper
@st.cache_data
def load_customer_data():
    try:
        sales_df = pd.read_csv(PROCESSED_PATH / "sales_features.csv")
        orders_df = pd.read_csv(RAW_PATH / "olist_orders_dataset.csv")
        segments_df = pd.read_csv(PROCESSED_PATH / "customer_segments.csv")
        products_df = pd.read_csv(RAW_PATH / "olist_products_dataset.csv")
        translation_df = pd.read_csv(RAW_PATH / "product_category_name_translation.csv")
        
        # Merge orders -> customer
        merged = sales_df.merge(orders_df[["order_id", "customer_id"]], on="order_id", how="inner")
        
        # Merge segments
        merged = merged.merge(segments_df[["customer_id", "customer_segment"]], on="customer_id", how="inner")
        
        # Translate segment names to simple terms
        segment_mapping = {
            "Premium": "Big Spenders",
            "High Value": "Frequent Shoppers",
            "Regular": "Normal Shoppers",
            "Occasional": "Rare Shoppers"
        }
        merged["customer_segment"] = merged["customer_segment"].map(segment_mapping)
        
        # Merge product category translations
        prod_trans = products_df.merge(translation_df, on="product_category_name", how="left")
        merged = merged.merge(prod_trans[["product_id", "product_category_name_english"]], on="product_id", how="left")
        merged["product_category_name_english"] = merged["product_category_name_english"].fillna("unknown")
        
        return merged
    except Exception as e:
        st.error(f"Error loading customer data: {e}")
        return pd.DataFrame()

df_cust = load_customer_data()

st.markdown('<div class="dashboard-header">Customer Types Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">Understand who spends the most money in your shop and who is worth marketing to.</div>', unsafe_allow_html=True)



if df_cust.empty:
    st.warning("Failed to load customer segments. Please check files.")
else:
    # Segment level summary
    segment_summary = df_cust.groupby("customer_segment").agg({
        "revenue": "sum",
        "gross_profit": "sum",
        "profit_margin_pct": "mean",
        "order_id": "nunique"
    }).reset_index()
    
    segment_summary.columns = ["segment", "revenue", "profit", "avg_margin", "total_orders"]
    segment_summary["aov"] = segment_summary["revenue"] / segment_summary["total_orders"]
    
    # Overview metrics across segments
    st.subheader("👥 Sales by Customer Type")
    
    cols = st.columns(4)
    seg_names = ["Big Spenders", "Frequent Shoppers", "Normal Shoppers", "Rare Shoppers"]
    
    for i, name in enumerate(seg_names):
        with cols[i]:
            seg_row = segment_summary[segment_summary["segment"] == name]
            if not seg_row.empty:
                s_rev = seg_row.iloc[0]["revenue"]
                s_profit = seg_row.iloc[0]["profit"]
                s_margin = seg_row.iloc[0]["avg_margin"]
                s_orders = seg_row.iloc[0]["total_orders"]
                
                st.markdown(f"""
                <div style="background: rgba(25, 30, 48, 0.45); border: 1px solid rgba(255,255,255,0.05); border-radius:12px; padding:15px; text-align:center;">
                    <h4 style="margin:0 0 10px 0; color:#00d4ff;">{name}</h4>
                    <p style="font-size:24px; font-weight:700; margin:5px 0; color:#fff;">₹{s_rev/1e6:.2f}M</p>
                    <p style="font-size:12px; color:#a0aec0; margin:0;">Profit: <b>₹{s_profit/1e6:.2f}M</b></p>
                    <p style="font-size:12px; color:#a0aec0; margin:0;">Profit Share: <b>{s_margin:.1f}%</b></p>
                    <p style="font-size:12px; color:#a0aec0; margin:0;">Total Orders: <b>{s_orders:,}</b></p>
                </div>
                """, unsafe_allow_html=True)
                
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Pie chart for segment revenue composition
        fig_revenue_pie = px.pie(
            segment_summary,
            names="segment",
            values="revenue",
            title="Where Our Sales Money Comes From (By Customer Type)",
            color="segment",
            color_discrete_map={"Big Spenders": "#ff9f43", "Frequent Shoppers": "#00d2d3", "Normal Shoppers": "#54a0ff", "Rare Shoppers": "#5f27cd"}
        )
        fig_revenue_pie = get_plotly_layout(fig_revenue_pie, show_legend=True)
        st.plotly_chart(fig_revenue_pie, use_container_width=True)
        
    with chart_col2:
        # AOV Bar Chart
        fig_aov = px.bar(
            segment_summary,
            x="segment",
            y="aov",
            title="Average Bill Size by Customer Type",
            color="segment",
            color_discrete_map={"Big Spenders": "#ff9f43", "Frequent Shoppers": "#00d2d3", "Normal Shoppers": "#54a0ff", "Rare Shoppers": "#5f27cd"},
            labels={"aov": "Average Spend (₹)", "segment": "Customer Type"}
        )
        fig_aov = get_plotly_layout(fig_aov, x_title="Customer Type", y_title="Average Spend (₹)", show_legend=False)
        st.plotly_chart(fig_aov, use_container_width=True)
        
    st.markdown("---")
    
    # Profile & Insights
    st.subheader("🔍 What different customers buy")
    
    selected_seg = st.selectbox("Select Customer Type to Check", seg_names)
    
    seg_details = df_cust[df_cust["customer_segment"] == selected_seg]
    
    detail_col1, detail_col2 = st.columns([3, 2])
    
    with detail_col1:
        st.markdown(f"#### 🛍️ Top 5 Categories purchased by **{selected_seg}**")
        fav_cats = seg_details.groupby("product_category_name_english").agg({
            "revenue": "sum",
            "gross_profit": "sum",
            "order_id": "count"
        }).reset_index().sort_values("revenue", ascending=False).head(5)
        
        fav_cats.columns = ["Product Type", "Sales (₹)", "Actual Profit (₹)", "Total Items Bought"]
        fav_cats["Sales (₹)"] = fav_cats["Sales (₹)"].map("₹{:,.2f}".format)
        fav_cats["Actual Profit (₹)"] = fav_cats["Actual Profit (₹)"].map("₹{:,.2f}".format)
        
        st.dataframe(fav_cats, use_container_width=True, hide_index=True)
        
    with detail_col2:
        st.markdown("#### 🎯 Simple Shop Tip")
        
        if selected_seg == "Big Spenders":
            render_panel(
                "<b>Big Spenders:</b> These customers spend the most money on each bill. "
                "They do not care about small discounts. Do not waste money giving them discounts! "
                "Instead, offer them fast delivery or a gift wrapper to make them happy.",
                type="success"
            )
        elif selected_seg == "Frequent Shoppers":
            render_panel(
                "<b>Frequent Shoppers:</b> They buy from you very often. "
                "They love deals like 'Buy for ₹200, Get ₹20 off'. Use these deals to make them buy "
                "even more items during their next visit.",
                type="success"
            )
        elif selected_seg == "Normal Shoppers":
            render_panel(
                "<b>Normal Shoppers:</b> This is your biggest group of customers. They bring in the most money overall. "
                "They love 10% to 15% discount sales on weekends. Use weekend sales to keep them coming back.",
                type="info"
            )
        elif selected_seg == "Rare Shoppers":
            render_panel(
                "<b>Rare Shoppers:</b> They rarely buy from you. "
                "To get them to buy, you must offer a large discount (like 20% off clearance items). "
                "This gets rid of old stock and brings them back into the shop.",
                type="warning"
            )
