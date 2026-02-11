# Skylark_Drones_Assignment
The Skylark BI Agent is a specialized Streamlit application that uses LangChain and Google Gemini to perform natural language data analysis on Monday.com boards. It allows founders and managers to ask complex questions about sales pipelines (Deals) and operational performance (Work Orders) without writing SQL or manual Excel formulas.
The system follows a "Retrieval-Augmented Execution" pattern. Instead of just searching for text, the agent writes and executes Python code in real-time to analyze your data.

Data Ingestion: The MondayService (custom module) fetches raw JSON data from Monday.com via GraphQL.

Data Sanitization: A cleaning layer transforms messy board headers (e.g., Close Date (A)) into Python-friendly snake_case (e.g., close_date_a).

The Brain (LLM): Google Gemini 1.5 Flash acts as the orchestrator, deciding which columns to analyze and how to structure the Python logic.

The Executor: The LangChain PandasDataFrameAgent uses a Python REPL to run the code against the local DataFrames stored in the Streamlit session state.

The Feedback Loop: If the LLM generates a parsing error, the handle_parsing_errors flag sends the error back to the model for an immediate self-correction.

⚙️ Setup & Monday.com Configuration
To get this agent running, you need to map your Monday.com boards correctly.

1. Prerequisites
Python 3.9+

A Google Gemini API Key (from Google AI Studio).

A Monday.com API Token.

2. Obtaining your Monday.com API Token
Log in to your Monday.com account.

Click on your Profile Picture in the bottom left corner.

Select Administration > API.

Copy the Personal API Token. Keep this secret!

3. Finding Board IDs
The agent requires two specific Board IDs to function:

Deals Board: Open your Sales/Deals board. The ID is the long numerical string at the end of the URL (e.g., monday.com/boards/123456789).

Work Orders Board: Repeat the process for your operational/execution board.

🚀 Installation
Clone the repository:

Install dependencies:

Configure Monday Service: Ensure your monday_service.py is in the same directory. This file should handle the GraphQL requests to Monday.com's /v2 endpoint.

Run the App:

🛠️ Data Dictionary (Expected Columns)
For the agent to provide the best insights, ensure your Monday.com boards contain the following (or similar) data points:

⚠️ Important Note on Security
The agent uses allow_dangerous_code=True. This is necessary for the agent to run the Python code required to analyze your DataFrames. Never deploy this app to a public-facing URL without adding an authentication layer (like Streamlit Authenticator).