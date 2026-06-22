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
PROCESSED_PATH = Path("data/processed")

# Load data helper
@st.cache_data
def load_pricing_data():
    try:
        sales_df = pd.read_csv(PROCESSED_PATH / "sales_features.csv")
        campaign_mapping = pd.read_csv(PROCESSED_PATH / "campaign_sales_mapping.csv")
        campaigns_df = pd.read_csv(PROCESSED_PATH / "campaigns.csv")
        
        # Merge campaign mapping & metadata
        merged = sales_df.merge(campaign_mapping, on="order_id", how="left")
        merged = merged.merge(campaigns_df[["campaign_id", "discount_pct", "campaign_name"]], on="campaign_id", how="left")
        
        # Aggregate by discount percentage
        disc_perf = merged.groupby("discount_pct").agg({
            "revenue": "sum",
            "gross_profit": "sum",
            "order_id": "count"
        }).reset_index()
        
        disc_perf.columns = ["discount_pct", "revenue", "profit", "units_sold"]
        disc_perf["margin_pct"] = (disc_perf["profit"] / disc_perf["revenue"]) * 100
        
        return disc_perf.sort_values("discount_pct"), merged
    except Exception as e:
        st.error(f"Error loading pricing data: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_disc, df_merged = load_pricing_data()

st.markdown('<div class="dashboard-header">Discount & Price Helper</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">Find the perfect discount percentage to make the most profit without giving away too much money.</div>', unsafe_allow_html=True)

if df_disc.empty:
    st.warning("Failed to load pricing data. Please check files.")
else:
    # Calculations
    best_discount_row = df_disc.sort_values("profit", ascending=False).iloc[0]
    best_discount_pct = best_discount_row["discount_pct"]
    best_discount_profit = best_discount_row["profit"]
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        render_kpi_card(
            "Best Discount Percentage",
            f"{best_discount_pct}% Discount",
            "Makes the most actual profit",
            "up",
            "🎯"
        )
    with col_p2:
        render_kpi_card(
            "Highest Profit Point",
            f"₹{best_discount_profit/1e6:.2f}M",
            f"Generated at {best_discount_pct}% discount",
            "up",
            "💎"
        )
    with col_p3:
        render_kpi_card(
            "Best Profit Share %",
            f"{df_disc['margin_pct'].max():.1f}%",
            f"Kept at {df_disc.loc[df_disc['margin_pct'].idxmax()]['discount_pct']}% discount",
            "up",
            "📈"
        )
        
    st.markdown("---")
    
    # Graphs Row 1
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        # Discount vs Revenue & Profit
        fig_revenue_profit = go.Figure()
        fig_revenue_profit.add_trace(go.Bar(
            x=df_disc["discount_pct"].astype(str) + "%",
            y=df_disc["revenue"],
            name="Sales (Money Made)",
            marker_color="#00c6ff"
        ))
        fig_revenue_profit.add_trace(go.Bar(
            x=df_disc["discount_pct"].astype(str) + "%",
            y=df_disc["profit"],
            name="Actual Profit (Money kept)",
            marker_color="#00ff88"
        ))
        
        fig_revenue_profit = get_plotly_layout(
            fig_revenue_profit,
            title_text="Sales and Actual Profit by Discount Rate (Blue is Sales, Green is Profit)",
            x_title="Discount Given",
            y_title="Amount (₹)"
        )
        st.plotly_chart(fig_revenue_profit, use_container_width=True)
        
    with g_col2:
        # Margin % vs Discount % Line
        fig_margin_line = go.Figure()
        fig_margin_line.add_trace(go.Scatter(
            x=df_disc["discount_pct"].astype(str) + "%",
            y=df_disc["margin_pct"],
            mode='lines+markers',
            name='Profit Share %',
            line=dict(color='#ff9f43', width=4),
            marker=dict(size=8, symbol="diamond")
        ))
        
        fig_margin_line = get_plotly_layout(
            fig_margin_line,
            title_text="How much Profit Share we lose when we give bigger discounts",
            x_title="Discount Given",
            y_title="Profit Share %"
        )
        st.plotly_chart(fig_margin_line, use_container_width=True)
        
    st.markdown("---")
    
    # Graphs Row 2
    elasticity_col, insights_col = st.columns([3, 2])
    
    with elasticity_col:
        st.subheader("📦 How many items we sell when we lower the price")
        st.markdown(
            "See how the number of items sold increases when we offer bigger discounts. "
            "Giving a discount must sell *many* more items to make up for the profit lost on each item."
        )
        
        fig_vol = px.line(
            df_disc,
            x="discount_pct",
            y="units_sold",
            text="units_sold",
            markers=True,
            labels={"discount_pct": "Discount Rate (%)", "units_sold": "Items Sold"}
        )
        fig_vol.update_traces(
            line=dict(color="#5f27cd", width=3),
            marker=dict(size=8),
            textposition="top center"
        )
        fig_vol = get_plotly_layout(fig_vol, x_title="Discount Rate (%)", y_title="Items Sold")
        st.plotly_chart(fig_vol, use_container_width=True)
        
    with insights_col:
        st.subheader("💡 Simple Discount Tips")
        
        render_panel(
            f"<b>The Profit Sweet Spot:</b> Offering a <b>{best_discount_pct}%</b> discount "
            f"gives you the highest actual profit of <b>₹{best_discount_profit:,.2f}</b>. "
            "This is the perfect balance where you sell more items without losing too much profit per item.",
            type="success"
        )
        
        # Analyze elasticity
        v_5 = df_disc[df_disc["discount_pct"] == 5].iloc[0]["units_sold"]
        v_25 = df_disc[df_disc["discount_pct"] == 25].iloc[0]["units_sold"]
        volume_increase = ((v_25 - v_5) / v_5) * 100
        
        render_panel(
            f"<b>Quantity Sold:</b> Increasing your discount from 5% to 25% "
            f"increased the items sold from {v_5:,} to {v_25:,} (a change of <b>{volume_increase:+.1f}%</b>). "
            "But look at the charts above: our profit at 25% is LOWER than our profit at 5%. "
            "This means giving a 25% discount **loses you money overall**!",
            type="warning"
        )
        
        render_panel(
            "<b>Price Directive:</b> You should cap your normal discount campaigns at **10%**. "
            "Only give a 20% or 25% discount if you have old, slow-moving items that you want to clear out of the warehouse.",
            type="info"
        )
