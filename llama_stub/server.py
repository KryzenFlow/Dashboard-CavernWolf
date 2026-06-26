"""LLaMA stub — llama.cpp-compatible /completion for default docker compose stack."""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="LLaMA Stub Service")


class CompletionRequest(BaseModel):
    prompt: str = ""
    n_predict: int = 128


@app.get("/health")
def health():
    return {"status": "ok", "service": "llama-stub"}


@app.post("/completion")
def completion(req: CompletionRequest):
    text = (
        f"[llama-stub] Simulated completion for: {req.prompt[:300]}"
        if req.prompt
        else "[llama-stub] Ready."
    )
    return {"content": text, "response": text}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
