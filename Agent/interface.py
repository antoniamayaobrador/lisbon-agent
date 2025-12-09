import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import gradio as gr
import requests
import json
from .config import Config

API_URL = "http://localhost:8000"

def query_agent(message, history):
    try:
        # In a real scenario, we'd call the API. 
        # For local demo simplicity, we can also import the graph directly if we want to avoid running separate processes.
        # But let's stick to the plan and assume the API is running or we use the graph directly.
        # To make it easier for the user to run just one script, I'll import the graph directly here too.
        from .graph import app as agent_app
        from langchain_core.messages import HumanMessage
        
        inputs = {"messages": [HumanMessage(content=message)]}
        result = agent_app.invoke(inputs)
        answer = result["messages"][-1].content
        return answer
    except Exception as e:
        return f"Error: {e}"

def rate_answer(rating, comment):
    # This would typically send to the API or save locally
    # For now, let's just save locally using Observability
    from .observability import Observability
    import uuid
    # We don't have the run_id easily here without state, so we'll generate a dummy one or handle it better in a full app
    run_id = str(uuid.uuid4()) 
    Observability.save_rating(run_id, rating, comment)
    return "Rating saved!"

with gr.Blocks(title="Geospatial Agent") as demo:
    gr.Markdown("# Geospatial LangGraph Agent")
    gr.Markdown("Ask questions about Lisboa's geospatial data.")
    
    chatbot = gr.ChatInterface(fn=query_agent)
    
    with gr.Row():
        rating = gr.Slider(minimum=1, maximum=5, step=1, label="Rate the last answer")
        comment = gr.Textbox(label="Comment")
        submit_rating = gr.Button("Submit Rating")
        rating_status = gr.Label()
    
    submit_rating.click(rate_answer, inputs=[rating, comment], outputs=[rating_status])

if __name__ == "__main__":
    Config.validate()
    # Allow access to the data directory for serving plots
    import os
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    demo.launch(server_name="0.0.0.0", server_port=7860, allowed_paths=[data_dir])
