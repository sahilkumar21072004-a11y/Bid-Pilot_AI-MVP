export const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = sessionStorage.getItem("bidpilot_access_token");
  if (token && !headers.has("Authorization")) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (response.status === 401 && path !== "/api/auth/login") window.dispatchEvent(new Event("bidpilot:unauthorized"));
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try { message = (await response.json()).detail || message; } catch { /* response may not be JSON */ }
    throw new Error(message);
  }
  return response;
}

export async function jsonRequest(path, method = "GET", body) {
  const response = await request(path, { method, headers: { "Content-Type": "application/json" }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  return response.status === 204 ? null : response.json();
}
