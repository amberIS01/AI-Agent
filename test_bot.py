from bot import HospitalReimbursementBot

def test_search():
    print("Testing Hospital Reimbursement Bot...")
    
    # Initialize the bot
    bot = HospitalReimbursementBot("data")
    
    # Load data
    print("\nLoading data...")
    data = bot.load_data()
    
    if data is None or data.empty:
        print("No data loaded. Please check the data folder.")
        return
        
    print(f"Loaded {len(data)} records.")
    
    # Process data
    print("\nProcessing data...")
    processed_data = bot.process_data()
    
    if processed_data is None or processed_data.empty:
        print("No data available after processing.")
        return
    
    # Test search
    print("\n=== Testing Search Functionality ===")
    
    # Test 1: Exact search
    print("\nTest 1: Exact search for 'knee'")
    results, total = bot.search("knee", use_fuzzy=False)
    print("\nSearch Results (Exact):")
    print(results.head() if not results.empty else "No results found")
    
    # Test 2: Fuzzy search
    print("\nTest 2: Fuzzy search for 'hip replace'")
    results, total = bot.search("hip replace", use_fuzzy=True)
    print("\nSearch Results (Fuzzy):")
    print(results.head() if not results.empty else "No results found")
    
    # Test 3: No match
    print("\nTest 3: Search for 'xyz123' (should return no results)")
    results, total = bot.search("xyz123", use_fuzzy=True)
    print("\nSearch Results:")
    print("No results found" if results.empty else results.head())

if __name__ == "__main__":
    test_search()
