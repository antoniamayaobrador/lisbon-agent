# Geospatial AI Agent for Real Estate

## Project Overview

This project is a proof-of-concept for a **Geospatial AI Agent** designed to revolutionize how we interact with urban data. It serves as a testbed for integrating Large Language Models (LLMs) with geospatial analysis tools, specifically targeting the **Real Estate** sector.

The core mission is to bridge the gap between complex geospatial data (GeoJSONs, street networks, administrative boundaries) and natural language questions. Instead of writing SQL or Python code, a user can simply ask: *"Where is the cheapest apartment near a metro station?"* and the agent handles the rest.

## Business Case

In the competitive real estate market, location is everything. However, location data is often siloed and difficult to analyze without technical expertise. This agent demonstrates how AI can:
-   **Democratize Data Access**: Allow non-technical stakeholders (agents, investors) to query complex datasets.
-   **Accelerate Decision Making**: Instantly answer proximity and affordability questions.
-   **Uncover Hidden Insights**: correlate noise levels, transport accessibility, and housing prices dynamically.

## Why This Project is Great

-   **Autonomous Reasoning**: It doesn't just look up data; it *plans* an analysis. If you ask for specific streets, it knows to fetch fresh data from OpenStreetMap.
-   **Tool-Use Capabilities**: It leverages a suite of specialized tools (`geopandas`, `osmnx`) to perform rigorous spatial operations (joins, nearest neighbor searches) rather than hallucinating answers.
-   **Synthetic Data Engine**: Includes a robust generator for synthetic housing data, complete with realistic pricing models and real street addresses, enabling stress-free testing and demonstrations.
-   **Visual Output**: Capable of generating plots and maps on the fly to visualize trends and locations.

## Features

-   **Context-Aware Retrieval (RAG)**: Automatically selects the most relevant datasets (tourism, noise, boundaries) for any query.
-   **Street-Sensitive Analysis**: Integrated with **OpenStreetMap** to understand street networks, walkability, and exact locations.
-   **Advanced Spatial Queries**:
    -   *Proximity*: "Find art galleries within 500m."
    -   *Containment*: "Which freguesia has the most museums?"
    -   *Affordability*: "Rank areas by price per square meter."
-   **Interactive Interface**: A clean, Gradio-based chat UI for easy interaction.

## Future Roadmap

To evolve this from a prototype to a production-ready system, the following features are envisioned:
-   **3D Visualization**: Integrate with Cesium or Mapbox GL for immersive 3D city views.
-   **Real-Time Data**: Connect to live APIs for transit schedules, traffic, and real estate listings.
-   **Predictive Modeling**: Incorporate scikit-learn models to predict future property prices based on urban indicators.
-   **Multi-Modal Inputs**: Allow users to upload their own GeoJSONs or images of maps for analysis.

---

## Technical Setup & Usage

### 1. Installation
```bash
pip install -r requirements.txt
pip install osmnx
```

### 2. Configuration
Create a `.env` file with your API key:
```
OPENAI_API_KEY=sk-...
```

### 3. Data Ingestion
Initialize the knowledge base:
```bash
python -m Agent.rag
```

### 4. Running the Agent
Launch the web interface:
```bash
python -m Agent.interface
```
Access at `http://localhost:7860`.

### 5. Synthetic Data Tools
-   **Generate Houses**: `python generate_houses.py`
-   **Add Addresses**: `python add_addresses.py`

## Architecture
-   **LangGraph**: Orchestrates the decision-making loop.
-   **ChromaDB**: Vector store for dataset metadata.
-   **OSMnx**: Street network data provider.
-   **Gradio**: Frontend interface.
