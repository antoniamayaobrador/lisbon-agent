from Agent.tools import web_search

def test_search():
    print("Testing web_search tool...")
    query = "Oceanário de Lisboa reviews"
    try:
        result = web_search.invoke(query)
        print(f"Search Result for '{query}':")
        print(result[:500] + "...") # Print first 500 chars
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_search()
