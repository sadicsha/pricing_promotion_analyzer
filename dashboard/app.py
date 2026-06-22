import streamlit as st
import pandas as pd
from pathlib import Path
from styles import inject_custom_css, render_kpi_card, render_panel

# Set page config once globally
st.set_page_config(
    page_title="Shop Profit & Advertising Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS styles globally
inject_custom_css()

# Sidebar Configuration (renders on all pages!)
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/combo-chart.png", width=80)
    
    # Store settings in session state
    st.session_state["llm_provider"] = "Demo Mode (Works Offline)"
    st.session_state["llm_api_key"] = ""
    
    st.markdown("### 💡 Quick Help")
    st.info(
        "Use the sidebar links to switch pages. "
        "Use the **AI Shop Assistant** page to ask questions using simple text."
    )

# Define the Welcome page contents
def show_welcome():
    # Data Paths
    PROCESSED_PATH = Path("data/processed")

    # Load global data helper
    try:
        sales_df = pd.read_csv(PROCESSED_PATH / "sales_features.csv")
        total_revenue = sales_df["revenue"].sum()
        total_profit = sales_df["gross_profit"].sum()
        avg_margin = sales_df["profit_margin_pct"].mean()
        total_orders = sales_df["order_id"].nunique()
    except Exception as e:
        total_revenue, total_profit, avg_margin, total_orders = 0, 0, 0, 0

    # Main Title Area
    st.markdown('<div class="dashboard-header">Shop Profit & Advertising Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Find the best discounts and advertisements to make your shop more profitable</div>', unsafe_allow_html=True)


    # Overview text
    st.markdown("""
    Many store owners give big discounts or pay for advertisements, but they do not know if they are actually making money or losing it. 
    Sometimes, giving a discount makes you sell more items, but you make less profit because you are giving away too much money.

    This tool reads your shop's database to show you exactly how much profit you keep, which products make the most money, 
    and what discounts you should offer to get the highest profit.
    """)

    st.markdown("---")

    # Quick Metrics Row
    st.subheader("📊 Global Shop Performance (Summary)")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_kpi_card(
            title="Total Sales (Money Made)",
            value=f"₹{total_revenue/1e6:.2f}M",
            change="All customer spend",
            change_direction="neutral",
            icon="💰"
        )

    with col2:
        render_kpi_card(
            title="Actual Profit (Money Left)",
            value=f"₹{total_profit/1e6:.2f}M",
            change="After subtracting item costs",
            change_direction="up",
            icon="💎"
        )

    with col3:
        render_kpi_card(
            title="Profit Share Percentage",
            value=f"{avg_margin:.1f}%",
            change="Rupees we keep from every sale",
            change_direction="up",
            icon="📈"
        )

    with col4:
        render_kpi_card(
            title="Total Customer Orders",
            value=f"{total_orders:,}",
            change="Total sales transactions",
            change_direction="neutral",
            icon="🛒"
        )

    st.markdown("---")

    # Workflow & Pipeline
    st.subheader("⚙️ How the Tool Works")

    col_flow1, col_flow2, col_flow3 = st.columns(3)

    with col_flow1:
        st.markdown("""
        #### 📥 1. Read Shop Data
        - We read your shop's order list, product list, and category lists.
        - We match the items you sold with their original buying costs.
        """)
        
    with col_flow2:
        st.markdown("""
        #### 🧠 2. Calculate Profit & Sales
        - We calculate the profit for each item: `Sale Price - Original Item Cost = Actual Profit`.
        - We see which types of customers buy the most.
        - We see which ads made more money than they cost.
        """)

    with col_flow3:
        st.markdown("""
        #### 🚀 3. Help You Decide
        - We provide a **Future Profit Calculator** where you can play with sliders to test different ad costs and discounts.
        - We provide an **AI Shop Assistant** where you can type questions and get simple answers immediately.
        """)

    render_panel(
        "To start exploring, select a dashboard from the sidebar navigation menu. "
        "To ask questions, click on the **AI Shop Assistant** page.",
        type="success"
    )

# Configure dynamic pages list using Streamlit Page API
pages = [
    st.Page(show_welcome, title="Welcome Portal", icon="🏠"),
    st.Page("pages/1_Executive_Dashboard.py", title="Overall Shop Performance", icon="📈"),
    st.Page("pages/2_Category_Analytics.py", title="Product Types Performance", icon="🛍️"),
    st.Page("pages/3_Customer_Analytics.py", title="Customer Types Analysis", icon="👥"),
    st.Page("pages/4_Campaign_Analytics.py", title="Ad & Campaign Performance", icon="📊"),
    st.Page("pages/5_Pricing_Analytics.py", title="Discount & Price Helper", icon="💸"),
    st.Page("pages/6_Promotion_Recommendation.py", title="Strategy & Simulator", icon="🔮"),
    st.Page("pages/7_AI_Decision_Agent.py", title="AI Shop Assistant", icon="🤖"),
]

# Run navigation router
pg = st.navigation(pages)
pg.run()