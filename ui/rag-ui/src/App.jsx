import { useState } from "react";
import axios from "axios";

const API = import.meta.env.VITE_API_BASE ?? "http://localhost:8001";

const asText = (err) => {
  if (!err) return "Unknown error";
  if (typeof err === "string") return err;
  if (err.detail) return typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
  try { return JSON.stringify(err); } catch { return "Error"; }
};

export default function App() {
  const [file, setFile] = useState(null);
  const [ingestResult, setIngestResult] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);

  const ingest = async () => {
    if (!file) return alert("Choose a .txt file first");
    const form = new FormData();
    form.append("file", file);
    setIngestResult("Uploading…");
    try {
      const { data } = await axios.post(`${API}/ingest`, form); // let browser set multipart boundary
      setIngestResult(`Inserted chunks: ${data.inserted}`);
    } catch (e) {
      console.error(e);
      setIngestResult(asText(e?.response?.data || e.message));
    }
  };

  const ask = async () => {
    if (!question.trim()) return;
    setAnswer("Thinking…");
    setSources([]);
    try {
      const { data } = await axios.post(`${API}/ask`, { question });
      setAnswer(data.answer || "(empty)");
      setSources(data.sources || []);
    } catch (e) {
      console.error(e);
      setAnswer("Error: " + asText(e?.response?.data || e.message));
    }
  };

  return (
    <div style={{ maxWidth: 760, margin: "2rem auto", fontFamily: "Inter, system-ui, sans-serif" }}>
      <h1>RAG Lab UI</h1>

      <section style={{ padding: "1rem", border: "1px solid #eee", borderRadius: 12, marginBottom: 16 }}>
        <h2>1) Ingest a text file</h2>
        <input type="file" accept=".txt,.md" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button onClick={ingest} style={{ marginLeft: 8 }}>Ingest</button>
        <div style={{ marginTop: 8, color: "#555" }}>{ingestResult}</div>
      </section>

      <section style={{ padding: "1rem", border: "1px solid #eee", borderRadius: 12 }}>
        <h2>2) Ask a question</h2>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What is PageRank?"
          style={{ width: "100%", padding: 8, marginBottom: 8 }}
        />
        <button onClick={ask}>Ask</button>

        <h3 style={{ marginTop: 16 }}>Answer</h3>
        <pre style={{ whiteSpace: "pre-wrap" }}>{answer}</pre>

        {!!sources.length && (
          <>
            <h4>Sources</h4>
            <ul>{sources.map((s, i) => <li key={i}>{s}</li>)}</ul>
          </>
        )}
      </section>
    </div>
  );
}
