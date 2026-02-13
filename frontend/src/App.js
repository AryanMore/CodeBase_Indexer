import React, { useState } from "react";

import Landing from "./components/Landing";
import Chat from "./components/Chat";

import { apiGet, apiPost } from "./services/api";

import "./styles/main.css";


function App() {

  const [page, setPage] = useState("landing");

  const [repoUrl, setRepoUrl] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);


  // ================= NAVIGATION =================

  const goBack = () => {
    setPage("landing");
    setMessages([]);
    setQuestion("");
    setStatus("");
  };


  // ================= INGEST =================

  const ingestRepo = async () => {

    if (!repoUrl.trim()) {
      setStatus("Repository URL required");
      return;
    }

    setLoading(true);
    setStatus("Indexing repository...");
    try {

      await apiPost("/ingest", {
        repo_url: repoUrl
      });

      setPage("chat");

    } catch {

      setStatus("Ingestion failed");

    }

    setLoading(false);
  };


  // ================= USE EXISTING =================

  const useExisting = async () => {

    setLoading(true);
    setStatus("");

    try {

      const data = await apiGet("/has_index");

      if (!data.has_index) {
        setStatus("No index found");
        setLoading(false);
        return;
      }

      setPage("chat");

    } catch {

      setStatus("Backend not reachable");

    }

    setLoading(false);
  };


  // ================= CHAT =================

  const sendQuestion = async () => {

    if (!question.trim()) return;

    setMessages(prev => [
      ...prev,
      { text: question, sender: "user" }
    ]);

    setQuestion("");

    try {

      const data = await apiPost("/query", {
        question
      });

      setMessages(prev => [
        ...prev,
        { text: data.answer, sender: "bot" }
      ]);

    } catch {

      setMessages(prev => [
        ...prev,
        {
          text: "Server error",
          sender: "bot"
        }
      ]);
    }
  };


  // ================= UI =================

  return (

    <div className="app-container">

      {page === "landing" && (

        <Landing
          repoUrl={repoUrl}
          setRepoUrl={setRepoUrl}
          ingestRepo={ingestRepo}
          useExisting={useExisting}
          loading={loading}
          status={status}
        />

      )}


      {page === "chat" && (

        <Chat
          messages={messages}
          question={question}
          setQuestion={setQuestion}
          sendQuestion={sendQuestion}
          goBack={goBack}   // 👈 NEW
        />

      )}

    </div>
  );
}

export default App;
