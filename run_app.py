import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import re

# Set page config
st.set_page_config(
    page_title="Hospital Reimbursement Portal",
    page_icon="🏥",
    layout="wide"
)

# Simple CSS
st.markdown("""
    <style>
    .procedure-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .amount {
        font-size: 1.2em;
        font-weight: bold;
        color: #1a73e8;
    }
    </style>
""", unsafe_allow_html=True)

# Load data function
def load_data():
    data_dir = Path("data")
    all_data = []
    
    # Sample data as fallback
    sample_data = {
        'Procedure': ['Knee Replacement', 'Hip Replacement', 'Appendectomy', 'Cataract Surgery', 'Colonoscopy'],
        'Code': ['KR-101', 'HR-202', 'AP-303', 'CS-404', 'CL-505'],
        'Amount': [12500.00, 11800.00, 8500.00, 6500.00, 3200.00],
        'SectionReference': ['4.2.1', '4.2.2', '3.1.5', '5.2.1', '3.3.2'],
        'Documentation': ['Pre-op report\nSurgical notes\nPost-op report', 
                         'X-ray results\nSurgical consent\nPost-op instructions',
                         'Lab results\nSurgical notes\nPathology report',
                         'Eye exam results\nSurgical consent\nPost-op care',
                         'Referral letter\nLab results\nPathology report'],
        'Exceptions': ['Requires pre-authorization', 
                      'Special implant needed', 
                      'Standard procedure', 
                      'Standard procedure', 
                      'Bowel prep required']
    }
    
    # Try to load from Excel files first
    excel_loaded = False
    excel_files = list(data_dir.glob("*.xlsx")) + list(data_dir.glob("*.xls"))
    
    for file in excel_files:
        try:
            # Try with different engines if needed
            try:
                df = pd.read_excel(file, engine='openpyxl')
            except:
                df = pd.read_excel(file, engine='xlrd')
                
            if not df.empty:
                df['SourceFile'] = file.name
                # Ensure required columns exist
                for col in ['Procedure', 'Code', 'Amount']:
                    if col not in df.columns:
                        df[col] = ''
                all_data.append(df)
                excel_loaded = True
        except Exception as e:
            st.warning(f"Error loading {file.name}: {str(e)}")
    
    # If no Excel files loaded, use sample data
    if not excel_loaded:
        st.warning("Using sample data. Add Excel files to the 'data' folder to load your own data.")
        return pd.DataFrame(sample_data)
    
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame(sample_data)

# Search function
def search_data(df, query):
    if not df.empty and query and str(query).strip():
        query = str(query).lower().strip()
        results = []
        
        for _, row in df.iterrows():
            # Check if query matches any field
            match_score = 0
            
            # Check procedure name (highest weight)
            if 'Procedure' in row and pd.notna(row['Procedure']):
                if query in str(row['Procedure']).lower():
                    match_score += 3
            
            # Check code (high weight)
            if 'Code' in row and pd.notna(row['Code']):
                if query in str(row['Code']).lower():
                    match_score += 2
            
            # Check other text fields
            text_fields = ['SectionReference', 'Documentation', 'Exceptions']
            for field in text_fields:
                if field in row and pd.notna(row[field]):
                    if query in str(row[field]).lower():
                        match_score += 1
            
            if match_score > 0:
                result = row.copy()
                result['MatchScore'] = match_score
                results.append(result)
        
        # Sort by match score and return top 10
        results = sorted(results, key=lambda x: x['MatchScore'], reverse=True)
        return pd.DataFrame(results[:10])
    
    # If no query, return first 10 rows with required columns
    required_cols = ['Procedure', 'Code', 'Amount', 'SectionReference', 'Documentation', 'Exceptions']
    available_cols = [col for col in required_cols if col in df.columns]
    return df[available_cols].head(10)

# Main app
def main():
    st.title("🏥 Hospital Reimbursement Portal")
    
    # Load data
    if 'data' not in st.session_state:
        with st.spinner('Loading data...'):
            st.session_state.data = load_data()
    
    # Sidebar with quick searches
    with st.sidebar:
        st.header("Quick Searches")
        if st.button("Show all procedures"):
            st.session_state.search_query = ""
        if st.button("Show expensive procedures (>5000)"):
            st.session_state.search_query = ">5000"
        if st.button("Show common procedures"):
            st.session_state.search_query = "common"
    
    # Search box
    search_query = st.text_input(
        "Search for procedures, codes, or amounts:",
        value=getattr(st.session_state, 'search_query', '')
    )
    
    # Display results
    if not st.session_state.data.empty:
        results = search_data(st.session_state.data, search_query)
        
        if results.empty:
            st.warning("No results found. Try a different search term.")
        else:
            st.write(f"Found {len(results)} results:")
            
            for _, row in results.iterrows():
                # Create a card for each result
                with st.container():
                    st.markdown(
                        f"""
                        <div style='
                            padding: 15px;
                            margin: 10px 0;
                            border-radius: 10px;
                            background-color: #f8f9fa;
                            border-left: 5px solid #1e88e5;
                        '>
                            <h3>{}</h3>
                            <p><strong>Code:</strong> {} | <strong>Section:</strong> {}</p>
                            <p style='font-size: 1.2em; color: #2e7d32;'><strong>CHF {}</strong></p>
                        </div>
                        """.format(
                            row.get('Procedure', 'N/A'),
                            row.get('Code', 'N/A'),
                            row.get('SectionReference', 'N/A'),
                            f"{float(row.get('Amount', 0)):,.2f}" if pd.notna(row.get('Amount')) else 'N/A'
                        ),
                        unsafe_allow_html=True
                    )
                    
                    # Show details in expander
                    with st.expander("View Details", expanded=False):
                        if 'Documentation' in row and pd.notna(row['Documentation']):
                            st.markdown("**Documentation Required:**")
                            docs = str(row['Documentation']).split('\n')
                            for doc in docs:
                                doc = doc.strip()
                                if doc:
                                    st.markdown(f"- {doc}")
                        
                        if 'Exceptions' in row and pd.notna(row['Exceptions']):
                            st.warning(f"**Note:** {row['Exceptions']}")
                        
                        if 'SourceFile' in row and pd.notna(row['SourceFile']):
                            st.caption(f"Source: {row['SourceFile']}")
                            
                    st.markdown("---")
    else:
        st.error("Failed to load data. Please check your data files.")

if __name__ == "__main__":
    main()
