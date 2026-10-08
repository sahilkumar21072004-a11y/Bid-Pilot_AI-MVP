import { useState } from "react";
import { Activity, LockKeyhole } from "lucide-react";
import { request } from "./api";

export default function Login({ onSuccess }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const response = await request("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }) });
      const data = await response.json(); sessionStorage.setItem("bidpilot_access_token", data.access_token); onSuccess(data);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return <main className="login-screen"><form className="login-card" onSubmit={submit}><div className="login-brand"><span><Activity size={20}/></span><strong>BID-PILOT <i>AI</i></strong></div><p className="eyebrow">SECURE WORKSPACE</p><h1>Welcome back</h1><p className="login-copy">Sign in to continue to your proposal workspace.</p>{error && <div className="alert error" role="alert">{error}</div>}<label className="field"><span>Username</span><input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required/></label><label className="field"><span>Password</span><input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required/></label><button className="button primary login-button" disabled={busy}><LockKeyhole size={15}/>{busy ? "Signing in…" : "Sign in"}</button><small>Local workspace authentication</small></form></main>;
}
