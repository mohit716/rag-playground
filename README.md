# AI Playground — RAG Lab (FastAPI + Chroma + Ollama) + Minimal React UI

A small, local-first RAG demo you can run on Windows with **Ollama** and a lightweight React UI.


---

## Features
- **Backend**: FastAPI API with endpoints:
  - `POST /ingest` — upload a text file; chunks are embedded and stored to Chroma
  - `POST /ask` — retrieve relevant chunks and generate an answer via Ollama
  - `GET /llm_test` — quick health probe for current model
- **Vector store**: Chroma (local, persisted under `labs/rag_lab/.chroma`)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **LLM**: Ollama (default model configurable; tested with `dolphin-phi:latest` and `gemma3:4b`)
- **Frontend**: Vite + React (file upload + ask/answer UI)
- **CORS enabled** for local dev (5173 ⇄ 8001)

---

## Architecture
```
React UI (Vite, axios)
      ↓
FastAPI (CORS)  ——→ Chroma (vector DB)
      ↓
Ollama (model picked by OLLAMA_MODEL)
```
Embedding model encodes documents & query; Chroma returns relevant chunks; the prompt plus context is sent to Ollama; the answer is returned with source filenames.

---

## Prerequisites
- **Windows + PowerShell**
- **Python 3.10+**
- **Node 18+** (for the UI)
- **Ollama** installed and running (defaults to `http://localhost:11434`)

Check models you have:
```powershell
ollama list
```
If RAM is tight, prefer **dolphin-phi:latest**, **gemma:2b**, or **phi3:mini**.

---

## Backend — Setup & Run
From project root:
```powershell
cd C:\Users\mohit\OneDrive\Desktop\ai-playground

# one-time: create venv
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# install requirements
pip install -r labs\rag_lab\requirements.txt

# run server
python -m uvicorn labs.rag_lab.app:app --reload --port 8001
```
Open FastAPI docs: http://localhost:8001/docs  
Health probe: http://localhost:8001/llm_test

### Switch the Ollama model (without code change)
```powershell
Ctrl + C  # stop server if running
$env:OLLAMA_MODEL="dolphin-phi:latest"
python -m uvicorn labs.rag_lab.app:app --reload --port 8001
```

> If you see an Ollama 500 with “requires more system memory”, close apps to free RAM or switch to a smaller model.

---

## Frontend — Setup & Run
```powershell
cd C:\Users\mohit\OneDrive\Desktop\ai-playground\ui\rag-ui
npm install
# ensure .env contains: VITE_API_BASE=http://localhost:8001
npm run dev
```
Open React app: http://localhost:5173

**Test flow:**
1) Click **Browse…** and pick a `.txt` file (example in `data/mini-wiki.txt`).
2) Click **Ingest** → see “Inserted chunks: N”.
3) Type a question (e.g., *What is PageRank?*) → **Ask** → see answer + sources.

---

## Project Tree
```
ai-playground/
├─ common/
│  ├─ __init__.py
│  └─ text.py
├─ labs/
│  └─ rag_lab/
│     ├─ __init__.py
│     ├─ app.py
│     ├─ requirements.txt
│     └─ .chroma/           # generated at runtime
├─ data/                    # your local files (ignored by git)
├─ ui/
│  └─ rag-ui/
│     ├─ .env               # VITE_API_BASE=http://localhost:8001
│     ├─ package.json
│     ├─ index.html
│     └─ src/
│        ├─ App.jsx
│        └─ main.jsx
└─ .gitignore
```

---

## Troubleshooting
- **UI says “Network Error” on Ingest**: CORS or wrong API base. Backend must include `CORSMiddleware`, and `ui/rag-ui/.env` must have `VITE_API_BASE=http://localhost:8001`.
- **502 on /ask**: the backend is up but Ollama failed. Check `/llm_test`. Often a **model tag** or **not enough RAM**.
- **Ollama memory error**: use a smaller model:  
  ```powershell
  $env:OLLAMA_MODEL="dolphin-phi:latest"
  # or gemma:2b / phi3:mini / qwen2:1.5b
  ```
- **Reset vector DB**:
  ```powershell
  # stop server first
  Remove-Item -Recurse -Force .\labs\rag_lab\.chroma
  ```


