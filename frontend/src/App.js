import React, { useState } from "react";

import Landing from "./components/Landing";
import Chat from "./components/Chat";

import { apiGet, apiPost, apiAgentQuery } from "./services/api";

import "./styles/main.css";


function App() {

  const [page, setPage] = useState("landing");

  const [repoUrl, setRepoUrl] = useState(
    "https://github.com/khushb-glide/GitHub-Repo-Doc-Bot"
  );
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [useAgent, setUseAgent] = useState(true);
  const [agentSessionId, setAgentSessionId] = useState(null);


  // ================= NAVIGATION =================

  const goBack = () => {
    setPage("landing");
    setMessages([]);
    setQuestion("");
    setStatus("");
    setAgentSessionId(null);
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

    const currentQuestion = question;

    setMessages(prev => [
      ...prev,
      { text: currentQuestion, sender: "user" }
    ]);

    setQuestion("");

    try {

      if (useAgent) {
        const data = await apiAgentQuery(repoUrl, currentQuestion, agentSessionId);
        if (data.session_id) {
          setAgentSessionId(data.session_id);
        }

        setMessages(prev => [
          ...prev,
          {
            text: data.answer,
            sender: "bot"
          }
        ]);

        return;
      }

      const data = await apiPost("/query", {
        question: currentQuestion
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
          goBack={goBack}
          useAgent={useAgent}
          setUseAgent={setUseAgent}
        />

      )}

    </div>
  );
}

export default App;
