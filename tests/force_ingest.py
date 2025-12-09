from Agent.rag import VectorStoreManager
from langchain_core.documents import Document
import os

manager = VectorStoreManager()
file_path = os.path.abspath("data/synthetic_houses.geojson")
meta = manager._extract_metadata(file_path)

if meta:
    print("Ingesting synthetic houses metadata directly...")
    doc = Document(page_content=meta["description"], metadata=meta)
    
    # Add to vector store
    manager.vector_store.add_documents([doc])
    print("Done.")
else:
    print("Failed to extract metadata.")
