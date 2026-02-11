import streamlit as st
import pandas as pd
from monday_service import MondayService
from langchain_google_genai import ChatGoogleGenerativeAI

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(page_title="Skylark BI Agent", page_icon="🤖", layout="wide")

st.title("🤖 Skylark Business Intelligence Agent")
st.markdown(
    """
This agent integrates with **Monday.com** to answer founder-level questions 
about Deals and Work Orders.
"""
)

with st.sidebar:
    st.header("Configuration")

    monday_api_key = st.text_input("Monday API Key", type="password")
    google_api_key = st.text_input("Google Gemini API Key", type="password")

    st.subheader("Board IDs")
    deals_board_id = st.text_input("Deals Board ID")
    work_orders_board_id = st.text_input("Work Orders Board ID")

    if st.button("Connect & Fetch Data"):
        if not monday_api_key or not deals_board_id or not work_orders_board_id:
            st.error("Please provide API keys and board IDs.")
        else:
            with st.spinner("Fetching data from Monday.com..."):
                monday = MondayService(monday_api_key)

                df_deals = monday.get_board_data(deals_board_id)
                df_orders = monday.get_board_data(work_orders_board_id)

                st.session_state["df_deals"] = df_deals
                st.session_state["df_orders"] = df_orders

                st.success(
                    f"Data loaded successfully! "
                    f"(Deals: {len(df_deals)}, Orders: {len(df_orders)})"
                )


if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! Ask me about revenue, pipeline health, or operational bottlenecks."
        }
    ]


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Ex: How is the pipeline looking for the energy sector?"):

    if "df_deals" not in st.session_state or "df_orders" not in st.session_state:
        st.error("Please load data from the sidebar first.")
        st.stop()

    if not google_api_key:
        st.error("Please enter your Google Gemini API Key.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data..."):

            try:
                df_deals = st.session_state["df_deals"]
                df_orders = st.session_state["df_orders"]

              

                # Convert numeric columns safely
                if "Masked Deal value" in df_deals.columns:
                    df_deals["Masked Deal value"] = pd.to_numeric(
                        df_deals["Masked Deal value"], errors="coerce"
                    )
                else:
                    df_deals["Masked Deal value"] = 0

                # Basic BI Metrics
                total_pipeline = df_deals["Masked Deal value"].sum()
                open_deals = df_deals[df_deals.get("Deal Status", "") == "Open"]
                open_pipeline = open_deals["Masked Deal value"].sum()

                total_deals = len(df_deals)
                total_orders = len(df_orders)

                # Sector breakdown (if available)
                sector_info = ""
                if "Sector/service" in df_deals.columns:
                    top_sector = (
                        df_deals.groupby("Sector/service")["Masked Deal value"]
                        .sum()
                        .sort_values(ascending=False)
                        .head(3)
                        .to_string()
                    )
                    sector_info = f"\nTop Sectors by Pipeline:\n{top_sector}"

               

                llm = ChatGoogleGenerativeAI(
                    model="gemini-flash-latest",
                    temperature=0,
                    google_api_key=google_api_key,
                )

                summary_context = f"""
You are a Business Intelligence Advisor for Skylark Drones.

Business Metrics:
- Total Pipeline Value: {total_pipeline}
- Open Pipeline Value: {open_pipeline}
- Total Deals: {total_deals}
- Total Work Orders: {total_orders}
{sector_info}

User Question:
{prompt}

Instructions:
1. Give a concise executive-level answer.
2. Provide insight, not just numbers.
3. Mention data caveats if appropriate.
"""

                response = llm.invoke(summary_context)
                # Gemini returns list-style content sometimes
                if isinstance(response.content, list):
                    result_text = response.content[0]["text"]
                else:
                    result_text = response.content


                st.markdown(result_text)

                st.session_state.messages.append(
                    {"role": "assistant", "content": result_text}
                )

            except Exception as e:
                error_msg = f"⚠️ Analysis error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
