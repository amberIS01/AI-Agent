import os
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import numpy as np
from fuzzywuzzy import fuzz
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class SearchResult:
    """Class to hold search result data."""
    procedure: str
    code: str
    amount: float
    source_file: str
    match_score: float = 100.0  # Default score for exact matches
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame conversion."""
        return {
            'Procedure': self.procedure,
            'Code': self.code,
            'Amount': self.amount,
            'SourceFile': self.source_file,
            'MatchScore': f"{self.match_score:.1f}%"
        }


class HospitalReimbursementBot:
    def __init__(self, data_folder='data'):
        """
        Initialize the bot with the path to the data folder.
        
        Args:
            data_folder (str): Path to the folder containing Excel files. Defaults to 'data'.
        """
        self.data_folder = Path(data_folder)
        self.data = None

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names and handle missing values.
        
        Args:
            df: Input DataFrame to be standardized
            
        Returns:
            pd.DataFrame: Standardized DataFrame
        """
        if df.empty:
            return df
            
        # Create a copy to avoid modifying the original
        df = df.copy()
        
        # Standardize column names (case-insensitive)
        column_mapping = {
            # Procedure related
            'procedure': 'Procedure',
            'proc': 'Procedure',
            'procedure_name': 'Procedure',
            'name': 'Procedure',
            'description': 'Procedure',
            
            # Code related
            'code': 'Code',
            'cpt': 'Code',
            'cpt_code': 'Code',
            'procedure_code': 'Code',
            
            # Amount related
            'amount': 'Amount',
            'price': 'Amount',
            'cost': 'Amount',
            'reimbursement': 'Amount',
            'charge': 'Amount',
            
            # Category/Type
            'category': 'Category',
            'type': 'Category',
            'department': 'Category',
            
            # Date related
            'date': 'Date',
            'service_date': 'Date',
            'procedure_date': 'Date'
        }
        
        # Apply column name standardization
        df.columns = [str(col).strip() for col in df.columns]
        df = df.rename(columns=lambda x: column_mapping.get(x.lower(), x))
        
        # Convert column names to Title Case and remove special characters
        df.columns = [re.sub(r'[^\w\s]', '', str(col)).strip().title().replace(' ', '') 
                     for col in df.columns]
        
        # Handle missing values
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
            
        for col in df.select_dtypes(include=[np.number]).columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Ensure required columns exist
        for col in ['Procedure', 'Code', 'Amount']:
            if col not in df.columns:
                df[col] = np.nan
                
        return df
    
    def _create_searchable_text(self, df: pd.DataFrame) -> pd.Series:
        """
        Create a searchable text column by combining all text columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            pd.Series: Series containing combined searchable text
        """
        # Select text columns (excluding binary and numeric types)
        text_columns = df.select_dtypes(include=['object']).columns
        
        # Combine all text columns into a single searchable string
        searchable = df[text_columns].apply(
            lambda x: ' | '.join(x.dropna().astype(str)),
            axis=1
        )
        
        return searchable
    
    def load_data(self) -> Optional[pd.DataFrame]:
        """
        Load and combine all Excel files from the data folder.
        
        Returns:
            Optional[pd.DataFrame]: Combined and standardized DataFrame or None if no data
        """
        if not self.data_folder.exists():
            print(f"[ERROR] Data folder not found: {self.data_folder}")
            return None
            
        # First try to load the sample validation data
        sample_file = self.data_folder / "sample_validation_data.xlsx"
        if sample_file.exists():
            try:
                self.data = pd.read_excel(sample_file)
                print("[INFO] Loaded sample validation data")
                return self.data
            except Exception as e:
                print(f"[WARNING] Could not load sample validation data: {str(e)}")
        
        # Fall back to regular data loading
        excel_files = list(self.data_folder.glob("*.xlsx")) + list(self.data_folder.glob("*.xls"))
        if not excel_files:
            print("[ERROR] No Excel files found in the data folder")
            return None
            
        all_data = []
        for file in excel_files:
            try:
                # Skip sample file if it exists
                if file.name == "sample_validation_data.xlsx":
                    continue
                    
                # Read all sheets
                xls = pd.ExcelFile(file)
                for sheet_name in xls.sheet_names:
                    try:
                        df = pd.read_excel(file, sheet_name=sheet_name)
                        if not df.empty:
                            # Add source file info
                            df['SourceFile'] = file.name
                            all_data.append(df)
                    except Exception as e:
                        print(f"[WARNING] Could not read sheet '{sheet_name}' from {file.name}: {str(e)}")
                        continue
            except Exception as e:
                print(f"[ERROR] Loading {file.name}: {str(e)}")
                continue
        
        if not all_data:
            print("[WARNING] No data was loaded from any files.")
            return None
            
        # Combine all data into a single DataFrame
        self.data = pd.concat(all_data, ignore_index=True)
        
        # Add searchable text column
        if not self.data.empty:
            self.data['SearchableText'] = self._create_searchable_text(self.data)
        
        total_records = len(self.data)
        print(f"\033[92m[SUCCESS]\033[0m Loaded {total_records} total records from {len(excel_files)} files")
        
        return self.data

    def process_data(self) -> Optional[pd.DataFrame]:
        """
        Process the loaded data by standardizing and cleaning it.
        
        Returns:
            Optional[pd.DataFrame]: Processed DataFrame or None if no data
        """
        if self.data is None or self.data.empty:
            print("No data to process. Please load data first using load_data().")
            return None
            
        print(f"Processing {len(self.data)} records...")
        
        # Ensure consistent data types
        if 'Amount' in self.data.columns:
            self.data['Amount'] = pd.to_numeric(self.data['Amount'], errors='coerce')
            
        # Fill any remaining NaN values in key columns
        for col in ['Procedure', 'Code']:
            if col in self.data.columns:
                self.data[col] = self.data[col].fillna('Unknown')
        
        # Remove any completely empty rows
        initial_count = len(self.data)
        self.data = self.data.dropna(how='all')
        if len(self.data) < initial_count:
            print(f"  [INFO] Removed {initial_count - len(self.data)} completely empty rows")
        
        print(f"[DONE] Processing complete. {len(self.data)} records remaining after cleaning.")
        return self.data
        
    def _calculate_match_score(self, text: str, query: str) -> float:
        """
        Calculate a match score between text and query using fuzzy matching.
        
        Args:
            text: Text to search in
            query: Search query
            
        Returns:
            float: Match score (0-100)
        """
        if not text or not query:
            return 0.0
            
        # Convert to string and lowercase for case-insensitive comparison
        text = str(text).lower()
        query = query.lower()
        
        # Use partial ratio for partial matches
        return fuzz.partial_ratio(text, query)
    
    def search(
        self, 
        query: str, 
        use_fuzzy: bool = False, 
        threshold: int = 70,
        top_n: int = 5
    ) -> Tuple[pd.DataFrame, int]:
        """
        Search for procedures matching the query.
        
        Args:
            query: Search term
            use_fuzzy: Whether to use fuzzy matching
            threshold: Minimum match score (0-100) for fuzzy matching
            top_n: Maximum number of results to return
            
        Returns:
            Tuple containing:
                - DataFrame with search results
                - Total number of matches found
        """
        print(f"\n[DEBUG] Starting search with query: '{query}'")
        print(f"[DEBUG] Data available: {not (self.data is None or self.data.empty)}")
        
        if self.data is None or self.data.empty:
            print("[ERROR] No data available. Please load data first using load_data().")
            return pd.DataFrame(columns=['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']), 0
            
        if not query or not query.strip():
            print("[ERROR] Please provide a search query.")
            return pd.DataFrame(columns=['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']), 0
            
        print(f"[SEARCH] Searching for: '{query}'" + (" (using fuzzy matching)" if use_fuzzy else ""))
        print(f"[DEBUG] Data columns: {self.data.columns.tolist()}")
        print(f"[DEBUG] First few rows:\n{self.data.head()}")
        
        results = []
        
        try:
            if use_fuzzy:
                # Fuzzy search - check all text columns
                text_columns = self.data.select_dtypes(include=['object']).columns
                
                for _, row in self.data.iterrows():
                    max_score = 0
                    
                    # Get the best match score across all text columns
                    for col in text_columns:
                        if col in row and pd.notna(row[col]):
                            score = self._calculate_match_score(str(row[col]), query)
                            max_score = max(max_score, score)
                    
                    if max_score >= threshold:
                        result = {
                            'Procedure': row.get('Procedure', 'N/A'),
                            'Code': row.get('Code', 'N/A'),
                            'Amount': row.get('Amount', 0),
                            'SourceFile': row.get('SourceFile', 'Unknown'),
                            'MatchScore': f"{max_score:.1f}%"
                        }
                        results.append(result)
                        print(f"[DEBUG] Found match: {result}")
            else:
                # Exact search (case-insensitive)
                query = str(query).lower()
                for _, row in self.data.iterrows():
                    match_found = False
                    for col in self.data.select_dtypes(include=['object']).columns:
                        if col in row and pd.notna(row[col]) and query in str(row[col]).lower():
                            match_found = True
                            break
                    
                    if match_found:
                        result = {
                            'Procedure': row.get('Procedure', 'N/A'),
                            'Code': row.get('Code', 'N/A'),
                            'Amount': row.get('Amount', 0),
                            'SourceFile': row.get('SourceFile', 'Unknown'),
                            'MatchScore': '100.0%'
                        }
                        results.append(result)
                        print(f"[DEBUG] Found exact match: {result}")
                        break  # Only add each row once
                
            print(f"[DEBUG] Found {len(results)} total matches")
            
            # Convert results to DataFrame
            if results:
                results_df = pd.DataFrame(results)
                # Ensure consistent column order
                results_df = results_df[['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']]
                return results_df.head(top_n), len(results_df)
            
            return pd.DataFrame(columns=['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']), 0
            
        except Exception as e:
            print(f"[ERROR] Error during search: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return pd.DataFrame(columns=['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']), 0

def process_data(self) -> Optional[pd.DataFrame]:
    """
    Process the loaded data by standardizing and cleaning it.
    
    Returns:
        Optional[pd.DataFrame]: Processed DataFrame or None if no data
    """
    if self.data is None or self.data.empty:
        print("No data to process. Please load data first using load_data().")
        return None
        
    print(f"Processing {len(self.data)} records...")
    
    # Ensure consistent data types
    if 'Amount' in self.data.columns:
        self.data['Amount'] = pd.to_numeric(self.data['Amount'], errors='coerce')
        
    # Fill any remaining NaN values in key columns
    for col in ['Procedure', 'Code']:
        if col in self.data.columns:
            self.data[col] = self.data[col].fillna('Unknown')
    
    # Remove any completely empty rows
    initial_count = len(self.data)
    self.data = self.data.dropna(how='all')
    if len(self.data) < initial_count:
        print(f"  [INFO] Removed {initial_count - len(self.data)} completely empty rows")
    
    print(f"[DONE] Processing complete. {len(self.data)} records remaining after cleaning.")
    return self.data
        
def _calculate_match_score(self, text: str, query: str) -> float:
    """
    Calculate a match score between text and query using fuzzy matching.
    
    Args:
        text: Text to search in
        query: Search query
        
    Returns:
        float: Match score (0-100)
    """
    if not text or not query:
        return 0.0
        
    # Convert to string and lowercase for case-insensitive comparison
    text = str(text).lower()
    query = query.lower()
    
    # Use partial ratio for partial matches
    return fuzz.partial_ratio(text, query)

def search(
    self, 
    query: str, 
    use_fuzzy: bool = False, 
    threshold: int = 70,
    top_n: int = 5
) -> Tuple[pd.DataFrame, int]:
    """
    Search for procedures matching the query.
    
    Args:
        query: Search term
        use_fuzzy: Whether to use fuzzy matching
        threshold: Minimum match score (0-100) for fuzzy matching
        top_n: Maximum number of results to return
        
    Returns:
        Tuple containing:
            - DataFrame with search results
            - Total number of matches found
    """
    print(f"\n[DEBUG] Starting search with query: '{query}'")
    print(f"[DEBUG] Data available: {not (self.data is None or self.data.empty)}")
    
    if self.data is None or self.data.empty:
        print("[ERROR] No data available. Please load data first using load_data().")
        return pd.DataFrame(columns=['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']), 0
        
    if not query or not query.strip():
        print("[ERROR] Please provide a search query.")
        return pd.DataFrame(columns=['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']), 0
        
    print(f"[SEARCH] Searching for: '{query}'" + (" (using fuzzy matching)" if use_fuzzy else ""))
    print(f"[DEBUG] Data columns: {self.data.columns.tolist()}")
    print(f"[DEBUG] First few rows:\n{self.data.head()}")
    
    results = []
    
    try:
        if use_fuzzy:
            # Fuzzy search - check all text columns
            text_columns = self.data.select_dtypes(include=['object']).columns
            
            for _, row in self.data.iterrows():
                max_score = 0
                
                # Get the best match score across all text columns
                for col in text_columns:
                    if col in row and pd.notna(row[col]):
                        score = self._calculate_match_score(str(row[col]), query)
                        max_score = max(max_score, score)
                
                if max_score >= threshold:
                    result = {
                        'Procedure': row.get('Procedure', 'N/A'),
                        'Code': row.get('Code', 'N/A'),
                        'Amount': row.get('Amount', 0),
                        'SourceFile': row.get('SourceFile', 'Unknown'),
                        'MatchScore': f"{max_score:.1f}%"
                    }
                    results.append(result)
                    print(f"[DEBUG] Found match: {result}")
        else:
            # Exact search (case-insensitive)
            query = str(query).lower()
            for _, row in self.data.iterrows():
                match_found = False
                for col in self.data.select_dtypes(include=['object']).columns:
                    if col in row and pd.notna(row[col]) and query in str(row[col]).lower():
                        match_found = True
                        break
                
                if match_found:
                    result = {
                        'Procedure': row.get('Procedure', 'N/A'),
                        'Code': row.get('Code', 'N/A'),
                        'Amount': row.get('Amount', 0),
                        'SourceFile': row.get('SourceFile', 'Unknown'),
                        'MatchScore': '100.0%'
                    }
                    results.append(result)
                    print(f"[DEBUG] Found exact match: {result}")
                    break  # Only add each row once
        
        print(f"[DEBUG] Found {len(results)} total matches")
        
        # Convert results to DataFrame
        if results:
            results_df = pd.DataFrame(results)
            # Ensure consistent column order
            results_df = results_df[['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']]
            return results_df.head(top_n), len(results_df)
        
        return pd.DataFrame(columns=['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']), 0
        
    except Exception as e:
        print(f"[ERROR] Error during search: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return pd.DataFrame(columns=['Procedure', 'Code', 'Amount', 'SourceFile', 'MatchScore']), 0


def interactive_search(bot):
    """Interactive search loop."""
    print("\n" + "="*50)
    print("  HOSPITAL REIMBURSEMENT SEARCH TOOL")
    print("  Type 'exit' to quit")
    print("="*50 + "\n")
    while True:
        print("\n" + "="*50)
        print("SEARCH OPTIONS")
        print("1. Exact search")
        print("2. Fuzzy search")
        print("3. Exit")
        
        choice = input("\nChoose an option (1-3): ").strip()
        
        if choice == '3':
            print("Exiting...")
            break
            
        if choice not in ['1', '2']:
            print("Invalid choice. Please try again.")
            continue
            
        query = input("\nEnter search term: ").strip()
        if not query:
            print("Search term cannot be empty.")
            continue
            
        # Perform search based on user choice
        use_fuzzy = (choice == '2')
        results, total = bot.search(
            query=query,
            use_fuzzy=use_fuzzy,
            threshold=70,
            top_n=5
        )
        
        if not results.empty:
            # Display results in a clean format
            print("\n" + "-"*80)
            print(f"{'PROCEDURE':<40} | {'CODE':<10} | {'AMOUNT':>10} | {'SOURCE':<20} | SCORE")
            print("-"*80)
            
            for _, row in results.iterrows():
                # Truncate long procedure names for display
                proc = (row['Procedure'][:37] + '...') if len(str(row['Procedure'])) > 40 else row['Procedure']
                amount = f"${float(row.get('Amount', 0)):,.2f}" if pd.notna(row.get('Amount')) else "N/A"
                print(f"{proc:<40} | {row.get('Code', ''):<10} | {amount:>10} | {row.get('SourceFile', '')[:17]:<20} | {row.get('MatchScore', '100.0%')}")
            
            if total > 5:
                print(f"\nShowing 5 of {total} total matches. Refine your search for better results.")


def main():
    # Create an instance of the bot
    bot = HospitalReimbursementBot()
    
    print("="*50)
    print("HOSPITAL REIMBURSEMENT BOT".center(50))
    print("="*50)
    
    # Load and process data
    print("\nLoading data from Excel files...")
    data = bot.load_data()
    
    if data is None or data.empty:
        print("❌ No data was loaded. Please check the data folder and try again.")
        return
        
    print(f"✅ Successfully loaded {len(data)} records.")
    
    # Process the data
    print("\nProcessing data...")
    processed_data = bot.process_data()
    
    if processed_data is None or processed_data.empty:
        print("❌ No data available after processing.")
        return
    
    print("\n" + "="*50)
    print("DATA SUMMARY".center(50))
    print("-"*50)
    print(f"Total procedures: {len(processed_data):,}")
    print(f"Unique codes: {processed_data['Code'].nunique():,}" if 'Code' in processed_data.columns else "No code column found")
    print(f"Data source files: {processed_data['SourceFile'].nunique():,}" if 'SourceFile' in processed_data.columns else "No source file info")
    
    # Start interactive search
    interactive_search(bot)


if __name__ == "__main__":
    main()
