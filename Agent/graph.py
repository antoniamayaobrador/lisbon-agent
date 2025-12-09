from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .rag import VectorStoreManager
from .tools import load_geojson, spatial_join, attribute_join, analyze_data, find_nearest, get_street_network, web_search
from .observability import Observability
from .config import Config
import json
import operator

# Define State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    relevant_datasets: List[dict]
    final_answer: str

# Initialize components
llm = ChatOpenAI(model=Config.MODEL_NAME, temperature=0)
rag = VectorStoreManager()

# Define Nodes
def retrieve_node(state: AgentState):
    """Retrieves relevant datasets based on the last user message."""
    last_message = state["messages"][-1].content
    datasets = rag.retrieve_datasets(last_message)
    
    # Force retrieval of boundaries to ensure spatial context
    boundary_datasets = rag.retrieve_datasets("administrative boundaries of Lisbon", k=2)
    
    # Force retrieval of POIs (restaurants, shops) to ensure we have data for location searches
    # This addresses the issue where specific place names (e.g. "Casinha dos Doces") don't trigger retrieval
    poi_datasets = rag.retrieve_datasets("restaurants cafes shops hotels", k=3)
    
    # Force retrieval of culture datasets to ensure comprehensive analysis
    culture_datasets = rag.retrieve_datasets("museums theaters cinemas galleries art", k=5)
    
    # Force retrieval of other domains for cross-domain analysis
    # Split to ensure noise isn't crowded out by many environment files
    general_datasets = rag.retrieve_datasets("environment air quality population architecture", k=5)
    noise_datasets = rag.retrieve_datasets("noise sound pollution", k=10)
    
    # Force retrieval of housing/property datasets
    housing_datasets = rag.retrieve_datasets("housing property prices real estate apartment", k=5)
    
    # Combine and deduplicate based on filename
    seen_files = set(d['filename'] for d in datasets)
    for d in boundary_datasets + poi_datasets + culture_datasets + general_datasets + noise_datasets + housing_datasets:
        if d['filename'] not in seen_files:
            datasets.append(d)
            seen_files.add(d['filename'])
            
    Observability.log_step("retrieve", {"query": last_message}, {"datasets": [d['filename'] for d in datasets]})
    return {"relevant_datasets": datasets}

def agent_node(state: AgentState):
    """Decides on tools to call or generates an answer."""
    messages = state["messages"]
    datasets = state.get("relevant_datasets", [])
    
    dataset_context = "\n".join([f"- {d['filename']} (Path: {d['source']}): {d['description']}" for d in datasets])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a geospatial analysis agent. 
        You have access to the following datasets:
        {dataset_context}
        
        Your goal is to answer the user's question using the provided tools.
        
        **Tools Usage Guidelines:**
        1. `load_geojson`: Use to inspect a dataset.
        2. `spatial_join` / `attribute_join`: Use to combine datasets. These tools return a NEW file path. Use this path for subsequent steps.
        3. `find_nearest`: Use to find the closest features from one dataset to another (e.g., closest restaurant to a station).
        4. `get_street_network`: Use to fetch fresh street data for a place.
        5. `web_search`: Use to find qualitative info (reviews, ratings, opening hours, facts) or when you need data not in your datasets. 
        6. `analyze_data`: Use to perform calculations, filtering, aggregations, OR PLOTTING.
           - You must write valid Python code (pandas/geopandas/matplotlib).
           - The dataframe is available as `gdf`.
           - You MUST assign your final answer to the variable `result`.
           - **Plotting**: If the user asks for a plot OR if the question involves spatial distribution/locations (e.g., "Where are...", "Show me...", "Count..."), YOU SHOULD GENERATE A PLOT unless explicitly told not to.
           - Use `gdf.plot()` or `plt.plot()`. 
           - **CRITICAL**: Save the figure to `plot_path` (variable provided to you) using `plt.savefig(plot_path)`. 
           - Set `result` to the string "Plot saved to " + plot_path.
           - Example Analysis: `result = gdf[gdf['pop'] > 1000].count()`
           - Example Plot: 
             ```python
             ax = gdf.plot(figsize=(10, 10), edgecolor='black')
             plt.title("Distribution of X")
             plt.axis('off')
             plt.savefig(plot_path)
             result = plot_path
             ```
        
        **Strategy:**
        - Break down complex questions into steps.
        - If you need to join data, do that first, then analyze the resulting file.
        - To find "closest X to Y":
            a. Filter Y to the specific feature (using `analyze_data`).
            b. Use `find_nearest` with the filtered Y and the full X dataset.
        - Always check the column names returned by tools to write correct analysis code.
        - **Visuals**: Always try to visualize the result if it's geospatial.
        """),
        ("placeholder", "{messages}"),
    ])
    
    tools = [load_geojson, spatial_join, attribute_join, analyze_data, find_nearest, get_street_network, web_search]
    agent = prompt | llm.bind_tools(tools)
    
    response = agent.invoke({"messages": messages, "dataset_context": dataset_context})
    
    # Check if response contains a plot path and format it as markdown image
    content = response.content
    if "data/plots/" in content and ".png" in content:
        # Simple heuristic to detect plot path in text and ensure it's displayed
        # If the agent just returns the path, we wrap it. 
        # If it already wrapped it, this might be redundant but harmless if we just append.
        # Better: let the agent handle it via instructions, but we can enforce it here.
        # Extract the path using regex or simple string manipulation
        import re
        # Look for "data/plots/..." pattern
        match = re.search(r'(data/plots/[^\s\n"]+\.png)', content)
        if match:
            plot_path = match.group(1)
            # Append markdown image syntax if not already present
            if f"![" not in content:
                response.content += f"\n\n![Generated Plot]({plot_path})" 
        
    Observability.log_step("agent", {"messages": [m.content for m in messages]}, {"response": response.content})
    
    return {"messages": [response]}

def tool_node(state: AgentState):
    """Executes tools called by the agent."""
    last_message = state["messages"][-1]
    
    if not last_message.tool_calls:
        return {}
    
    tool_map = {
        "load_geojson": load_geojson,
        "spatial_join": spatial_join,
        "attribute_join": attribute_join,
        "analyze_data": analyze_data,
        "find_nearest": find_nearest,
        "get_street_network": get_street_network,
        "web_search": web_search
    }
    
    responses = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_func = tool_map.get(tool_name)
        
        if tool_func:
            result = tool_func.invoke(tool_args)
            responses.append(
                {"tool_call_id": tool_call["id"], "name": tool_name, "content": str(result)}
            )
            Observability.log_step("tool_execution", {"tool": tool_name, "args": tool_args}, {"result": result})

    # Convert tool responses to ToolMessages (simplified for this custom node, 
    # but in standard LangGraph we'd use ToolMessage)
    from langchain_core.messages import ToolMessage
    tool_messages = [ToolMessage(tool_call_id=r["tool_call_id"], content=r["content"], name=r["name"]) for r in responses]
    
    return {"messages": tool_messages}

def should_continue(state: AgentState):
    """Determines if the agent should continue or end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

app = workflow.compile()
