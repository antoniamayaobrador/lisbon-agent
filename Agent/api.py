from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .graph import app as agent_app
from .observability import Observability
from langchain_core.messages import HumanMessage
import uuid

app = FastAPI(title="Geospatial Agent API")

class QueryRequest(BaseModel):
    question: str

class RatingRequest(BaseModel):
    run_id: str
    rating: int
    comment: str = ""

@app.post("/query")
async def query_agent(request: QueryRequest):
    run_id = str(uuid.uuid4())
    try:
        inputs = {"messages": [HumanMessage(content=request.question)]}
        result = agent_app.invoke(inputs)
        answer = result["messages"][-1].content
        
        # Log the run
        Observability.log_step("api_request", {"question": request.question}, {"answer": answer, "run_id": run_id})
        
        return {"answer": answer, "run_id": run_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rate")
async def rate_run(request: RatingRequest):
    try:
        Observability.save_rating(request.run_id, request.rating, request.comment)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
