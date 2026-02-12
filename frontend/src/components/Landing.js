import React from "react";
import Loader from "./Loader";

function Landing({
  repoUrl,
  setRepoUrl,
  ingestRepo,
  useExisting,
  loading,
  status
}) {

  return (

    <div className="card fade-in">

      <h1>Repo Doc Bot</h1>

      <p className="subtitle">
        AI Assistant for GitHub Repositories
      </p>

      <input
        className="input"
        value={repoUrl}
        onChange={e => setRepoUrl(e.target.value)}
        placeholder="https://github.com/user/repo"
      />

      <div className="btn-group">

        <button
          className="btn primary"
          disabled={loading}
          onClick={ingestRepo}
        >
          Ingest
        </button>

        <button
          className="btn secondary"
          disabled={loading}
          onClick={useExisting}
        >
          Use Existing
        </button>

      </div>

      <p className="status">{status}</p>

      {loading && <Loader />}

    </div>
  );
}

export default Landing;
