from Agent.tools import web_search

def test_search():
    print("Testing web_search tool...")
    queries = ["Pizza Hut Avenidas Novas menu", "History of Lisbon", "Saraiva Portuguese restaurant"]
    
    for q in queries:
        print(f"\n--- Query: {q} ---")
        try:
            result = web_search.invoke(q)
            print(f"Result (first 200 chars): {result[:200]}...")
            if not result or "Error" in result:
                print(f"FAILURE TAG: {result}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_search()
