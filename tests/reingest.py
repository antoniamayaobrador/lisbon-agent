from Agent.rag import VectorStoreManager
from Agent.config import Config

if __name__ == "__main__":
    Config.validate()
    print("Re-ingesting metadata with improved descriptions...")
    manager = VectorStoreManager()
    manager.ingest_metadata()
    print("Ingestion complete.")
