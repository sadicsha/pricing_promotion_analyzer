import os
import re
import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_classic.agents import initialize_agent, AgentType
from langchain_classic.tools import Tool
from langchain_groq import ChatGroq

# Database connection
DB_PATH = Path("database/retail_marketing.db")
PROCESSED_PATH = Path("data/processed")

class RetailAgent:
    def __init__(self, provider="Demo Mode (Offline Heuristics)", api_key=""):
        self.provider = provider
        self.api_key = api_key
        self.engine = create_engine(f"sqlite:///{DB_PATH}")
        self.is_live = provider != "Demo Mode (Offline Heuristics)" and api_key != ""
        
        # Load local datasets for fast simulated lookup
        try:
            self.sales_df = pd.read_csv(PROCESSED_PATH / "sales_features.csv")
            self.campaigns_df = pd.read_csv(PROCESSED_PATH / "campaigns.csv")
        except Exception:
            self.sales_df = pd.DataFrame()
            self.campaigns_df = pd.DataFrame()

    def run_query(self, query_text):
        """
        Main query entry point. Routes to Live LangChain Agent or Simulated AI Analyst.
        """
        if self.is_live:
            try:
                return self._run_live_agent(query_text)
            except Exception as e:
                return (
                    f"⚠️ **Error running Live LLM Agent:** {str(e)}\n\n"
                    f"**Falling back to Simulated Offline AI Agent to answer your query:**\n\n"
                    f"{self._run_simulated_agent(query_text)}"
                )
        else:
            return self._run_simulated_agent(query_text)

    def _run_live_agent(self, query_text):
        """
        Initializes and runs the live LangChain agent using the user's API Key.
        """
        # Configure env key for LangChain modules
        if self.provider == "Groq API":
            os.environ["GROQ_API_KEY"] = self.api_key
            llm = ChatGroq(model_name="mixtral-8x7b-32768", temperature=0.2)
        elif self.provider == "OpenAI":
            from langchain_openai import ChatOpenAI
            os.environ["OPENAI_API_KEY"] = self.api_key
            llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2)
        elif self.provider == "Gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            os.environ["GOOGLE_API_KEY"] = self.api_key
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
        else:
            raise ValueError("Unsupported provider")

        # Set up SQL Database Tool
        db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
        
        # Define additional analytical tools
        tools = [
            Tool(
                name="SQL_Query_Executor",
                func=lambda q: db.run(q),
                description="Use this to execute raw SQL SELECT queries on the SQLite database tables (orders, order_items, customers, payments, products). Only write SELECT queries."
            ),
            Tool(
                name="KPI_Analyzer",
                func=lambda x: f"Total Revenue: ₹{self.sales_df['revenue'].sum():,.2f}, Total Profit: ₹{self.sales_df['gross_profit'].sum():,.2f}, Average Margin: {self.sales_df['profit_margin_pct'].mean():.2f}%",
                description="Use this tool to fetch high level business metrics."
            ),
            Tool(
                name="Discount_Performance_Fetcher",
                func=self._get_discount_effectiveness_summary,
                description="Use this tool to retrieve statistics about how different discount percentages performed historically."
            )
        ]
        
        # Initialize zero-shot react agent
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )
        
        # Run agent
        response = agent.run(
            f"You are a retail pricing intelligence assistant. Analyze this user query and run SQL or analytical tools to answer it: '{query_text}'. "
            "Formulate the response in clear, concise markdown with appropriate headers."
        )
        return response

    def _df_to_markdown(self, df):
        if df.empty:
            return "No records found."
        headers = list(df.columns)
        md = "| " + " | ".join([str(h) for h in headers]) + " |\n"
        md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for _, row in df.iterrows():
            md += "| " + " | ".join([str(val).replace("|", "\\|") for val in row]) + " |\n"
        return md

    def _run_simulated_agent(self, query_text):
        """
        Simulated AI Agent. Parses query keywords and runs python logic, 
        returning accurate retail analytics formatted as beautiful markdown.
        """
        q = query_text.lower()
        
        # 1. Discount / Pricing Queries
        if any(w in q for w in ["discount", "offer", "percent", "sweet spot"]):
            summary = self._get_discount_effectiveness_summary()
            return (
                "### 🎯 Offline Pricing & Discount Analysis\n\n"
                "Historical retail transactions were analyzed to evaluate discount performance across campaigns:\n\n"
                f"{summary}\n\n"
                "**💡 Recommendation:**\n"
                "- A **5% discount** is historically the most profitable, yielding high profit margins and strong gross profits.\n"
                "- Capping standard promotional discounts at **10%** is advised. Discounts above 15% suffer from diminishing marginal returns and erode margins without driving sufficient volume growth."
            )
            
        # 2. Campaign ROI Queries
        elif any(w in q for w in ["campaign", "roi", "marketing", "channel"]):
            try:
                mapping = pd.read_csv(PROCESSED_PATH / "campaign_sales_mapping.csv")
                merged = self.sales_df.merge(mapping, on="order_id", how="left")
                camp_perf = merged.groupby("campaign_id").agg({
                    "revenue": "sum",
                    "gross_profit": "sum"
                }).reset_index()
                camp_perf = camp_perf.merge(self.campaigns_df, on="campaign_id", how="left")
                camp_perf["roi_pct"] = ((camp_perf["gross_profit"] - camp_perf["budget"]) / camp_perf["budget"]) * 100
                camp_perf = camp_perf.sort_values("roi_pct", ascending=False)
                
                table_md = "| Campaign Name | Channel | Discount % | Budget | Revenue | Profit | ROI (%) |\n|---|---|---|---|---|---|---|\n"
                for _, row in camp_perf.iterrows():
                    table_md += f"| {row['campaign_name']} | {row['channel']} | {row['discount_pct']}% | ₹{row['budget']:,} | ₹{row['revenue']:,.2f} | ₹{row['gross_profit']:,.2f} | {row['roi_pct']:.1f}% |\n"
                
                best_camp = camp_perf.iloc[0]
                
                return (
                    "### 📊 Offline Campaign Performance & ROI Diagnostics\n\n"
                    "Here is a summary of the marketing campaigns and their return on investment (ROI):\n\n"
                    f"{table_md}\n\n"
                    f"**💡 Recommendation:**\n"
                    f"- The most successful campaign is **'{best_camp['campaign_name']}'** (via the {best_camp['channel']} channel) generating a **{best_camp['roi_pct']:.1f}% ROI**.\n"
                    f"- It is recommended to repeat this promotion configuration for next month."
                )
            except Exception as e:
                return f"Error retrieving campaign ROI: {e}"

        # 3. Customer Segments
        elif any(w in q for w in ["customer", "segment", "premium", "high value", "regular"]):
            try:
                orders_df = pd.read_csv(Path("data/raw/olist_orders_dataset.csv"))
                segments_df = pd.read_csv(PROCESSED_PATH / "customer_segments.csv")
                
                merged = self.sales_df.merge(orders_df[["order_id", "customer_id"]], on="order_id", how="inner")
                merged = merged.merge(segments_df[["customer_id", "customer_segment"]], on="customer_id", how="inner")
                
                seg_summary = merged.groupby("customer_segment").agg({
                    "revenue": "sum",
                    "gross_profit": "sum",
                    "order_id": "nunique"
                }).reset_index()
                
                table_md = "| Segment | Total Revenue | Gross Profit | Orders Count | Average Order Value |\n|---|---|---|---|---|\n"
                for _, row in seg_summary.iterrows():
                    aov = row['revenue'] / row['order_id']
                    table_md += f"| {row['customer_segment']} | ₹{row['revenue']:,.2f} | ₹{row['gross_profit']:,.2f} | {row['order_id']:,} | ₹{aov:,.2f} |\n"
                    
                return (
                    "### 👥 Offline Customer Segment Performance Analysis\n\n"
                    "Analysis of purchasing metrics across randomly simulated customer segments:\n\n"
                    f"{table_md}\n\n"
                    "**💡 Recommendation:**\n"
                    "- **Premium & High Value** segments represent our most profitable buckets per basket size.\n"
                    "- Focus loyalty rewards and tiered incentives (e.g., free shipping thresholds) on **Regular** customers, who form the bulk of transactions."
                )
            except Exception as e:
                return f"Error analyzing customer segments: {e}"

        # 4. Category Queries
        elif any(w in q for w in ["category", "categories", "product", "products"]):
            try:
                products_df = pd.read_csv(Path("data/raw/olist_products_dataset.csv"))
                translation_df = pd.read_csv(Path("data/raw/product_category_name_translation.csv"))
                prod_trans = products_df.merge(translation_df, on="product_category_name", how="left")
                merged = self.sales_df.merge(prod_trans[["product_id", "product_category_name_english"]], on="product_id", how="left")
                merged["product_category_name_english"] = merged["product_category_name_english"].fillna("unknown")
                
                cat_summary = merged.groupby("product_category_name_english").agg({
                    "revenue": "sum",
                    "gross_profit": "sum"
                }).reset_index().sort_values("gross_profit", ascending=False).head(5)
                
                table_md = "| Category Name | Total Sales Revenue | Gross Profit Generated |\n|---|---|---|\n"
                for _, row in cat_summary.iterrows():
                    table_md += f"| {row['product_category_name_english']} | ₹{row['revenue']:,.2f} | ₹{row['gross_profit']:,.2f} |\n"
                    
                return (
                    "### 🛍️ Offline Category Profitability Analysis\n\n"
                    "Here are the top 5 most profitable product categories:\n\n"
                    f"{table_md}\n\n"
                    "**💡 Recommendation:**\n"
                    "- Increase promotional banners and allocate larger marketing shares to these top 5 categories. "
                    "They represent the strongest revenue engines in the organization."
                )
            except Exception as e:
                return f"Error analyzing product categories: {e}"

        # 5. Raw SQL execution requests
        elif "select" in q and "from" in q:
            try:
                sql_q = query_text
                # strip out markdown blocks if written inside one
                sql_q = sql_q.replace("```sql", "").replace("```", "").strip()
                res = pd.read_sql(sql_q, self.engine)
                return (
                    "### 🖥️ SQL Execution Results\n\n"
                    "SQL Query ran successfully against SQLite database:\n"
                    f"```sql\n{sql_q}\n```\n\n"
                    f"{self._df_to_markdown(res.head(20))}"
                )
            except Exception as e:
                return f"⚠️ **SQL execution error:** {str(e)}"
                
        # 6. Default response
        else:
            return (
                "👋 **Hello! I am your AI Pricing Analyst.**\n\n"
                "I can help you analyze financial performance, discounts, campaign ROI, and customer segmentation. "
                "Since we are in **Demo Mode**, I parse key terms in your question to answer using local database logic.\n\n"
                "Try asking me questions like:\n"
                "- *What discount percentage is most profitable?*\n"
                "- *Which campaign had the highest ROI?*\n"
                "- *Show customer segment profitability.*\n"
                "- *What are the top product categories by profit?*\n"
                "- *Or write a SQL query (e.g. `SELECT * FROM campaigns`)*"
            )

    def _get_discount_effectiveness_summary(self, *args, **kwargs):
        """
        Helper to summarize discount performance in a markdown table.
        """
        try:
            mapping = pd.read_csv(PROCESSED_PATH / "campaign_sales_mapping.csv")
            merged = self.sales_df.merge(mapping, on="order_id", how="left")
            merged = merged.merge(self.campaigns_df[["campaign_id", "discount_pct"]], on="campaign_id", how="left")
            
            disc_summary = merged.groupby("discount_pct").agg({
                "revenue": "sum",
                "gross_profit": "sum",
                "order_id": "count"
            }).reset_index()
            disc_summary.columns = ["discount_pct", "revenue", "profit", "units_sold"]
            disc_summary["margin_pct"] = (disc_summary["profit"] / disc_summary["revenue"]) * 100
            
            table_md = "| Discount Rate | Total Revenue | Gross Profit | Units Sold | Average Margin (%) |\n|---|---|---|---|---|\n"
            for _, row in disc_summary.iterrows():
                table_md += f"| {row['discount_pct']}% | ₹{row['revenue']:,.2f} | ₹{row['profit']:,.2f} | {row['units_sold']:,} | {row['margin_pct']:.1f}% |\n"
                
            return table_md
        except Exception as e:
            return f"Error fetching discount summary: {e}"
