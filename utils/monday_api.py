import os
import requests
import json
import logging
from datetime import datetime

class MondayAPI:
    """Monday.com API integration utilities"""

    def __init__(self):
        self.api_token = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQxMDM1MDMyNiwiYWFpIjoxMSwidWlkIjo1NTIyMDQ0LCJpYWQiOiIyMDI0LTA5LTEzVDExOjUyOjQzLjAwMFoiLCJwZXIiOiJtZTp3cml0ZSIsImFjdGlkIjozNzk1MywicmduIjoidXNlMSJ9.hwTlwMwtbhKdZsYcGT7UoENBLZUAxnfUXchj5RZJBz4"
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def format_date_to_dd_mm_yyyy(self, date_string):
        """Convert various date formats to dd/mm/yyyy"""
        if not date_string or date_string.strip() == "":
            return ""
        
        # Clean the input string
        date_string = date_string.strip()
        
        # If already in dd/mm/yyyy format, validate and return
        import re
        dd_mm_yyyy_pattern = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_string)
        if dd_mm_yyyy_pattern:
            day, month, year = dd_mm_yyyy_pattern.groups()
            try:
                # Validate the date
                parsed_date = datetime(int(year), int(month), int(day))
                return parsed_date.strftime('%d/%m/%Y')
            except ValueError:
                pass
        
        # List of common date formats to try
        date_formats = [
            '%Y-%m-%d',           # 2024-01-15
            '%d/%m/%Y',           # 15/01/2024 (already correct)
            '%m/%d/%Y',           # 01/15/2024
            '%Y/%m/%d',           # 2024/01/15
            '%d-%m-%Y',           # 15-01-2024
            '%Y-%m-%dT%H:%M:%S',  # 2024-01-15T10:30:00
            '%Y-%m-%dT%H:%M:%SZ', # 2024-01-15T10:30:00Z
            '%Y-%m-%dT%H:%M:%S.%fZ', # 2024-01-15T10:30:00.000Z
            '%d/%m/%y',           # 15/01/24
            '%d.%m.%Y',           # 15.01.2024
            '%Y.%m.%d',           # 2024.01.15
            '%d %b %Y',           # 15 Jan 2024
            '%b %d, %Y',          # Jan 15, 2024
            '%B %d, %Y',          # January 15, 2024
            '%d %B %Y',           # 15 January 2024
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_string, date_format)
                formatted = parsed_date.strftime('%d/%m/%Y')
                logging.info(f"Successfully parsed '{date_string}' using format '{date_format}' -> '{formatted}'")
                return formatted
            except ValueError:
                continue
        
        # If no format matches, try to extract date parts using regex
        
        # Try to find year, month, day patterns (ISO format)
        year_month_day = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', date_string)
        if year_month_day:
            year, month, day = year_month_day.groups()
            try:
                parsed_date = datetime(int(year), int(month), int(day))
                formatted = parsed_date.strftime('%d/%m/%Y')
                logging.info(f"Parsed using regex (YYYY-MM-DD): '{date_string}' -> '{formatted}'")
                return formatted
            except ValueError:
                pass
        
        # Try day/month/year or month/day/year patterns
        day_month_year = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', date_string)
        if day_month_year:
            first, second, year = day_month_year.groups()
            # First try day/month interpretation (European format)
            try:
                parsed_date = datetime(int(year), int(second), int(first))
                formatted = parsed_date.strftime('%d/%m/%Y')
                logging.info(f"Parsed using regex (DD/MM/YYYY): '{date_string}' -> '{formatted}'")
                return formatted
            except ValueError:
                # If that fails, try month/day interpretation (US format)
                try:
                    parsed_date = datetime(int(year), int(first), int(second))
                    formatted = parsed_date.strftime('%d/%m/%Y')
                    logging.info(f"Parsed using regex (MM/DD/YYYY): '{date_string}' -> '{formatted}'")
                    return formatted
                except ValueError:
                    pass
        
        logging.warning(f"Could not parse date format: {date_string}")
        return date_string  # Return original if parsing fails

    def execute_query(self, query, variables=None):
        """Execute GraphQL query to Monday.com API"""
        try:
            payload = {
                "query": query,
                "variables": variables or {}
            }

            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                logging.error(f"Monday.com API errors: {result['errors']}")
                raise Exception(f"API errors: {result['errors']}")

            return result.get("data")

        except requests.exceptions.RequestException as e:
            logging.error(f"Monday.com API request failed: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")

    def get_board_columns(self, board_id):
        """Get all columns from a Monday.com board"""
        query = """
        query GetBoardColumns($boardId: ID!) {
            boards(ids: [$boardId]) {
                columns {
                    id
                    title
                    type
                }
            }
        }
        """

        variables = {"boardId": board_id}
        result = self.execute_query(query, variables)

        if result and result.get("boards"):
            return result["boards"][0].get("columns", [])
        return []

    def get_board_items(self, board_id, limit=50):
        """Get items from a Monday.com board"""
        query = """
        query GetBoardItems($boardId: ID!, $limit: Int) {
            boards(ids: [$boardId]) {
                items(limit: $limit) {
                    id
                    name
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
        }
        """

        variables = {"boardId": str(board_id), "limit": limit}
        result = self.execute_query(query, variables)

        if result and result.get("boards") and len(result["boards"]) > 0:
            return result["boards"][0].get("items", [])
        return []

    def get_item_by_id(self, board_id, item_id):
        """Get a specific item by ID from a Monday.com board"""
        query = """
        query ($itemId: ID!) {
            items(ids: [$itemId]) {
                id
                name
                board {
                    id
                }
                column_values {
                    id
                    text
                    value
                    type
                    ... on MirrorValue {
                        display_value
                    }
                }
            }
        }
        """

        variables = {"itemId": str(item_id)}
        result = self.execute_query(query, variables)

        if result and result.get("items") and len(result["items"]) > 0:
            item = result["items"][0]
            # Verify the item belongs to the correct board
            if item.get("board", {}).get("id") == str(board_id):
                return item
        return None

    def get_item_column_values(self, item_id):
        """Get column values for a specific item"""
        query = """
        query ($itemId: ID!) {
            items(ids: [$itemId]) {
                id
                name
                column_values {
                    id
                    text
                    value
                    type
                    ... on MirrorValue {
                        display_value
                    }
                }
            }
        }
        """

        variables = {"itemId": str(item_id)}
        result = self.execute_query(query, variables)

        if result and result.get("items") and len(result["items"]) > 0:
            return result["items"][0]
        return None

    def get_column_value(self, column_data):
        """Extract the correct value from a column, handling mirror columns and formatting dates"""
        if not column_data:
            logging.warning("No column data provided")
            return ""

        logging.info(f"Processing column data: {column_data}")
        
        column_type = column_data.get('type', '')
        raw_value = ""

        # For mirror columns, use display_value if available
        if column_data.get('display_value'):
            raw_value = str(column_data['display_value']).strip()
            logging.info(f"Using display_value: '{raw_value}'")
        elif column_data.get('text'):
            # For text columns, use text value
            raw_value = str(column_data['text']).strip()
            logging.info(f"Using text value: '{raw_value}'")
        else:
            # For other column types, try to extract from value
            value = column_data.get('value')
            if value:
                try:
                    # Try to parse JSON value
                    import json
                    parsed_value = json.loads(value) if isinstance(value, str) else value
                    logging.info(f"Parsed JSON value: {parsed_value}")

                    if isinstance(parsed_value, dict):
                        # Check if it's an empty structure (like {'ids': []})
                        if 'ids' in parsed_value and not parsed_value.get('ids'):
                            logging.info("Empty ids array detected, returning empty string")
                            return ""
                        
                        # Look for common value fields
                        if 'text' in parsed_value:
                            raw_value = str(parsed_value['text']).strip()
                            logging.info(f"Using parsed text: '{raw_value}'")
                        elif 'label' in parsed_value:
                            raw_value = str(parsed_value['label']).strip()
                            logging.info(f"Using parsed label: '{raw_value}'")
                        elif 'date' in parsed_value:
                            raw_value = str(parsed_value['date']).strip()
                            logging.info(f"Using parsed date: '{raw_value}'")
                        else:
                            # Check if all values in dict are empty/None
                            non_empty_values = [v for v in parsed_value.values() if v]
                            if not non_empty_values:
                                logging.info("All dict values are empty, returning empty string")
                                return ""
                            raw_value = str(parsed_value).strip()
                            logging.info(f"Using stringified parsed value: '{raw_value}'")
                    else:
                        raw_value = str(parsed_value).strip()
                        logging.info(f"Using stringified parsed value: '{raw_value}'")
                except Exception as e:
                    logging.error(f"Error parsing JSON value: {e}")
                    raw_value = str(value).strip()
                    logging.info(f"Using raw value: '{raw_value}'")

        if not raw_value:
            logging.warning("No value found in column data")
            return ""

        # Always try to format dates to dd/mm/yyyy - check if this looks like a date first
        if self.is_date_like(raw_value) or column_type in ['date', 'creation_log', 'lookup', 'timeline']:
            formatted_date = self.format_date_to_dd_mm_yyyy(raw_value)
            if formatted_date:
                # Always return the formatted date, even if it was already in correct format
                if formatted_date != raw_value:
                    logging.info(f"Formatted date from '{raw_value}' to '{formatted_date}'")
                return formatted_date

        return raw_value

    def is_date_like(self, value):
        """Check if a string looks like a date"""
        if not value or not isinstance(value, str):
            return False
        
        import re
        # Clean the value for better pattern matching
        cleaned_value = value.strip()
        
        # Common date patterns - expanded for better detection
        date_patterns = [
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',     # 2024-01-15 or 2024/01/15
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',     # 15/01/2024 or 15-01-2024
            r'\d{4}\.\d{1,2}\.\d{1,2}',         # 2024.01.15
            r'\d{1,2}\.\d{1,2}\.\d{4}',         # 15.01.2024
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}T',    # ISO format with time
            r'\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',  # 15 Jan, 15 Feb, etc.
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}',  # Jan 15, Feb 20, etc.
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',   # General date patterns including 2-digit years
            r'\d{4}',                           # Just a year (when length is exactly 4)
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, cleaned_value.lower()):
                return True
        
        # Additional check for standalone year
        if re.match(r'^\d{4}$', cleaned_value) and 1900 <= int(cleaned_value) <= 2100:
            return True
            
        return False

    def update_item_column(self, board_id, item_id, column_id, value):
        """Update a specific column value for an item"""
        # Get column type to determine proper formatting and mutation
        try:
            columns = self.get_board_columns(board_id)
            column_type = None
            for col in columns:
                if col['id'] == column_id:
                    column_type = col['type']
                    break

            logging.info(f"Column {column_id} type: {column_type}")

            # Format dates before saving - check for any date-like content
            processed_value = value
            if (column_type in ['date', 'creation_log', 'text', 'lookup', 'timeline'] or 
                self.is_date_like(str(value))):
                formatted_date = self.format_date_to_dd_mm_yyyy(str(value))
                if formatted_date:
                    processed_value = formatted_date
                    if formatted_date != str(value):
                        logging.info(f"Formatted date for saving: '{value}' -> '{processed_value}'")
                    else:
                        logging.info(f"Date already in correct format: '{processed_value}'")

            # Format value based on column type
            if column_type == 'long_text':
                # For long text columns, use simple string format as per Monday.com API docs
                formatted_value = str(processed_value)
            elif column_type == 'text':
                # For regular text columns, use JSON format
                formatted_value = json.dumps(str(processed_value))
            else:
                # For other column types, preserve original formatting
                if isinstance(processed_value, str):
                    formatted_value = json.dumps(processed_value)
                else:
                    formatted_value = json.dumps(str(processed_value))

            # Use different mutation for long text columns
            if column_type == 'long_text':
                query = """
                mutation UpdateItemColumn($boardId: ID!, $itemId: ID!, $columnId: String!, $value: String!) {
                    change_simple_column_value(
                        board_id: $boardId,
                        item_id: $itemId,
                        column_id: $columnId,
                        value: $value
                    ) {
                        id
                    }
                }
                """

                variables = {
                    "boardId": board_id,
                    "itemId": item_id,
                    "columnId": column_id,
                    "value": formatted_value
                }
            else:
                query = """
                mutation UpdateItemColumn($boardId: ID!, $itemId: ID!, $columnId: String!, $value: JSON!) {
                    change_column_value(
                        board_id: $boardId,
                        item_id: $itemId,
                        column_id: $columnId,
                        value: $value
                    ) {
                        id
                    }
                }
                """

                variables = {
                    "boardId": board_id,
                    "itemId": item_id,
                    "columnId": column_id,
                    "value": formatted_value
                }

            result = self.execute_query(query, variables)
            logging.info(f"Updated column {column_id} for item {item_id} in board {board_id} with value: {value}")
            return result

        except Exception as e:
            logging.error(f"Error getting column type: {e}")
            # Fallback to regular mutation with JSON formatting
            formatted_value = json.dumps(str(value))

            query = """
            mutation UpdateItemColumn($boardId: ID!, $itemId: ID!, $columnId: String!, $value: JSON!) {
                change_column_value(
                    board_id: $boardId,
                    item_id: $itemId,
                    column_id: $columnId,
                    value: $value
                ) {
                    id
                }
            }
            """

            variables = {
                "boardId": board_id,
                "itemId": item_id,
                "columnId": column_id,
                "value": formatted_value
            }

        result = self.execute_query(query, variables)
        logging.info(f"Updated column {column_id} for item {item_id} in board {board_id} with value: {value}")
        return result

    def create_item(self, board_id, item_name, group_id=None):
        """Create a new item in Monday.com board"""
        group_clause = f', group_id: "{group_id}"' if group_id else ""

        mutation = f"""
        mutation {{
            create_item (board_id: {board_id}, item_name: "{item_name}"{group_clause}) {{
                id
                name
            }}
        }}
        """

        return self._make_request(mutation)

    def create_item_with_values(self, board_id, item_name, column_values, group_id=None):
        """Create a new item with multiple column values in a single request"""
        try:
            # Use GraphQL variables to properly handle special characters
            mutation = """
            mutation CreateItem($boardId: ID!, $itemName: String!, $columnValues: JSON!, $groupId: String) {
                create_item (
                    board_id: $boardId, 
                    item_name: $itemName,
                    column_values: $columnValues,
                    group_id: $groupId
                ) {
                    id
                    name
                }
            }
            """
            
            variables = {
                "boardId": int(board_id),
                "itemName": item_name,
                "columnValues": json.dumps(column_values),
                "groupId": group_id
            }
            
            # Use execute_query instead of _make_request for proper variable handling
            result = self.execute_query(mutation, variables)
            logging.info(f"Create item result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error creating item with values: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _make_request(self, mutation):
        """Helper function to make the API request"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            data = {'query': mutation}
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                logging.error(f"Monday.com API errors: {result['errors']}")
                raise Exception(f"API errors: {result['errors']}")
            
            return result.get("data")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Monday.com API request failed: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")
