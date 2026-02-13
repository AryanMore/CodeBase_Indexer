const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

export const apiGet = async (url) => {
  const res = await fetch(`${API}${url}`);
  if (!res.ok) throw new Error();
  return res.json();
};
export const apiPost = async (url, body) => {

  const res = await fetch(`${API}${url}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  if (!res.ok) throw new Error();

  return res.json();
};


export const apiAgentQuery = async (repo_url, question, session_id) => {
  const res = await fetch(`${API}/agent/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ repo_url, question, session_id })
  });

  if (!res.ok) throw new Error();

  return res.json();
};
