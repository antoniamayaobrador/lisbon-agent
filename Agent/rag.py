import os
import json
import glob
import geopandas as gpd
from typing import List, Dict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from .config import Config

class VectorStoreManager:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=Config.EMBEDDING_MODEL)
        self.vector_store = Chroma(
            persist_directory=Config.CHROMA_DB_DIR,
            embedding_function=self.embeddings,
            collection_name="geospatial_datasets"
        )

    def _extract_metadata(self, file_path: str) -> Dict:
        """Extracts metadata from a GeoJSON, JSON, or Excel file."""
        try:
            # Determine file type and read accordingly
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.xlsx':
                import pandas as pd
                df = pd.read_excel(file_path, nrows=5)
                # Convert to gdf-like structure for consistency if needed, or just extract columns
                columns = list(df.columns)
                geometry_type = ["None (Tabular)"]
                crs = "None"
            else:
                # Read only the first few rows to get schema without loading everything
                gdf = gpd.read_file(file_path, rows=5)
                columns = list(gdf.columns)
                geometry_type = gdf.geom_type.unique().tolist()
                crs = str(gdf.crs)
            
            filename = os.path.basename(file_path)
            category = os.path.basename(os.path.dirname(file_path))
            
            # Use filename for category if generic 'data'
            if category == 'data':
                if 'house' in filename.lower() or 'property' in filename.lower():
                    category = 'housing'
                elif 'street' in filename.lower():
                    category = 'transport'

            
            description = f"Dataset: {filename}\nCategory: {category}\nColumns: {', '.join(columns)}\nGeometry Type: {geometry_type}\nCRS: {crs}"
            
            # Enhance description for boundaries to improve retrieval
            if category == "boundaries" or "freguesia" in filename.lower():
                description += "\nThis dataset contains administrative boundaries, neighborhoods, districts, and freguesias of Lisbon. Use this for spatial filtering by location name (e.g., Avenidas Novas, Belém, etc.)."
            
            # Add category-specific keywords
            category_keywords = {
                "tourism": "restaurants, food, dining, hotels, accommodation, nightlife, bars, clubs",
                "services": "shops, stores, markets, pharmacies, police, schools, universities, malls",
                "transport": "metro, subway, train, bus, tram, stops, stations",
                "culture": "museums, theaters, monuments, art, history, cinemas, galleries, auditoriums, residencies",
                "environment": "parks, gardens, trees, green spaces, nature, noise, air quality, pollution, sound",
                "population": "census, demographics, inhabitants, residents, population density",
                "population": "census, demographics, inhabitants, residents, population density",
                "remarkable_architecture": "architecture, buildings, palaces, churches, religious, noble, monuments, heritage",
                "housing": "houses, property, real estate, prices, cost, cheap, expensive, rent, buy, apartments, residential, home"
            }
            
            if category in category_keywords:
                description += f"\nKeywords: {category_keywords[category]}"

            return {
                "source": file_path,
                "filename": filename,
                "category": category,
                "columns": json.dumps(columns),
                "description": description
            }
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None

    def ingest_metadata(self):
        """Scans data directory and ingests metadata into vector store."""
        print("Scanning data directory...")
        geojson_files = glob.glob(os.path.join(Config.DATA_DIR, "**", "*.geojson"), recursive=True)
        json_files = glob.glob(os.path.join(Config.DATA_DIR, "**", "*.json"), recursive=True)
        xlsx_files = glob.glob(os.path.join(Config.DATA_DIR, "**", "*.xlsx"), recursive=True)
        all_files = geojson_files + json_files + xlsx_files
        
        documents = []
        for file_path in all_files:
            # Skip non-spatial JSONs if any (simple check)
            # We can try to read metadata and if it fails, skip
            metadata = self._extract_metadata(file_path)
            if metadata:
                doc = Document(
                    page_content=metadata["description"],
                    metadata=metadata
                )
                documents.append(doc)
        
        if documents:
            print(f"Ingesting {len(documents)} datasets into vector store...")
            self.vector_store.add_documents(documents)
            print("Ingestion complete.")
        else:
            print("No datasets found to ingest.")

    def retrieve_datasets(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieves relevant datasets based on a query."""
        results = self.vector_store.similarity_search(query, k=k)
        return [doc.metadata for doc in results]

if __name__ == "__main__":
    # Test ingestion
    Config.validate()
    manager = VectorStoreManager()
    manager.ingest_metadata()
