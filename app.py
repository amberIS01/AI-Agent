import streamlit as st
from datetime import datetime
from bot import HospitalReimbursementBot
import pandas as pd
import os

# Set page configuration
st.set_page_config(
    page_title="Hospital Reimbursement Query Portal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
    <style>
        .main-header {font-size: 2.5rem; color: #1E3F66; margin-bottom: 1rem;}
        .sub-header {color: #2E5A88; margin: 1.5rem 0 1rem 0;}
        .result-box {
            background-color: #F8FAFF;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 5px solid #1E3F66;
        }
        .quick-question-btn {
            width: 100%;
            margin: 0.5rem 0;
            padding: 0.5rem;
            text-align: left;
            background-color: #E8F0FE;
            color: #1E3F66;
            border: 1px solid #B8D4FF;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .quick-question-btn:hover {
            background-color: #D0E2FF;
            transform: translateX(5px);
        }
        .section {
            background-color: white;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'bot' not in st.session_state:
    st.session_state.bot = HospitalReimbursementBot(data_folder='data')
    try:
        # Load and process data when the app starts
        with st.spinner("Loading reimbursement data..."):
            # Force reload data
            st.session_state.bot.data = None
            data = st.session_state.bot.load_data()
            if data is not None:
                processed_data = st.session_state.bot.process_data()
                if processed_data is not None:
                    st.success(f"Successfully loaded {len(processed_data)} records!")
                else:
                    st.error("Failed to process data")
            else:
                st.error("No data was loaded. Please check if there are Excel files in the data directory.")
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        import traceback
        st.text(traceback.format_exc())
    
    st.session_state.last_query = ""
    st.session_state.results = None
    st.session_state.quick_question = ""  # Store the quick question separately

# Sidebar with quick questions
with st.sidebar:
    st.markdown("""
    <style>
        .quick-question-btn {
            margin-bottom: 8px;
            width: 100%;
            text-align: left;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: all 0.2s;
        }
        .quick-question-btn:hover {
            background-color: #f0f2f6;
            transform: translateX(4px);
        }
        .quick-question-btn:active {
            transform: translateX(0);
        }
        .btn-icon {
            margin-right: 8px;
            font-size: 1.1em;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("## 💡 Quick Questions")
    st.markdown("<div style='margin-bottom: 16px; color: #666;'>Click any question to search:</div>", unsafe_allow_html=True)
    
    # Define quick questions matching the reference image
    quick_questions = [
        {"icon": "💰", "text": "Show me procedures under CHF 5,000", "query": "amount < 5000"},
        {"icon": "⚠️", "text": "Show procedures requiring authorization", "query": "authorization required"},
        {"icon": "📅", "text": "Show procedures updated this month", "query": "valid_after 01/05/2024"},
        {"icon": "🏥", "text": "Show most common procedures", "query": "sort:frequency"}
    ]
    
    # Create styled buttons for each quick question
    for i, q in enumerate(quick_questions):
        if st.button(
            f"{q['icon']} {q['text']}",
            key=f"qq_{i}",
            help=f"Search: {q['query']}",
            use_container_width=True,
            type="secondary"
        ):
            # Store the query and trigger search
            st.session_state.last_query = q['query']
            st.session_state.search_clicked = True
            st.rerun()
    
    # Add divider and about section
    st.markdown("---")
    with st.expander("ℹ️ About this tool", expanded=False):
        st.markdown("""
        This portal helps you find reimbursement information for hospital procedures.
        
        **Features:**
        - Search by procedure name, code, or amount
        - Filter by department or requirements
        - View detailed documentation needs
        - Check for special requirements
        
        Data is updated monthly from official sources.
        """)
        
        # Add a small footer
        st.markdown("---")
        st.caption("v1.0.0 • Last updated: May 2024")

# Add custom CSS for the entire app
st.markdown("""
    <style>
        /* Base styles */
        .main {
            background-color: #f8f9fa;
        }
        
        /* Main container */
        .block-container {
            padding-top: 2rem;
            max-width: 1200px;
        }
        
        /* Header */
        .main-header {
            color: #1a237e;
            font-weight: 600;
            margin-bottom: 1.5rem;
            font-size: 2rem;
            border-bottom: 2px solid #e3f2fd;
            padding-bottom: 0.5rem;
        }
        
        /* Search form */
        .stTextInput>div>div>input {
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            padding: 0.75rem 1rem;
            font-size: 1rem;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #1a73e8;
            box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
        }
        
        /* Buttons */
        .stButton>button {
            border-radius: 8px;
            font-weight: 500;
            padding: 0.5rem 1.5rem;
            transition: all 0.2s;
        }
        
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .stButton>button:active {
            transform: translateY(0);
        }
        
        /* Cards */
        .procedure-card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid #e0e0e0;
            transition: all 0.2s;
        }
        
        .procedure-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #1a237e;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #f8f9fa;
            padding: 1.5rem;
        }
        
        /* Quick question buttons */
        .quick-question-btn {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.75rem;
            text-align: left;
            width: 100%;
            transition: all 0.2s;
            font-size: 0.95rem;
            color: #1a237e;
        }
        
        .quick-question-btn:hover {
            background: #f1f8ff;
            border-color: #1a73e8;
            transform: translateX(4px);
        }
        
        .quick-question-btn:active {
            transform: translateX(0);
        }
        
        .btn-icon {
            margin-right: 8px;
            font-size: 1.1em;
            color: #1a73e8;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .main-header {
                font-size: 1.75rem;
            }
            
            .procedure-card {
                padding: 1.25rem;
            }
        }
        
        /* Status indicators */
        .status-approved {
            color: #0d8a00;
            background-color: #e6f7e6;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .status-pending {
            color: #e6a700;
            background-color: #fff8e6;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)

# Font Awesome Icons
st.markdown('''
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
''', unsafe_allow_html=True)

# Main content
st.markdown("<h1 class='main-header'><i class='fas fa-hospital me-2'></i>Hospital Reimbursement Query Portal</h1>", unsafe_allow_html=True)

# Search functionality
if 'search_clicked' not in st.session_state:
    st.session_state.search_clicked = False

# Process quick question if present
if 'quick_question' in st.session_state and st.session_state.quick_question:
    query = st.session_state.quick_question
    st.session_state.last_query = query
    st.session_state.search_clicked = True
    # Clear it after processing to prevent re-triggering
    del st.session_state.quick_question

# Main search form
with st.form("search_form"):
    # Create two columns for the search box and button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Use the last query if available, otherwise empty
        default_query = st.session_state.get('last_query', '')
        query = st.text_input(
            "Search for procedures, codes, or amounts:",
            value=default_query,
            placeholder="e.g., knee replacement, 27447, >5000",
            label_visibility="collapsed",
            key="search_input"
        )
    
    with col2:
        st.markdown("<div style='height: 29px; display: flex; align-items: flex-end;'>", unsafe_allow_html=True)
        search_clicked = st.form_submit_button("Search", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Check if search was clicked or if we have a search triggered from quick question
    if search_clicked or st.session_state.get('search_clicked'):
        if st.session_state.get('last_query'):
            with st.spinner("Searching..."):
                # Store the search time
                st.session_state.search_time = datetime.now()
                
                try:
                    # Perform the search
                    results, total_matches = st.session_state.bot.search(
                        query=st.session_state.last_query,
                        use_fuzzy=True,
                        threshold=60,
                        top_n=10
                    )
                    
                    # Store results in session state
                    st.session_state.results = results
                    st.session_state.total_matches = total_matches
                    
                except Exception as e:
                    st.error(f"An error occurred during search: {str(e)}")
                finally:
                    # Reset the search_clicked flag
                    if 'search_clicked' in st.session_state:
                        del st.session_state['search_clicked']
        else:
            st.warning("Please enter a search term")

# Display results
def display_results(results: pd.DataFrame, query: str):
    """Display search results in a clean, professional format matching the reference."""
    if results is None or results.empty:
        st.warning("No results found. Try a different search term.")
        return
    
    # Display search info
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;'>
        <h2 style='margin: 0; color: #1a237e;'>Search Results</h2>
        <span style='color: #666; font-size: 0.9rem;'>
            <i class='far fa-clock' style='margin-right: 4px;'></i>
            Processed: {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Display each result as a card
    for _, row in results.iterrows():
        # Format amount with thousand separators and 2 decimal places
        amount = f"{float(row.get('Amount', 0)):,.2f}" if pd.notna(row.get('Amount')) else "N/A"
        
        # Format validity dates
        valid_from = pd.to_datetime(row.get('ValidFrom', '')).strftime('%d/%m/%Y') if pd.notna(row.get('ValidFrom')) else 'N/A'
        valid_until = pd.to_datetime(row.get('ValidUntil', '')).strftime('%d/%m/%Y') if pd.notna(row.get('ValidUntil')) else 'N/A'
        
        # Get documentation items
        docs = []
        if pd.notna(row.get('Documentation')):
            doc_text = str(row['Documentation'])
            docs = [d.strip() for d in doc_text.split('\n') if d.strip()]
        
        # Get exceptions
        exceptions = row.get('Exceptions', '')
        
        # Create the card
        with st.container():
            st.markdown("""
            <div class='procedure-card'>
                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;'>
                    <div>
                        <div style='font-size: 1.25rem; font-weight: 600; color: #1a237e; margin-bottom: 4px;'>
                            {procedure}
                        </div>
                        <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 8px;'>
                            <span style='background: #e3f2fd; color: #0d47a1; padding: 2px 8px; border-radius: 12px; font-size: 0.85rem;'>
                                {code}
                            </span>
                            <span style='color: #666; font-size: 0.9rem;'>
                                <i class='far fa-file-alt' style='margin-right: 4px;'></i>
                                {section_ref}
                            </span>
                        </div>
                        <div style='color: #666; font-size: 0.9rem; margin-bottom: 8px;'>
                            <i class='far fa-calendar-alt' style='margin-right: 4px;'></i>
                            Valid: {valid_from} - {valid_until}
                        </div>
                    </div>
                    <div style='background: #f5f9ff; border-radius: 8px; padding: 12px 16px; text-align: right; min-width: 120px;'>
                        <div style='font-size: 0.85rem; color: #666;'>Amount</div>
                        <div style='font-size: 1.5rem; font-weight: 700; color: #1a73e8;'>
                            CHF {amount}
                        </div>
                    </div>
                </div>
                
                {documentation_section}
                
                {exceptions_section}
            </div>
            """.format(
                procedure=row.get('Procedure', 'N/A'),
                code=row.get('Code', 'N/A'),
                section_ref=row.get('SectionReference', 'N/A'),
                valid_from=valid_from,
                valid_until=valid_until,
                amount=amount,
                documentation_section=f"""
                <div style='margin: 16px 0;'>
                    <div style='font-weight: 600; color: #444; margin-bottom: 8px;'>
                        <i class='fas fa-file-medical' style='margin-right: 6px; color: #1a73e8;'></i>
                        Documentation Requirements:
                    </div>
                    <ul style='margin: 8px 0 0 0; padding-left: 24px; color: #444;'>
                        {" ".join([f'<li style="margin-bottom: 6px;">{doc}</li>' for doc in docs]) if docs else '<li>No specific documentation required</li>'}
                    </ul>
                </div>
                """,
                exceptions_section=f"""
                {f'''
                <div style='background: #fff8e1; border-left: 4px solid #ffc107; padding: 12px; margin: 12px 0; border-radius: 0 4px 4px 0;'>
                    <div style='font-weight: 600; color: #e6a700; margin-bottom: 4px;'>
                        <i class='fas fa-exclamation-triangle' style='margin-right: 6px;'></i>
                        Important Note:
                    </div>
                    <div style='color: #5d4037;'>{exceptions}</div>
                </div>
                ''' if pd.notna(exceptions) and str(exceptions).strip().lower() not in ['', 'nan'] else ''}
                """
            ), unsafe_allow_html=True)
            
            # Add a subtle divider between cards (but not after the last one)
            if _ < len(results) - 1:
                st.markdown("<div style='height: 1px; background: #f0f0f0; margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

if 'results' in st.session_state and st.session_state.results is not None:
    display_results(st.session_state.results, st.session_state.last_query)

# Add some space at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("### About")
st.markdown("""
This portal helps you search and find reimbursement information for hospital procedures.
For assistance, please contact the billing department.
""")

# Custom CSS for better mobile responsiveness
st.markdown("""
    <style>
        /* Main container padding */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        /* Better spacing for mobile */
        @media (max-width: 768px) {
            .stButton>button {
                width: 100%;
                margin: 5px 0;
            }
            .stTextInput>div>div>input {
                font-size: 16px !important; /* Fix for iOS zoom */
            }
        }
        /* Highlight amount boxes */
        .stMetric {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 10px;
            background-color: #f8f9fa;
            text-align: center;
        }
        .stMetric [data-testid="stMetricValue"] {
            font-size: 1.2rem;
            font-weight: bold;
            color: #1f77b4;
        }
        /* Better expander styling */
        .streamlit-expanderHeader {
            font-size: 1.1rem;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)
