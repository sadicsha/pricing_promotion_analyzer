import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add project root to path to allow backend agent and styles import
sys.path.append(str(Path(__file__).parent.parent))
from styles import inject_custom_css, render_panel
from src.agents.agent_engine import RetailAgent

# Inject styling
inject_custom_css()

st.markdown('<div class="dashboard-header">AI Shop Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">Ask questions about your shop sales, profit, and ads in simple words.</div>', unsafe_allow_html=True)

# Fetch credentials from session state or default
llm_provider = st.session_state.get("llm_provider", "Demo Mode (Works Offline)")
llm_key = st.session_state.get("llm_api_key", "")

# Initialize Backend Agent
@st.cache_resource
def get_agent(provider, api_key):
    return RetailAgent(provider=provider, api_key=api_key)

agent = get_agent(llm_provider, llm_key)

# Sidebar indicator
with st.sidebar:
    st.markdown("### 🖥️ AI Status Details")
    status_color = "green" if agent.is_live else "orange"
    status_text = "Connected to AI Model" if agent.is_live else "Offline Mode (No Key)"
    
    st.markdown(f"**Status:** :{status_color}[{status_text}]")
    st.markdown(f"**Model Selected:** `{llm_provider}`")
    
    st.markdown("---")
    st.markdown("### 📋 Shop Data Sheets Available")
    st.markdown("""
    - `orders` (purchases and bills)
    - `order_items` (items in each bill)
    - `customers` (customer lists)
    - `payments` (money paid)
    - `products` (item types)
    """)
    
    if st.button("🧹 Clear Conversation"):
        st.session_state["messages"] = []
        st.rerun()

# Initialize Chat Messages
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hello! I am your AI Shop Assistant. Ask me anything about your sales, discounts, ads, or customer types in simple words! (For example: 'Which advertisement was the most worth the money?' or 'What discount makes the most profit?')."}
    ]

# Display Suggestion Chips
st.markdown("#### 💡 Quick Questions (Click to Ask)")
col_s1, col_s2, col_s3, col_s4 = st.columns(4)

suggestions = [
    ("💸 Best Discounts", "What discount makes the most profit?"),
    ("📢 Best Ads", "Which advertisement was the most worth the money?"),
    ("👥 Customer Profit", "Which customer type makes the most profit?"),
    ("🛍️ Best Product Types", "What are the top product types by profit?")
]

prompt_to_submit = None

for idx, (label, text) in enumerate(suggestions):
    cols = [col_s1, col_s2, col_s3, col_s4]
    if cols[idx].button(label, use_container_width=True):
        prompt_to_submit = text

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle suggestion click or new user text input
user_input = st.chat_input("Type your question here...")

if prompt_to_submit:
    user_input = prompt_to_submit

if user_input:
    # Append user question
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # Generate agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = agent.run_query(user_input)
            
            # Simple term replacements in offline agent output
            response = response.replace("Offline Pricing & Discount Analysis", "Simple Discount Analysis")
            response = response.replace("Offline Campaign Performance & ROI Diagnostics", "Simple Advertisement Worth Analysis")
            response = response.replace("Offline Customer Segment Performance Analysis", "Simple Customer Types Analysis")
            response = response.replace("Offline Category Profitability Analysis", "Simple Product Types Analysis")
            response = response.replace("gross profit", "actual profit")
            response = response.replace("ROI (%)", "Worth / ROI %")
            response = response.replace("customer_segment", "customer type")
            response = response.replace("revenue", "sales")
            response = response.replace("Premium", "Big Spenders")
            response = response.replace("High Value", "Frequent Shoppers")
            response = response.replace("Regular", "Normal Shoppers")
            response = response.replace("Occasional", "Rare Shoppers")
            
            st.markdown(response)
            
    # Append assistant response
    st.session_state["messages"].append({"role": "assistant", "content": response})
    
    # Force refresh to clear state if suggestion was used
    if prompt_to_submit:
        st.rerun()
