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
def load_executive_data():
    try:
        sales_df = pd.read_csv(PROCESSED_PATH / "sales_features.csv")
        orders_df = pd.read_csv(RAW_PATH / "olist_orders_dataset.csv")
        products_df = pd.read_csv(RAW_PATH / "olist_products_dataset.csv")
        translation_df = pd.read_csv(RAW_PATH / "product_category_name_translation.csv")
        
        # Merge orders temporal data
        orders_minimal = orders_df[["order_id", "order_purchase_timestamp"]]
        sales_merged = sales_df.merge(orders_minimal, on="order_id", how="inner")
        sales_merged["order_purchase_timestamp"] = pd.to_datetime(sales_merged["order_purchase_timestamp"])
        sales_merged["month"] = sales_merged["order_purchase_timestamp"].dt.to_period("M").astype(str)
        
        # Product translation mapping
        prod_translated = products_df.merge(translation_df, on="product_category_name", how="left")
        prod_minimal = prod_translated[["product_id", "product_category_name_english"]]
        sales_merged = sales_merged.merge(prod_minimal, on="product_id", how="left")
        
        return sales_merged
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df_sales = load_executive_data()

st.markdown('<div class="dashboard-header">Overall Shop Performance</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">See how much money the shop made and how much profit is left over after buying the items.</div>', unsafe_allow_html=True)

if df_sales.empty:
    st.warning("Failed to load sales data. Please check database files.")
else:
    # Calculations
    total_rev = df_sales["revenue"].sum()
    total_profit = df_sales["gross_profit"].sum()
    avg_margin = df_sales["profit_margin_pct"].mean()
    total_orders = df_sales["order_id"].nunique()
    aov = total_rev / total_orders if total_orders > 0 else 0
    total_cost = df_sales["cost_price"].sum()
    
    # KPI metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card("Total Sales (Money Made)", f"₹{total_rev/1e6:.2f}M", "Total money paid by customers", "neutral", "💰")
    with col2:
        render_kpi_card("Actual Profit (Money Left)", f"₹{total_profit/1e6:.2f}M", "Money left after paying for items", "up", "💎")
    with col3:
        render_kpi_card("Profit Share %", f"{avg_margin:.1f}%", "Percentage of sales we keep", "up", "📈")
    with col4:
        render_kpi_card("Total Orders", f"{total_orders:,}", "Total purchases made", "neutral", "🛒")
    with col5:
        render_kpi_card("Avg Customer Spend", f"₹{aov:.2f}", "Average spend per bill", "neutral", "🏷️")
        
    st.markdown("---")
    
    # Charts Section
    chart_col1, chart_col2 = st.columns([2, 1])
    
    with chart_col1:
        # Time-series trend lines
        monthly_stats = df_sales.groupby("month").agg({
            "revenue": "sum",
            "gross_profit": "sum"
        }).reset_index().sort_values("month")
        
        monthly_stats = monthly_stats[monthly_stats["month"] >= "2017-01"]
        monthly_stats = monthly_stats[monthly_stats["month"] <= "2018-08"]
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=monthly_stats["month"], 
            y=monthly_stats["revenue"],
            mode='lines+markers',
            name='Total Sales (Money Made)',
            line=dict(color='#00c6ff', width=3),
            marker=dict(size=6)
        ))
        fig_trend.add_trace(go.Scatter(
            x=monthly_stats["month"], 
            y=monthly_stats["gross_profit"],
            mode='lines+markers',
            name='Actual Profit (Money Left)',
            line=dict(color='#00ff88', width=3),
            marker=dict(size=6)
        ))
        
        fig_trend = get_plotly_layout(
            fig_trend, 
            title_text="Sales and Profit Month by Month (Blue is Sales, Green is Profit)",
            x_title="Timeline (Months)",
            y_title="Amount (₹)"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with chart_col2:
        # Cost vs profit donut chart
        fig_cost_profit = go.Figure(data=[go.Pie(
            labels=['Item Cost (Buying price)', 'Actual Profit (Money kept)'],
            values=[total_cost, total_profit],
            hole=.4,
            marker_colors=['#ff5e62', '#00ff88']
        )])
        fig_cost_profit = get_plotly_layout(
            fig_cost_profit,
            title_text="Where the Sales Money Went",
            show_legend=True
        )
        st.plotly_chart(fig_cost_profit, use_container_width=True)
        
    st.markdown("---")
    
    # Bottom Row: Top products & Insights
    table_col, insight_col = st.columns([3, 2])
    
    with table_col:
        st.subheader("🏆 Top 10 Best Selling Items (Most Profit)")
        
        # Find top 10 products
        top_products = df_sales.groupby(["product_id", "product_category_name_english"]).agg({
            "revenue": "sum",
            "gross_profit": "sum",
            "profit_margin_pct": "mean"
        }).reset_index()
        
        top_products = top_products.sort_values("gross_profit", ascending=False).head(10)
        
        # Format columns
        top_products.columns = ["Product ID", "Product Type", "Total Sales (₹)", "Actual Profit (₹)", "Profit Share (%)"]
        top_products["Total Sales (₹)"] = top_products["Total Sales (₹)"].map("₹{:,.2f}".format)
        top_products["Actual Profit (₹)"] = top_products["Actual Profit (₹)"].map("₹{:,.2f}".format)
        top_products["Profit Share (%)"] = top_products["Profit Share (%)"].map("{:.1f}%".format)
        
        st.dataframe(top_products, use_container_width=True, hide_index=True)
        
    with insight_col:
        st.subheader("💡 Simple Shop Tips")
        
        # Determine highest profit category
        top_cat = df_sales.groupby("product_category_name_english")["gross_profit"].sum().idxmax()
        top_cat_profit = df_sales.groupby("product_category_name_english")["gross_profit"].sum().max()
        
        render_panel(
            f"The types of items that make the most profit are <b>{top_cat}</b>. "
            f"They made a total profit of <b>₹{top_cat_profit:,.2f}</b>. "
            f"You should put more of these items in your shop and show them on the front shelf!",
            type="success"
        )
        
        # Cost check
        margin_pct = (total_profit / total_rev) * 100
        if margin_pct < 40:
            render_panel(
                f"We keep <b>{margin_pct:.1f}%</b> of our sales money. This is a bit low. "
                f"You should give fewer discounts or sell items at a slightly higher price to keep more profit.",
                type="warning"
            )
        else:
            render_panel(
                f"We keep <b>{margin_pct:.1f}%</b> of our sales money. This is very good! "
                f"This means you can afford to run more ads to get new customers.",
                type="info"
            )
            
        render_panel(
            f"On average, each customer spends <b>₹{aov:.2f}</b> when they buy from you. "
            f"If you sell items as a bundle (for example, buy 2 together for a small discount), "
            f"you can get them to spend more money!",
            type="info"
        )
