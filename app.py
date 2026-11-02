import asyncio
import json
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llm_factory import PROVIDERS_CONFIG, verify_llm_credentials
from screener_engine import run_screening_orchestrator

app = FastAPI(
    title="Crypto Volatility Screener & AI Technical Analyst",
    description="Multi-Provider Crypto Screener with Live Browser Agent",
    version="2.0.0"
)

# Restrict CORS to trusted local origins
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [
    origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()
]
if not allowed_origins:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# In-memory storage for active tasks & Concurrency Lock
active_tasks: Dict[str, Dict[str, Any]] = {}
screening_lock = asyncio.Lock()

class ScreenRequest(BaseModel):
    provider: str = "google"
    model: str = "gemini-3.8-flash"
    api_key: Optional[str] = None
    headed: bool = False

class VerifyKeyRequest(BaseModel):
    provider: str = "google"
    model: str = "gemini-3.8-flash"
    api_key: str

def validate_provider(provider: str):
    p = provider.lower().strip()
    if p not in PROVIDERS_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider '{provider}'. Allowed: {list(PROVIDERS_CONFIG.keys())}"
        )

@app.get("/api/models")
async def get_models():
    """Returns available providers and 2026 model configurations."""
    return {
        "providers": PROVIDERS_CONFIG
    }

@app.post("/api/verify-model")
async def verify_model(req: VerifyKeyRequest):
    """Verifies that the provided API key & model work and have active quota."""
    validate_provider(req.provider)
    if not req.api_key or len(req.api_key.strip()) < 5:
        raise HTTPException(status_code=400, detail="API key is required.")
        
    res = await verify_llm_credentials(
        provider=req.provider,
        model=req.model,
        api_key=req.api_key.strip()
    )
    return res

@app.post("/api/screen")
async def start_screening(req: ScreenRequest):
    """
    Initiates a new screening job. Returns task_id to listen to via SSE stream.
    Enforces single-job concurrency to prevent local resource exhaustion.
    """
    validate_provider(req.provider)
    
    # Check if a screening job is already actively running
    if screening_lock.locked():
        raise HTTPException(
            status_code=409,
            detail="A screening task is already in progress. Please wait for it to complete."
        )
        
    task_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    
    active_tasks[task_id] = {
        "queue": queue,
        "status": "running"
    }
    
    async def emit_callback(event: Dict[str, Any]):
        await queue.put(event)
        
    async def task_runner():
        async with screening_lock:
            try:
                await run_screening_orchestrator(
                    provider=req.provider,
                    model=req.model,
                    api_key=req.api_key,
                    headed=req.headed,
                    emit_callback=emit_callback
                )
            except Exception as e:
                await emit_callback({
                    "type": "error",
                    "message": f"Orchestrator error: {str(e)}"
                })
            finally:
                if task_id in active_tasks:
                    active_tasks[task_id]["status"] = "finished"
                # Signal end of stream
                await queue.put({"type": "__END__"})
                
                # Delayed auto-cleanup after 60s if client disconnected or abandoned
                async def delayed_cleanup():
                    await asyncio.sleep(60)
                    active_tasks.pop(task_id, None)
                asyncio.create_task(delayed_cleanup())

    # Launch task asynchronously in the background
    asyncio.create_task(task_runner())
    
    return {
        "task_id": task_id,
        "message": "Screening job started. Connect to /api/stream/{task_id} for live updates."
    }

@app.get("/api/stream/{task_id}")
async def stream_task_events(task_id: str, request: Request):
    """
    Server-Sent Events (SSE) endpoint to stream real-time updates for a task.
    """
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_info = active_tasks[task_id]
    queue: asyncio.Queue = task_info["queue"]
    
    async def event_generator():
        try:
            while True:
                # Disconnect check
                if await request.is_disconnected():
                    break
                    
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25.0)
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment
                    yield ": ping\n\n"
                    continue
                    
                if isinstance(event, dict) and event.get("type") == "__END__":
                    break
                    
                data_json = json.dumps(event)
                yield f"data: {data_json}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup finished task after streaming
            if task_id in active_tasks and active_tasks[task_id]["status"] == "finished":
                active_tasks.pop(task_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/")
async def root():
    """Returns API service status and discovery endpoints."""
    return {
        "status": "online",
        "service": "Crypto Volatility Screener & AI Analyst API",
        "version": "2.0.0",
        "docs": "/docs",
        "models": "/api/models"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
