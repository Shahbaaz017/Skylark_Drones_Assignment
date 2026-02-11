import requests
import pandas as pd
import json

class MondayService:
    def __init__(self, api_key):
        self.api_url = "https://api.monday.com/v2"
        self.headers = {"Authorization": api_key, "API-Version": "2023-10"}

    def get_board_data(self, board_id):
        """
        Fetches all items from a board and normalizes them into a clean Pandas DataFrame.
        """
        # GraphQL Query to get item names and column values
        query = """
        query ($board_id: [ID!]) {
            boards (ids: $board_id) {
                name
                items_page (limit: 500) {
                    items {
                        name
                        column_values {
                            column { title }
                            text
                        }
                    }
                }
            }
        }
        """
        
        try:
            response = requests.post(
                self.api_url, 
                json={'query': query, 'variables': {'board_id': [board_id]}}, 
                headers=self.headers
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.text}")
                
            data = response.json()
            
            # Error handling for GraphQL errors
            if "errors" in data:
                raise Exception(f"GraphQL Error: {data['errors']}")

            items = data['data']['boards'][0]['items_page']['items']
            
            # Transformation Logic: Convert Monday's nested JSON to Flat Rows
            normalized_data = []
            for item in items:
                row = {"Name": item['name']}
                for col in item['column_values']:
                    # Handle empty columns gracefully
                    if col['column'] and col['column']['title']:
                        row[col['column']['title']] = col['text'] if col['text'] else None
                normalized_data.append(row)

            df = pd.DataFrame(normalized_data)
            return self._clean_dataframe(df)

        except Exception as e:
            return pd.DataFrame() # Return empty DF on failure to ensure app doesn't crash

    def _clean_dataframe(self, df):
        """
        Handles 'Data Resilience': Standardizing dates, numeric values, and handling NaNs.
        """
        if df.empty:
            return df

        # Auto-detect and convert numeric columns
        for col in df.columns:
            # Try converting to numeric, coercing errors to NaN
            try:
                # Remove currency symbols or commas if present
                if df[col].dtype == object:
                    clean_col = df[col].astype(str).str.replace(r'[$,]', '', regex=True)
                    pd.to_numeric(clean_col, errors='raise') # Test conversion
                    df[col] = pd.to_numeric(clean_col, errors='coerce')
            except:
                pass # Keep as string if not numeric

            # Standardize Dates (look for columns with 'date' in the name)
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Handle Missing Values (Fill NA with explicit 'Unknown' for categorical, 0 for numeric)
        # This helps the AI understand that data is missing rather than crashing
        df = df.fillna("N/A")
        
        return df