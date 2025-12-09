from Agent.config import Config
from Agent.rag import VectorStoreManager
from Agent.graph import app
from langchain_core.messages import HumanMessage

def test_agent():
    print("Validating config...")
    Config.validate()
    
    print("Initializing RAG...")
    rag = VectorStoreManager()
    # Uncomment to ingest if needed, but assuming it's done or we do it once
    # rag.ingest_metadata() 
    
    print("Running test query...")
    query = "restaurants in Avenidas Novas"
    inputs = {"messages": [HumanMessage(content=query)]}
    
    try:
        result = app.invoke(inputs)
        answer = result["messages"][-1].content
        print(f"Query: {query}")
        print(f"Answer: {answer}")
    except Exception as e:
        print(f"Error running agent: {e}")

if __name__ == "__main__":
    test_agent()
