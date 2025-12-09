from Agent.rag import VectorStoreManager
from Agent.config import Config

def test_boundary_retrieval():
    Config.validate()
    rag = VectorStoreManager()
    
    # Test with a query that SHOULD retrieve boundaries
    queries = [
        "freguesias in Lisbon",
        "administrative boundaries",
        "Avenidas Novas",
        "restaurants in Avenidas Novas"
    ]
    
    for q in queries:
        print(f"\nQuery: '{q}'")
        results = rag.retrieve_datasets(q, k=10)
        found = any("freguesias" in r['filename'] for r in results)
        print(f"Found freguesias? {found}")
        for r in results:
            if "freguesias" in r['filename']:
                print(f"  - MATCH: {r['filename']}")
                print(f"  - Description: {r['description']}")

if __name__ == "__main__":
    test_boundary_retrieval()
