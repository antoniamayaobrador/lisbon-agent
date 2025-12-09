import argparse
import uvicorn
from Agent.config import Config
from Agent.rag import VectorStoreManager

def main():
    parser = argparse.ArgumentParser(description="Launch the Geospatial Agent")
    parser.add_argument("--ingest", action="store_true", help="Ingest metadata into vector store")
    parser.add_argument("--api", action="store_true", help="Run the API server")
    parser.add_argument("--ui", action="store_true", help="Run the Gradio UI")
    
    args = parser.parse_args()
    
    # Validate config
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return

    if args.ingest:
        print("Starting ingestion...")
        manager = VectorStoreManager()
        manager.ingest_metadata()
        print("Ingestion complete.")
        
    if args.api:
        print("Starting API server...")
        uvicorn.run("Agent.api:app", host="0.0.0.0", port=8000, reload=True)
        
    if args.ui:
        print("Starting Gradio UI...")
        # Import here to avoid issues if dependencies aren't fully set up when just ingesting
        from Agent.interface import demo
        demo.launch(server_name="0.0.0.0", server_port=7860)

    if not (args.ingest or args.api or args.ui):
        print("No action specified. Use --ingest, --api, or --ui.")
        parser.print_help()

if __name__ == "__main__":
    main()
