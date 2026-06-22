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
def load_campaign_data():
    try:
        sales_df = pd.read_csv(PROCESSED_PATH / "sales_features.csv")
        campaign_mapping = pd.read_csv(PROCESSED_PATH / "campaign_sales_mapping.csv")
        campaigns_df = pd.read_csv(PROCESSED_PATH / "campaigns.csv")
        
        # Merge sales with mapping
        merged = sales_df.merge(campaign_mapping, on="order_id", how="left")
        
        # Campaign performance summary
        camp_perf = merged.groupby("campaign_id").agg({
            "revenue": "sum",
            "gross_profit": "sum",
            "order_id": "nunique"
        }).reset_index()
        
        # Merge with campaigns metadata
        camp_perf = camp_perf.merge(campaigns_df, on="campaign_id", how="left")
        
        # Calculate ROI %
        camp_perf["roi_pct"] = ((camp_perf["gross_profit"] - camp_perf["budget"]) / camp_perf["budget"]) * 100
        
        return camp_perf.sort_values("roi_pct", ascending=False), merged
    except Exception as e:
        st.error(f"Error loading campaign data: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_camp, df_merged = load_campaign_data()

st.markdown('<div class="dashboard-header">Ad & Campaign Performance</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">See which sales and advertisements made the most profit and were worth the money.</div>', unsafe_allow_html=True)

if df_camp.empty:
    st.warning("Failed to load campaign data. Please check files.")
else:
    # Top Campaign KPIs
    best_campaign = df_camp.iloc[0]
    worst_campaign = df_camp.iloc[-1]
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        render_kpi_card(
            "Best Advertisement",
            f"{best_campaign['campaign_name']}",
            f"{best_campaign['roi_pct']:.1f}% Worth (ROI)",
            "up",
            "🏆"
        )
    with col_c2:
        render_kpi_card(
            "Biggest Profit Maker",
            f"{df_camp.loc[df_camp['gross_profit'].idxmax()]['campaign_name']}",
            f"₹{df_camp['gross_profit'].max()/1e6:.2f}M Profit",
            "up",
            "💎"
        )
    with col_c3:
        render_kpi_card(
            "Total Money Spent on Ads",
            f"₹{df_camp['budget'].sum():,}",
            "Across 5 campaign types",
            "neutral",
            "💰"
        )
        
    st.markdown("---")
    
    # Table & Chart Row
    table_col, chart_col = st.columns([4, 3])
    
    with table_col:
        st.subheader("📊 Advertisement Performance Summary")
        
        # Format table for user view
        table_df = df_camp[[
            "campaign_name", "channel", "discount_pct", "budget", "revenue", "gross_profit", "roi_pct"
        ]].copy()
        
        table_df.columns = ["Ad Sale Name", "Ad Type", "Discount % Given", "Ad Cost (₹)", "Sales (₹)", "Actual Profit (₹)", "Worth / ROI %"]
        table_df["Ad Cost (₹)"] = table_df["Ad Cost (₹)"].map("₹{:,.0f}".format)
        table_df["Sales (₹)"] = table_df["Sales (₹)"].map("₹{:,.2f}".format)
        table_df["Actual Profit (₹)"] = table_df["Actual Profit (₹)"].map("₹{:,.2f}".format)
        table_df["Worth / ROI %"] = table_df["Worth / ROI %"].map("{:.1f}%".format)
        
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        
    with chart_col:
        # Budget vs Profit bar chart
        fig_bars = go.Figure()
        fig_bars.add_trace(go.Bar(
            x=df_camp["campaign_name"],
            y=df_camp["budget"],
            name="Ad Cost (₹)",
            marker_color="#ff5e62"
        ))
        fig_bars.add_trace(go.Bar(
            x=df_camp["campaign_name"],
            y=df_camp["gross_profit"],
            name="Actual Profit Made (₹)",
            marker_color="#00ff88"
        ))
        
        fig_bars = get_plotly_layout(
            fig_bars,
            title_text="Ad Cost vs. Actual Profit Made (Green should be higher than Red!)",
            x_title="Ad Campaign",
            y_title="Amount (₹)"
        )
        st.plotly_chart(fig_bars, use_container_width=True)
        
    st.markdown("---")
    
    # Channel Analysis Row
    chan_col1, chan_col2 = st.columns([1, 1])
    
    with chan_col1:
        # ROI by Channel
        fig_chan_roi = px.bar(
            df_camp,
            x="channel",
            y="roi_pct",
            color="roi_pct",
            color_continuous_scale=px.colors.sequential.Teal,
            title="Ad Worth (ROI %) by Advertisement Type",
            labels={"roi_pct": "Worth / ROI (%)", "channel": "Ad Type"}
        )
        fig_chan_roi.update_layout(coloraxis_showscale=False)
        fig_chan_roi = get_plotly_layout(fig_chan_roi, x_title="Ad Type", y_title="Worth / ROI (%)")
        st.plotly_chart(fig_chan_roi, use_container_width=True)
        
    with chan_col2:
        st.subheader("💡 Simple Advertising Tips")
        
        render_panel(
            f"You should repeat the advertisement <b>'{best_campaign['campaign_name']}'</b> "
            f"({best_campaign['channel']} ad, with a {best_campaign['discount_pct']}% discount). "
            f"It was the most worth the money, returning <b>{best_campaign['roi_pct']:.1f}%</b>. "
            f"It made a profit of ₹{best_campaign['gross_profit']:,.2f} while only costing ₹{best_campaign['budget']:,.2f} to run!",
            type="success"
        )
        
        if worst_campaign["roi_pct"] < 0:
            render_panel(
                f"The advertisement <b>'{worst_campaign['campaign_name']}'</b> ({worst_campaign['channel']} ad) "
                f"lost money, returning a negative <b>{worst_campaign['roi_pct']:.1f}%</b>. "
                f"You should stop paying for this advertisement because it costs more than the profit it brings in.",
                type="warning"
            )
        else:
            render_panel(
                f"All advertisements brought in positive profits. The lowest performing one is <b>'{worst_campaign['campaign_name']}'</b> "
                f"which returned <b>{worst_campaign['roi_pct']:.1f}%</b>. Monitor this one closely.",
                type="info"
            )
            
        render_panel(
            "<b>General Tip:</b> Ads with huge discounts (like Flash Sale at 25%) often lose money. "
            "Smaller discounts (like 5% or 10%) combined with cheap advertisements (like SMS or Email) "
            "are the best way to keep your profits high.",
            type="info"
        )
