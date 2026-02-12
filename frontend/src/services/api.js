import { API_URL } from "../config";

const API = API_URL;

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
