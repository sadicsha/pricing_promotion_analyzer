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
def load_category_data():
    try:
        sales_df = pd.read_csv(PROCESSED_PATH / "sales_features.csv")
        products_df = pd.read_csv(RAW_PATH / "olist_products_dataset.csv")
        translation_df = pd.read_csv(RAW_PATH / "product_category_name_translation.csv")
        campaigns_df = pd.read_csv(PROCESSED_PATH / "campaigns.csv")
        campaign_mapping = pd.read_csv(PROCESSED_PATH / "campaign_sales_mapping.csv")
        
        # Merge products translation
        prod_translated = products_df.merge(translation_df, on="product_category_name", how="left")
        
        # Merge campaigns info
        sales_merged = sales_df.merge(campaign_mapping, on="order_id", how="left")
        sales_merged = sales_merged.merge(campaigns_df, on="campaign_id", how="left")
        
        # Merge products
        sales_merged = sales_merged.merge(
            prod_translated[["product_id", "product_category_name_english"]],
            on="product_id",
            how="left"
        )
        
        # Fill missing categories
        sales_merged["product_category_name_english"] = sales_merged["product_category_name_english"].fillna("unknown")
        
        return sales_merged
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df_cat = load_category_data()

st.markdown('<div class="dashboard-header">Product Types Performance</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">See which types of items sell the best and make the most profit.</div>', unsafe_allow_html=True)

if df_cat.empty:
    st.warning("Failed to load category data. Please verify files.")
else:
    # Tab layout
    tab_overview, tab_deep_dive = st.tabs(["📊 Main Performance Overview", "🔍 Inspect a Single Product Type"])
    
    with tab_overview:
        # Aggregated Category Stats
        cat_performance = df_cat.groupby("product_category_name_english").agg({
            "revenue": "sum",
            "gross_profit": "sum",
            "profit_margin_pct": "mean",
            "order_id": "count"
        }).reset_index()
        
        cat_performance.columns = ["category", "revenue", "profit", "margin_pct", "volume"]
        cat_performance = cat_performance[cat_performance["category"] != "unknown"]
        
        # Top 10 charts row
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            top_revenue = cat_performance.sort_values("revenue", ascending=False).head(10)
            fig_rev = px.bar(
                top_revenue,
                x="revenue",
                y="category",
                orientation='h',
                title="Top 10 Product Types by Sales (Money Made)",
                color="revenue",
                color_continuous_scale=px.colors.sequential.Blues,
                labels={"revenue": "Sales (₹)", "category": "Product Type"}
            )
            fig_rev.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
            fig_rev = get_plotly_layout(fig_rev, x_title="Sales (₹)")
            st.plotly_chart(fig_rev, use_container_width=True)
            
        with chart_col2:
            top_profit = cat_performance.sort_values("profit", ascending=False).head(10)
            fig_prof = px.bar(
                top_profit,
                x="profit",
                y="category",
                orientation='h',
                title="Top 10 Product Types by Actual Profit",
                color="profit",
                color_continuous_scale=px.colors.sequential.Viridis,
                labels={"profit": "Profit (₹)", "category": "Product Type"}
            )
            fig_prof.update_layout(yaxis={'categoryorder':'total ascending'}, coloraxis_showscale=False)
            fig_prof = get_plotly_layout(fig_prof, x_title="Profit (₹)")
            st.plotly_chart(fig_prof, use_container_width=True)
            
        st.markdown("---")
        
        # Scatter Plot - Margin vs Revenue
        st.subheader("🎯 Sales vs. Profit Share Map")
        st.markdown(
            "This map shows where each product type sits. "
            "Items on the **right** bring in the most sales money. "
            "Items at the **top** let us keep a higher percentage of the money as profit."
        )
        
        avg_rev_val = cat_performance["revenue"].median()
        avg_margin_val = cat_performance["margin_pct"].mean()
        
        fig_scatter = px.scatter(
            cat_performance,
            x="revenue",
            y="margin_pct",
            size="volume",
            color="profit",
            hover_name="category",
            text="category",
            color_continuous_scale=px.colors.sequential.Plasma,
            labels={"revenue": "Sales (₹)", "margin_pct": "Average Profit Share (%)", "profit": "Actual Profit (₹)"}
        )
        
        fig_scatter.add_vline(x=avg_rev_val, line_dash="dash", line_color="rgba(255,255,255,0.4)", annotation_text="Middle Sales Line")
        fig_scatter.add_hline(y=avg_margin_val, line_dash="dash", line_color="rgba(255,255,255,0.4)", annotation_text="Middle Profit Share Line")
        
        fig_scatter.update_traces(textposition='top center')
        fig_scatter = get_plotly_layout(
            fig_scatter, 
            x_title="Sales (₹)", 
            y_title="Profit Share (%)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with tab_deep_dive:
        st.subheader("🔍 Inspect a Single Product Type")
        
        # Category list selection
        categories_list = sorted(df_cat["product_category_name_english"].unique())
        if "unknown" in categories_list:
            categories_list.remove("unknown")
            
        selected_cat = st.selectbox("Select a Product Type to Check", categories_list)
        
        # Filtered data
        cat_df = df_cat[df_cat["product_category_name_english"] == selected_cat]
        
        # Calculate filtered metrics
        c_rev = cat_df["revenue"].sum()
        c_prof = cat_df["gross_profit"].sum()
        c_margin = cat_df["profit_margin_pct"].mean()
        c_orders = cat_df["order_id"].count()
        
        # Columns
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            render_kpi_card("Sales (Money Made)", f"₹{c_rev:,.2f}", icon="💰")
        with col_m2:
            render_kpi_card("Actual Profit (Money kept)", f"₹{c_prof:,.2f}", icon="💎")
        with col_m3:
            render_kpi_card("Profit Share %", f"{c_margin:.1f}%", icon="📈")
        with col_m4:
            render_kpi_card("Total Items Sold", f"{c_orders:,}", icon="📦")
            
        st.markdown("---")
        
        deep_col1, deep_col2 = st.columns([3, 2])
        
        with deep_col1:
            st.markdown(f"#### 🏷️ Sales for **{selected_cat.title()}** under different Advertisements")
            
            # Group by campaigns
            camp_dist = cat_df.groupby(["campaign_name", "discount_pct"]).agg({
                "revenue": "sum",
                "gross_profit": "sum",
                "order_id": "count"
            }).reset_index()
            
            fig_camp_dist = px.bar(
                camp_dist,
                x="campaign_name",
                y="revenue",
                color="gross_profit",
                text="discount_pct",
                labels={"revenue": "Sales (₹)", "campaign_name": "Ad Name", "gross_profit": "Profit (₹)"},
                title="Sales and Profit by Ad Campaign (Number on bars shows Discount %)"
            )
            fig_camp_dist = get_plotly_layout(fig_camp_dist, x_title="Ad Campaign", y_title="Sales (₹)")
            st.plotly_chart(fig_camp_dist, use_container_width=True)
            
        with deep_col2:
            st.markdown(f"#### 🏆 Top Selling Items in **{selected_cat.title()}**")
            
            top_prod_cat = cat_df.groupby("product_id").agg({
                "revenue": "sum",
                "gross_profit": "sum",
                "profit_margin_pct": "mean"
            }).reset_index()
            
            top_prod_cat = top_prod_cat.sort_values("gross_profit", ascending=False).head(5)
            top_prod_cat.columns = ["Product ID", "Sales (₹)", "Profit (₹)", "Profit Share (%)"]
            
            top_prod_cat["Sales (₹)"] = top_prod_cat["Sales (₹)"].map("₹{:,.2f}".format)
            top_prod_cat["Profit (₹)"] = top_prod_cat["Profit (₹)"].map("₹{:,.2f}".format)
            top_prod_cat["Profit Share (%)"] = top_prod_cat["Profit Share (%)"].map("{:.1f}%".format)
            
            st.dataframe(top_prod_cat, use_container_width=True, hide_index=True)
            
            # Recommendation panels
            st.markdown("#### 🎯 Simple Shop Tip")
            if c_margin < 20:
                render_panel(
                    f"The profit share from {selected_cat} is very low ({c_margin:.1f}%). "
                    "You should stop giving discounts on these items because they are costing you too much money.",
                    type="warning"
                )
            elif c_margin > 40:
                render_panel(
                    f"Excellent profit share ({c_margin:.1f}%) in {selected_cat}. "
                    "This is a great place to offer a small discount because you keep a lot of money anyway. A discount will attract more shoppers!",
                    type="success"
                )
            else:
                render_panel(
                    f"Profit share is average ({c_margin:.1f}%) in {selected_cat}. "
                    "Keep prices where they are. Do not raise or lower them.",
                    type="info"
                )
