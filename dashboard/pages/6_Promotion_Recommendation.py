import streamlit as st
import pandas as pd
import numpy as np
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
def load_recommendation_data():
    try:
        sales_df = pd.read_csv(PROCESSED_PATH / "sales_features.csv")
        products_df = pd.read_csv(RAW_PATH / "olist_products_dataset.csv")
        translation_df = pd.read_csv(RAW_PATH / "product_category_name_translation.csv")
        orders_df = pd.read_csv(RAW_PATH / "olist_orders_dataset.csv")
        segments_df = pd.read_csv(PROCESSED_PATH / "customer_segments.csv")
        campaigns_df = pd.read_csv(PROCESSED_PATH / "campaigns.csv")
        campaign_mapping = pd.read_csv(PROCESSED_PATH / "campaign_sales_mapping.csv")
        
        # Merge translation
        prod_trans = products_df.merge(translation_df, on="product_category_name", how="left")
        
        # Merge sales with categories, segments, and campaigns
        merged = sales_df.merge(orders_df[["order_id", "customer_id"]], on="order_id", how="inner")
        merged = merged.merge(segments_df[["customer_id", "customer_segment"]], on="customer_id", how="inner")
        merged = merged.merge(prod_trans[["product_id", "product_category_name_english"]], on="product_id", how="left")
        merged["product_category_name_english"] = merged["product_category_name_english"].fillna("unknown")
        
        # Translate segments inside database
        segment_mapping = {
            "Premium": "Big Spenders",
            "High Value": "Frequent Shoppers",
            "Regular": "Normal Shoppers",
            "Occasional": "Rare Shoppers"
        }
        merged["customer_segment"] = merged["customer_segment"].map(segment_mapping)
        
        # Merge campaign mapping & metadata for discount analysis
        merged = merged.merge(campaign_mapping, on="order_id", how="left")
        merged = merged.merge(campaigns_df[["campaign_id", "discount_pct"]], on="campaign_id", how="left")
        
        return merged
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df_rec = load_recommendation_data()

st.markdown('<div class="dashboard-header">Strategy Advisor & Future Calculator</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">Get simple recommendations for your shop and use the calculator to predict your future profits.</div>', unsafe_allow_html=True)

if df_rec.empty:
    st.warning("Failed to load recommendation data. Please check files.")
else:
    # Tab navigation
    tab_rec, tab_sim = st.tabs(["💡 What to Do (Strategy Advisor)", "🔮 Future Profit Calculator"])
    
    with tab_rec:
        st.subheader("📋 Item Types Recommendations")
        st.markdown(
            "We checked all your product types to see how much money they make. "
            "Here is what you should do for each type of product:"
        )
        
        # Calculate Category level metrics and benchmarks
        cat_summary = df_rec[df_rec["product_category_name_english"] != "unknown"].groupby("product_category_name_english").agg({
            "revenue": "sum",
            "gross_profit": "sum",
            "profit_margin_pct": "mean"
        }).reset_index()
        
        avg_revenue = cat_summary["revenue"].mean()
        avg_profit = cat_summary["gross_profit"].mean()
        
        recs = []
        for _, row in cat_summary.iterrows():
            cat = row["product_category_name_english"]
            rev = row["revenue"]
            profit = row["gross_profit"]
            margin = row["profit_margin_pct"]
            
            if rev > avg_revenue and profit > avg_profit:
                rec = "🚀 Pay for more ads (Very Profitable)"
                action = "This item sells in high volumes and keeps a good profit. Spend more on ads to get more customers!"
            elif rev > avg_revenue and profit <= avg_profit:
                rec = "⚠️ Give fewer discounts (Losing money on discounts)"
                action = "You sell a lot of these items, but make very little profit because you give too many discounts. Raise the price or stop discounts!"
            elif rev <= avg_revenue and profit <= avg_profit:
                rec = "🛑 Stop/Review this category (Not selling well)"
                action = "These items are not selling well and do not bring in profit. Review buying costs or stop selling them."
            else:
                rec = "🎯 Give small discounts to specific customers"
                action = "These items have high profit margins but low sales volume. Offer small discounts to Big Spenders to get them to buy more."
                
            recs.append([cat, rev, profit, margin, rec, action])
            
        rec_df = pd.DataFrame(recs, columns=["Product Type", "Sales (₹)", "Actual Profit (₹)", "Profit Share (%)", "What to Do", "Action steps"])
        
        # Display selection filter
        filter_rec = st.selectbox(
            "Filter by Action Type",
            ["All", "🚀 Pay for more ads (Very Profitable)", "⚠️ Give fewer discounts (Losing money on discounts)", "🎯 Give small discounts to specific customers", "🛑 Stop/Review this category (Not selling well)"]
        )
        
        display_rec_df = rec_df.copy()
        if filter_rec != "All":
            display_rec_df = display_rec_df[display_rec_df["What to Do"] == filter_rec]
            
        display_rec_df = display_rec_df.sort_values("Actual Profit (₹)", ascending=False)
        
        # Format table
        display_rec_df["Sales (₹)"] = display_rec_df["Sales (₹)"].map("₹{:,.2f}".format)
        display_rec_df["Actual Profit (₹)"] = display_rec_df["Actual Profit (₹)"].map("₹{:,.2f}".format)
        display_rec_df["Profit Share (%)"] = display_rec_df["Profit Share (%)"].map("{:.1f}%".format)
        
        st.dataframe(display_rec_df, use_container_width=True, hide_index=True)
        
    with tab_sim:
        st.subheader("🔮 Future Profit Calculator")
        st.markdown(
            "Play with the settings below. Choose a product type, select a customer type, "
            "set your ad cost, and select a discount to see how much profit you can make!"
        )
        
        # User input controls in two columns
        sim_col1, sim_col2 = st.columns(2)
        
        with sim_col1:
            categories_list = sorted(df_rec["product_category_name_english"].unique())
            if "unknown" in categories_list:
                categories_list.remove("unknown")
            sim_category = st.selectbox("Select Product Type to Test", categories_list)
            
            sim_segment = st.selectbox("Select Customer Type to Target", ["All Customers", "Big Spenders", "Frequent Shoppers", "Normal Shoppers", "Rare Shoppers"])
            
        with sim_col2:
            sim_budget = st.slider("Ad Budget (Money to spend on ads) (₹)", min_value=1000, max_value=30000, value=8000, step=1000)
            sim_discount = st.select_slider("Discount to offer (%)", options=[5, 10, 15, 20, 25], value=10)
            
        st.markdown("---")
        
        # Simulation Logic
        cat_mask = df_rec["product_category_name_english"] == sim_category
        if sim_segment != "All Customers":
            seg_mask = df_rec["customer_segment"] == sim_segment
            base_df = df_rec[cat_mask & seg_mask]
        else:
            base_df = df_rec[cat_mask]
            
        if base_df.empty:
            st.warning(f"No transactions found for this group. Simulating based on product type averages.")
            base_df = df_rec[cat_mask]
            
        base_units = len(base_df)
        avg_price = base_df["price"].mean()
        avg_cost = base_df["cost_price"].mean()
        
        disc_multipliers = {5: 1.0, 10: 1.25, 15: 1.15, 20: 0.95, 25: 1.40}
        vol_multiplier = disc_multipliers.get(sim_discount, 1.0)
        
        budget_multiplier = 1.0 + 0.25 * np.log1p((sim_budget - 1000) / 4000.0)
        
        sim_units = max(1, int(round(base_units * vol_multiplier * budget_multiplier * 0.05)))
        sim_unit_selling_price = avg_price * (1 - (sim_discount / 100))
        sim_unit_cost = avg_cost
        
        sim_revenue = sim_units * sim_unit_selling_price
        sim_cost = sim_units * sim_unit_cost
        sim_gross_profit = sim_revenue - sim_cost
        sim_margin = (sim_gross_profit / sim_revenue) * 100 if sim_revenue > 0 else 0
        sim_roi = ((sim_gross_profit - sim_budget) / sim_budget) * 100
        
        # Render Simulated Results
        st.subheader("📊 Estimated Results (Forecast)")
        
        res_col1, res_col2, res_col3, res_col4, res_col5 = st.columns(5)
        
        with res_col1:
            render_kpi_card("Estimated Items Sold", f"{sim_units:,}", "Number of sales", "neutral", "📦")
        with res_col2:
            render_kpi_card("Estimated Sales", f"₹{sim_revenue:,.2f}", "Total money made", "neutral", "💰")
        with res_col3:
            render_kpi_card("Estimated Profit", f"₹{sim_gross_profit:,.2f}", "Money kept after costs", "up" if sim_gross_profit > sim_budget else "down", "💎")
        with res_col4:
            render_kpi_card("Estimated Profit Share", f"{sim_margin:.1f}%", "Percentage we keep", "up" if sim_margin > 30 else "down", "📈")
        with res_col5:
            render_kpi_card("Estimated Ad Return", f"{sim_roi:.1f}%", "Profit made per rupee spent", "up" if sim_roi > 0 else "down", "🚀")
            
        st.markdown("---")
        
        # Dynamic simulation insights
        st.subheader("💡 Calculator Help & Insights")
        
        rec_directive = rec_df[rec_df["Product Type"] == sim_category].iloc[0]["What to Do"]
        
        sim_advice_col1, sim_advice_col2 = st.columns(2)
        
        with sim_advice_col1:
            render_panel(
                f"The strategic advice for this product type is: <b>{rec_directive}</b>. "
                "Try to match your calculator choices to this advice for best results.",
                type="info"
            )
            
            if sim_roi < 0:
                render_panel(
                    f"Your settings will lose you money! The ad return is negative (<b>{sim_roi:.1f}%</b>). "
                    f"This means the profit made (₹{sim_gross_profit:,.2f}) is LESS than the ad cost (₹{sim_budget:,}). "
                    "Try reducing the ad budget or choosing a smaller discount (like 5% or 10%) to protect your profits.",
                    type="warning"
                )
            elif sim_roi > 100:
                render_panel(
                    f"Excellent! This campaign makes a great ad return of <b>{sim_roi:.1f}%</b>. "
                    "You should definitely run this advertisement. Target Big Spenders to get even higher sales!",
                    type="success"
                )
            else:
                render_panel(
                    f"This campaign makes a moderate ad return of <b>{sim_roi:.1f}%</b>. "
                    "You can optimize this by testing a smaller discount rate to save margins.",
                    type="info"
                )
                
        with sim_advice_col2:
            # Draw a mini local line chart showing simulated profit at different discount rates
            sim_discounts = [5, 10, 15, 20, 25]
            sim_profits = []
            
            for d in sim_discounts:
                d_vol_mult = disc_multipliers.get(d, 1.0)
                d_units = max(1, int(round(base_units * d_vol_mult * budget_multiplier * 0.05)))
                d_selling = avg_price * (1 - (d / 100))
                d_profit = (d_units * d_selling) - (d_units * avg_cost)
                sim_profits.append(d_profit)
                
            fig_sim_curve = go.Figure()
            fig_sim_curve.add_trace(go.Scatter(
                x=[f"{d}%" for d in sim_discounts],
                y=sim_profits,
                mode='lines+markers',
                line=dict(color='#00ff88', width=3),
                marker=dict(size=6)
            ))
            fig_sim_curve = get_plotly_layout(
                fig_sim_curve,
                title_text=f"Estimated Profit Curve at different Discounts for '{sim_category.title()}'",
                x_title="Discount",
                y_title="Profit (₹)",
                show_legend=False
            )
            st.plotly_chart(fig_sim_curve, use_container_width=True)
