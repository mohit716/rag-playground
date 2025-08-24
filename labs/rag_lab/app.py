from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
from common.text import chunk
import requests
import os
from fastapi.middleware.cors import CORSMiddleware

# ---- App & CORS ----
app = FastAPI(title="RAG Lab")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Config ----
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMB_MODEL = os.getenv("EMB_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")  # change via env to try others

# ---- Vector store ----
client = chromadb.PersistentClient(path="labs/rag_lab/.chroma")
collection = client.get_or_create_collection("docs")

# ---- Embeddings ----
embedder = SentenceTransformer(EMB_MODEL)

class Ask(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"ok": True, "model": OLLAMA_MODEL}

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """
    Upload a text file, split into chunks, embed, and store in Chroma.
    """
    text = (await file.read()).decode("utf-8", errors="ignore")
    chunks = chunk(text)
    embs = embedder.encode(chunks, show_progress_bar=False).tolist()
    ids = [f"{file.filename}-{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embs,
        metadatas=[{"source": file.filename}] * len(chunks),
    )
    return {"inserted": len(chunks)}

@app.post("/ask")
async def ask(payload: Ask):
    """
    Ask a question, retrieve top-k chunks, pass them to Ollama for answer.
    """
    query = payload.question
    q_emb = embedder.encode([query]).tolist()[0]
    res = collection.query(query_embeddings=[q_emb], n_results=4)

    docs = res.get("documents", [])
    context = "\n\n".join(docs[0]) if docs and docs[0] else ""

    prompt = f"""
You are a helpful assistant. Use the CONTEXT to answer concisely and cite sources by filename.

QUESTION: {query}
CONTEXT:
{context}
"""

    # Non-streaming call → clean single JSON; surface Ollama errors clearly
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama connection error: {e}")

    if not r.ok:
        # Return Ollama's body so the UI shows the real cause (e.g., bad tag, OOM)
        raise HTTPException(status_code=502, detail=f"Ollama {r.status_code}: {r.text}")

    try:
        resp = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail=f"Ollama returned non-JSON: {r.text[:300]}")

    answer = (resp.get("response") or "").strip()

    sources = [m.get("source") for m in res.get("metadatas", [[]])[0]] if res.get("metadatas") else []
    sources = list(dict.fromkeys([s for s in sources if s]))

    return {"answer": answer, "sources": sources}

@app.get("/llm_test")
def llm_test():
    """
    Quick probe: ask Ollama 'ping' with current OLLAMA_MODEL.
    """
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": "ping", "stream": False},
            timeout=60,
        )
        ok = r.ok
        body = r.text
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama connection error: {e}")

    if not ok:
        raise HTTPException(status_code=502, detail=f"Ollama {r.status_code}: {body}")

    return {"ok": True, "model": OLLAMA_MODEL}
