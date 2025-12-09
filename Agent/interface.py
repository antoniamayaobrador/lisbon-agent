import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import gradio as gr
import requests
import json
from .config import Config

API_URL = "http://localhost:8000"

async def query_agent(message, history):
    try:
        from .graph import app as agent_app
        from langchain_core.messages import HumanMessage
        
        inputs = {"messages": [HumanMessage(content=message)]}
        
        # Use astream_events to catch token streaming from the LLM
        # We look for "on_chat_model_stream" events.
        final_answer = ""
        
        async for event in agent_app.astream_events(inputs, version="v1"):
            kind = event["event"]
            
            # Streaming LLM tokens
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content
                if content:
                    if isinstance(content, list):
                        # Handle list content (e.g. from complex tool calls or reasoning models)
                        for item in content:
                            if isinstance(item, str):
                                final_answer += item
                            elif isinstance(item, dict) and "text" in item:
                                final_answer += item["text"]
                    else:
                        final_answer += str(content)
                    
                    yield final_answer
                    
            # Optional: Intermediate status updates on tool usage?
            # if kind == "on_tool_start":
            #     yield final_answer + f"\n\n*Using tool: {event['name']}...*"
            
    except Exception as e:
        yield f"Error: {e}"

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
