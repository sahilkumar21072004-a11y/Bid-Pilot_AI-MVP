import { useCallback, useEffect, useState } from "react";
import { Activity, ArrowDownToLine, BookOpen, BriefcaseBusiness, Building2, Check, ChevronRight, CircleHelp, FileText, LayoutDashboard, Plus, Search, Settings2, ShieldCheck, Sparkles, Trash2, Upload, Users, WandSparkles } from "lucide-react";
import { API, jsonRequest, request } from "./api";
import "./analytics.css";
import "./workflow.css";
import Login from "./Login.jsx";
import "./login.css";
import "./versions.css";

const AGENTS = ["Extraction Agent", "Analysis Agent", "Drafting Agent", "Cost Estimation Agent", "Compliance Agent", "Optimisation Agent"];
const blankCompany = { name: "", tagline: "", capabilities: "", certifications: "", case_studies: "", rate_card: "" };

export default function App() {
  const [page, setPage] = useState("Overview");
  const [dashboard, setDashboard] = useState({});
  const [proposals, setProposals] = useState([]);
  const [knowledge, setKnowledge] = useState([]);
  const [company, setCompany] = useState(blankCompany);
  const [templates, setTemplates] = useState([]);
  const [team, setTeam] = useState([]);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [authReady, setAuthReady] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [query, setQuery] = useState("");
  const [knowledgeForm, setKnowledgeForm] = useState({ title: "", content: "", category: "General", tags: "" });
  const [templateForm, setTemplateForm] = useState({ name: "", sections: "Executive Summary, Delivery Approach, Timeline, Investment, Compliance" });
  const [memberForm, setMemberForm] = useState({ name: "", email: "", username: "", password: "", role: "Reviewer" });

  const refresh = useCallback(async () => {
    setError("");
    try {
      const [stats, proposalRows, knowledgeRows, companyRow, templateRows, teamRows] = await Promise.all([
        jsonRequest("/api/dashboard"), jsonRequest("/api/proposals"), jsonRequest("/api/knowledge"), jsonRequest("/api/company-profile"), jsonRequest("/api/templates"), jsonRequest("/api/team")
      ]);
      setDashboard(stats); setProposals(proposalRows); setKnowledge(knowledgeRows); setCompany({ ...blankCompany, ...companyRow }); setTemplates(templateRows); setTeam(teamRows);
      if (selected) setSelected(proposalRows.find((item) => item.id === selected.id) || null);
    } catch (e) { setError(`${e.message}. Check that the backend is running on ${API}.`); }
  }, [selected]);

  useEffect(() => {
    let active = true;
    jsonRequest("/api/auth/config").then((config) => {
      if (!active) return;
      setAuthRequired(config.required); setAuthenticated(!config.required || config.authenticated); setUser(config.authenticated ? { username: config.username, role: config.role } : null);
      if (!config.required || config.authenticated) refresh();
    }).catch((e) => { if (active) setError(`Could not check workspace login: ${e.message}`); }).finally(() => { if (active) setAuthReady(true); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    const unauthorized = () => { sessionStorage.removeItem("bidpilot_access_token"); setAuthenticated(false); setUser(null); };
    window.addEventListener("bidpilot:unauthorized", unauthorized);
    return () => window.removeEventListener("bidpilot:unauthorized", unauthorized);
  }, []);

  async function generate(event) {
    event.preventDefault(); const file = event.currentTarget.elements.rfp.files[0];
    if (!file) { setError("Choose an RFP file first."); return; }
    setBusy(true); setError(""); setNotice("");
    const body = new FormData(); body.append("file", file);
    try { const response = await request(`/api/proposals/generate${event.currentTarget.elements.template.value ? `?template_id=${event.currentTarget.elements.template.value}` : ""}`, { method: "POST", body }); const draft = await response.json(); await refresh(); setSelected(draft); setPage("Proposals"); setNotice("Draft generated in local demo mode."); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  async function saveProposal() {
    if (!selected) return;
    try { const saved = await jsonRequest(`/api/proposals/${selected.id}`, "PUT", selected); setSelected(saved); await refresh(); setNotice("Proposal changes saved."); }
    catch (e) { setError(e.message); }
  }

  async function restoreVersion(versionId) {
    if (!selected) return;
    try { const restored = await jsonRequest(`/api/proposals/${selected.id}/versions/${versionId}/restore`, "POST"); setSelected(restored); await refresh(); setNotice("Version restored and saved as a new version."); }
    catch (e) { setError(e.message); }
  }

  async function exportProposal(format) {
    try { const response = await request(`/api/proposals/${selected.id}/export?format=${format}`, { method: "POST" }); const blob = await response.blob(); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `proposal-${selected.id}.${format}`; link.click(); URL.revokeObjectURL(link.href); }
    catch (e) { setError(e.message); }
  }

  async function addKnowledge(event) {
    event.preventDefault(); try { await jsonRequest("/api/knowledge", "POST", knowledgeForm); setKnowledgeForm({ title: "", content: "", category: "General", tags: "" }); await refresh(); setNotice("Knowledge entry added."); } catch (e) { setError(e.message); }
  }

  async function removeKnowledge(id) { try { await jsonRequest(`/api/knowledge/${id}`, "DELETE"); await refresh(); } catch (e) { setError(e.message); } }
  async function addTemplate(event) { event.preventDefault(); try { await jsonRequest("/api/templates", "POST", { name: templateForm.name, sections: templateForm.sections.split(",").map((s) => s.trim()).filter(Boolean) }); setTemplateForm({ ...templateForm, name: "" }); await refresh(); setNotice("Template saved."); } catch (e) { setError(e.message); } }
  async function addMember(event) { event.preventDefault(); try { await jsonRequest("/api/team", "POST", memberForm); setMemberForm({ name: "", email: "", username: "", password: "", role: "Reviewer" }); await refresh(); setNotice("Team login account added."); } catch (e) { setError(e.message); } }

  const nav = [{ label: "Overview", icon: LayoutDashboard }, { label: "Proposals", icon: FileText }, { label: "Knowledge base", icon: BookOpen }, { label: "Company profile", icon: Building2 }, { label: "Templates", icon: BriefcaseBusiness }, { label: "Team", icon: Users }].filter((item) => item.label !== "Team" || !authRequired || user?.role === "admin");
  if (!authReady) return <div className="login-screen"><div className="login-loading">Checking workspace access…</div></div>;
  if (authRequired && !authenticated) return <Login onSuccess={(data) => { setUser(data); setAuthenticated(true); setError(""); refresh(); }} />;
  return <div className="shell">
    <aside className="sidebar"><div className="brand"><div className="brand-icon"><Activity size={19}/></div><div><strong>BID-PILOT <i>AI</i></strong><small>PROPOSAL INTELLIGENCE</small></div></div><div className="nav-label">WORKSPACE</div><nav>{nav.map(({ label, icon: Icon }) => <button key={label} className={`nav-link ${page === label ? "active" : ""}`} onClick={() => { setPage(label); setSelected(null); }}><Icon size={17}/>{label}{label === "Proposals" && <span className="nav-count">{proposals.length}</span>}</button>)}</nav><div className="side-bottom"><div className="demo-badge"><span/> {authRequired ? `Signed in as ${user?.username || "admin"}` : "Local demo mode"}</div><div className="help"><CircleHelp size={17}/><strong>Need a hand?</strong><p>API and health checks are available in FastAPI docs.</p><a href={`${API}/docs`} target="_blank" rel="noreferrer">Open API guide <ChevronRight size={14}/></a></div>{authRequired && <button className="signout-button" onClick={() => { sessionStorage.removeItem("bidpilot_access_token"); setAuthenticated(false); setUser(null); }}>Sign out</button>}<small className="version">BID-PILOT AI · MVP</small></div></aside>
    <main className="main"><header className="topbar"><div><span className="crumb">WORKSPACE / </span><span>{selected && page === "Proposals" ? selected.title : page}</span></div><div className="top-user"><span className="online-dot"/> SYSTEM READY <div className="avatar">SK</div></div></header>
      <div className="content">{error && <div className="alert error">{error}<button onClick={() => setError("")}>×</button></div>}{notice && <div className="alert success">{notice}<button onClick={() => setNotice("")}>×</button></div>}
      {page === "Overview" && <><div className="welcome"><div><p className="eyebrow">BID-PILOT WORKSPACE</p><h1>Good morning, Sahil <Sparkles size={22}/></h1><p>Turn RFP requirements into a grounded proposal your team can review.</p></div><button className="button secondary" onClick={() => { setSelected(null); setPage("Proposals"); }}><Plus size={16}/> New proposal</button></div>
        <div className="stat-grid">{[["Proposals", dashboard.proposals ?? "—", "Saved drafts", FileText], ["Requirements", dashboard.requirements ?? "—", "Across proposals", Settings2], ["Mandatory", dashboard.mandatory ?? "—", "Must-have items", ShieldCheck], ["Compliance", `${dashboard.compliance ?? 0}%`, "Approved requirements", Check]].map(([label, value, sub, Icon]) => <article className="stat-card" key={label}><div className="stat-head"><span>{label}</span><Icon size={16}/></div><strong>{value}</strong><small>{sub}</small></article>)}</div>
        <div className="dashboard-grid"><section className="panel upload-panel"><div className="panel-title"><div><span className="eyebrow">GET STARTED · STEP 01</span><h2>Start with an RFP</h2></div><span className="step-pill">01 / 03</span></div><form onSubmit={generate}><label className="dropzone"><input name="rfp" type="file" accept=".pdf,.docx,.txt,.md"/><Upload size={24}/><strong>Drop your RFP here</strong><span>or browse from your computer</span><small>PDF, DOCX, TXT or MD · up to 25 MB</small></label><div className="upload-actions"><select name="template"><option value="">Standard proposal template</option>{templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</select><button className="button primary" disabled={busy}>{busy ? <><span className="spinner"/> Processing</> : <><WandSparkles size={16}/> Generate proposal</>}</button></div></form></section>
        <section className="panel agent-panel"><div className="panel-title"><div><span className="eyebrow">YOUR AI TEAM</span><h2>Specialised agents</h2></div><span className="ready-pill"><span/> Demo ready</span></div><div className="agent-grid">{AGENTS.map((name, i) => <div className="agent" key={name}><span className={`agent-icon tint-${i}`}>{["EX", "AN", "DR", "CE", "CO", "OP"][i]}</span><div><strong>{name}</strong><small><span/> Ready for demo workflow</small></div><ChevronRight size={15}/></div>)}</div><div className="workflow-line"><Sparkles size={16}/> Proposal workflow <small>Upload an RFP to begin</small></div></section></div>
        <section className="panel recent-panel"><div className="panel-title"><div><span className="eyebrow">WORK IN PROGRESS</span><h2>Recent proposals</h2></div><button className="text-button" onClick={() => setPage("Proposals")}>View all <ChevronRight size={15}/></button></div>{proposals.length ? <div className="table-wrap"><table><thead><tr><th>PROPOSAL</th><th>STATUS</th><th>REQUIREMENTS</th><th>UPDATED</th><th/></tr></thead><tbody>{proposals.slice(0,5).map((p) => <tr key={p.id} onClick={() => { setSelected(p); setPage("Proposals"); }}><td><strong>{p.title}</strong><small>{p.source_name}</small></td><td><span className="status-tag">{p.status}</span></td><td>{p.requirements.length}</td><td>{new Date(p.updated_at).toLocaleDateString()}</td><td><ChevronRight size={16}/></td></tr>)}</tbody></table></div> : <div className="empty">No proposals yet. Upload an RFP to create your first demo draft.</div>}</section>
      </>}
      {page === "Proposals" && <section className="page-section"><PageTitle eyebrow="PROPOSAL WORKSPACE" title={selected ? selected.title : "Proposals"} text="Generate, review and maintain RFP response drafts." action={!selected && <button className="button secondary" onClick={() => { setSelected(null); setPage("Overview"); }}><Plus size={15}/> New proposal</button>}/>{selected ? <ProposalEditor proposal={selected} setProposal={setSelected} onSave={saveProposal} onExport={exportProposal} onBack={() => setSelected(null)} team={team}/> : proposals.length ? <div className="proposal-grid">{proposals.map((p) => <button className="proposal-card" key={p.id} onClick={() => setSelected(p)}><div className="proposal-card-head"><span className="doc-icon"><FileText size={18}/></span><span className="status-tag">{p.status}</span></div><strong>{p.title}</strong><small>{p.source_name}</small><div className="proposal-meta"><span>{p.requirements.length} requirements</span><span>{new Date(p.updated_at).toLocaleDateString()}</span></div></button>)}</div> : <div className="empty panel">No proposal drafts yet. Use Overview to upload an RFP.</div>}</section>}
      {page === "Knowledge base" && <section className="page-section"><PageTitle eyebrow="GROUNDED CONTENT" title="Knowledge base" text="Manage the approved facts used to ground proposal drafts."/><div className="two-col"><form className="panel form-panel" onSubmit={addKnowledge}><h3>Add knowledge entry</h3><Field label="Title"><input required value={knowledgeForm.title} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, title: e.target.value })}/></Field><Field label="Content"><textarea required rows="6" value={knowledgeForm.content} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, content: e.target.value })}/></Field><div className="form-row"><Field label="Category"><input value={knowledgeForm.category} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, category: e.target.value })}/></Field><Field label="Tags"><input value={knowledgeForm.tags} onChange={(e) => setKnowledgeForm({ ...knowledgeForm, tags: e.target.value })}/></Field></div><button className="button primary"><Plus size={15}/> Add entry</button></form><div className="panel"><div className="list-heading"><div><h3>Approved reference content</h3><p>{knowledge.length} entries</p></div><label className="search"><Search size={15}/><input placeholder="Search knowledge" value={query} onChange={(e) => setQuery(e.target.value)}/></label></div><div className="knowledge-list">{knowledge.filter((k) => `${k.title} ${k.content} ${k.tags}`.toLowerCase().includes(query.toLowerCase())).map((item) => <article className="knowledge-item" key={item.id}><div><span className="category-tag">{item.category}</span><h4>{item.title}</h4><p>{item.content}</p><small>{item.tags}</small></div><button className="icon-button danger" title="Delete entry" onClick={() => removeKnowledge(item.id)}><Trash2 size={16}/></button></article>)}</div></div></div></section>}
      {page === "Company profile" && <section className="page-section"><PageTitle eyebrow="ORGANISATION SETTINGS" title="Company profile" text="Maintain the company evidence used in draft generation."/><form className="panel form-panel wide-form" onSubmit={async (e) => { e.preventDefault(); try { await jsonRequest("/api/company-profile", "PUT", company); setNotice("Company profile saved."); } catch (ex) { setError(ex.message); } }}><div className="form-row"><Field label="Company name"><input value={company.name} onChange={(e) => setCompany({ ...company, name: e.target.value })}/></Field><Field label="Tagline"><input value={company.tagline} onChange={(e) => setCompany({ ...company, tagline: e.target.value })}/></Field></div><Field label="Capabilities"><textarea rows="4" value={company.capabilities} onChange={(e) => setCompany({ ...company, capabilities: e.target.value })}/></Field><Field label="Certifications"><textarea rows="3" value={company.certifications} onChange={(e) => setCompany({ ...company, certifications: e.target.value })}/></Field><Field label="Case studies"><textarea rows="4" value={company.case_studies} onChange={(e) => setCompany({ ...company, case_studies: e.target.value })}/></Field><Field label="Rate card (JSON or free text)"><textarea rows="3" value={company.rate_card} onChange={(e) => setCompany({ ...company, rate_card: e.target.value })}/></Field><button className="button primary">Save company profile</button></form></section>}
      {page === "Templates" && <section className="page-section"><PageTitle eyebrow="REUSABLE STRUCTURE" title="Proposal templates" text="Create reusable proposal section outlines."/><div className="two-col"><form className="panel form-panel" onSubmit={addTemplate}><h3>New template</h3><Field label="Template name"><input required value={templateForm.name} onChange={(e) => setTemplateForm({ ...templateForm, name: e.target.value })}/></Field><Field label="Sections (comma separated)"><textarea rows="5" value={templateForm.sections} onChange={(e) => setTemplateForm({ ...templateForm, sections: e.target.value })}/></Field><button className="button primary"><Plus size={15}/> Save template</button></form><div className="panel"><h3>Available templates</h3>{templates.map((t) => <div className="template-item" key={t.id}><span className="doc-icon"><FileText size={17}/></span><div><strong>{t.name}</strong><small>{t.sections.join(" · ")}</small></div><button className="icon-button danger" onClick={async () => { try { await jsonRequest(`/api/templates/${t.id}`, "DELETE"); await refresh(); } catch (e) { setError(e.message); } }}><Trash2 size={16}/></button></div>)}</div></div></section>}
      {page === "Team" && <section className="page-section"><PageTitle eyebrow="REVIEW WORKFLOW" title="Team" text="Create reviewer and read-only accounts for this workspace."/><div className="two-col"><form className="panel form-panel" onSubmit={addMember}><h3>Add a collaborator</h3><Field label="Full name"><input required value={memberForm.name} onChange={(e) => setMemberForm({ ...memberForm, name: e.target.value })}/></Field><Field label="Email"><input required type="email" value={memberForm.email} onChange={(e) => setMemberForm({ ...memberForm, email: e.target.value })}/></Field><Field label="Username"><input required minLength="3" pattern="[A-Za-z0-9_.-]+" value={memberForm.username} onChange={(e) => setMemberForm({ ...memberForm, username: e.target.value })}/></Field><Field label="Temporary password (12+ characters)"><input required minLength="12" type="password" autoComplete="new-password" value={memberForm.password} onChange={(e) => setMemberForm({ ...memberForm, password: e.target.value })}/></Field><Field label="Role"><select value={memberForm.role} onChange={(e) => setMemberForm({ ...memberForm, role: e.target.value })}><option>Reviewer</option><option>Viewer</option></select></Field><button className="button primary"><Plus size={15}/> Create account</button></form><div className="panel"><h3>Workspace accounts</h3>{team.length ? team.map((member) => <div className="template-item" key={member.id}><span className="avatar">{member.name.slice(0,1).toUpperCase()}</span><div><strong>{member.name}</strong><small>{member.username} · {member.email}</small></div><select aria-label={`Role for ${member.username}`} value={member.role} onChange={async (e) => { try { await jsonRequest(`/api/team/${member.id}`, "PATCH", { role: e.target.value }); await refresh(); } catch (error) { setError(error.message); } }}><option>Reviewer</option><option>Viewer</option></select><button className="button secondary" onClick={async () => { try { await jsonRequest(`/api/team/${member.id}`, "PATCH", { active: !member.active }); await refresh(); } catch (error) { setError(error.message); } }}>{member.active ? "Active" : "Inactive"}</button><button className="icon-button danger" title="Remove account" onClick={async () => { try { await jsonRequest(`/api/team/${member.id}`, "DELETE"); await refresh(); } catch (e) { setError(e.message); } }}><Trash2 size={16}/></button></div>) : <div className="empty">No team accounts yet.</div>}<p className="security-note">Reviewers can work with proposals. Viewers have read-only API access. The admin is configured in backend/.env.</p></div></div></section>}
      {page === "Proposals" && selected && <VersionHistory proposal={selected} onRestore={restoreVersion}/>}
      </div></main>
  </div>;
}

function PageTitle({ eyebrow, title, text, action }) { return <div className="page-title"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{text}</p></div>{action}</div>; }
function Field({ label, children }) { return <label className="field"><span>{label}</span>{children}</label>; }

function ProposalEditor({ proposal, setProposal, onSave, onExport, onBack, team }) {
  const patch = (key, value) => setProposal({ ...proposal, [key]: value });
  const patchSection = (index, key, value) => patch("sections", proposal.sections.map((section, i) => i === index ? { ...section, [key]: value } : section));
  const patchRequirement = (index, key, value) => patch("requirements", proposal.requirements.map((item, i) => i === index ? { ...item, [key]: value } : item));
  return <div className="editor"><div className="editor-toolbar"><button className="text-button" onClick={onBack}>← All proposals</button><div className="toolbar-actions"><select value={proposal.status} onChange={(e) => patch("status", e.target.value)}><option>Draft</option><option>In review</option><option>Approved</option><option>Submitted</option></select><button className="button secondary" onClick={() => onExport("docx")}><ArrowDownToLine size={15}/> DOCX</button><button className="button secondary" onClick={() => onExport("pdf")}><ArrowDownToLine size={15}/> PDF</button><button className="button primary" onClick={onSave}>Save changes</button></div></div><div className="editor-meta"><span>{proposal.source_name}</span><span>{proposal.requirements.length} requirements</span><span>Updated {new Date(proposal.updated_at).toLocaleString()}</span></div>{proposal.workflow && <div className="workflow-card"><div className="workflow-card-head"><div><span className="eyebrow">MULTI-AGENT RUN</span><strong>{proposal.workflow.llm_mode === "llm" ? "LLM-assisted draft" : "Local mock draft"}</strong></div><span className="status-tag">{proposal.workflow.compliance?.readiness_percent || 0}% reviewed</span></div><div className="workflow-agents">{(proposal.workflow.agents || []).map((run) => <span key={run.agent}><Check size={13}/>{run.agent}</span>)}</div><div className="workflow-cost">{proposal.workflow.cost_estimate?.total ? <>Estimated cost: <strong>${Number(proposal.workflow.cost_estimate.total).toLocaleString()}</strong> · {proposal.workflow.cost_estimate.planning_hours} planning hours</> : <>Planning effort: {proposal.workflow.cost_estimate?.planning_hours || 0} hours · Add a numeric rate card to calculate price</>}</div></div>}<Field label="Proposal title"><input className="title-input" value={proposal.title} onChange={(e) => patch("title", e.target.value)}/></Field><div className="editor-grid"><div><h3>Proposal sections</h3>{proposal.sections.map((section, index) => <article className="panel edit-section" key={index}><input className="section-heading" value={section.heading} onChange={(e) => patchSection(index, "heading", e.target.value)}/><textarea rows="7" value={section.body} onChange={(e) => patchSection(index, "body", e.target.value)}/></article>)}</div><aside><div className="panel review-panel"><h3>Review workflow</h3><Field label="Assigned reviewer"><select value={proposal.reviewer || ""} onChange={(e) => patch("reviewer", e.target.value)}><option value="">Unassigned</option>{team.map((member) => <option key={member.id} value={member.name}>{member.name} · {member.role}</option>)}</select></Field><p className="small-label">COMPLIANCE MATRIX</p>{proposal.requirements.map((item, index) => <div className="compliance-item" key={item.id || index}><div><span className={`category-tag ${item.category === "Mandatory" ? "mandatory" : ""}`}>{item.category}</span><p>{item.text}</p></div><select value={item.review_status || "Needs review"} onChange={(e) => patchRequirement(index, "review_status", e.target.value)}><option>Needs review</option><option>In progress</option><option>Approved</option><option>Gap</option></select><textarea aria-label="Requirement response" rows="2" value={item.response || ""} onChange={(e) => patchRequirement(index, "response", e.target.value)} placeholder="Response / evidence"/></div>)}<h3>Review comments</h3><Comments proposal={proposal} patch={patch}/></div></aside></div></div>;
}

function Comments({ proposal, patch }) {
  const [text, setText] = useState("");
  return <><div className="comments">{(proposal.comments || []).map((comment, i) => <div className="comment" key={i}><strong>{comment.author || "Reviewer"}</strong><p>{comment.text}</p></div>)}</div><form className="comment-form" onSubmit={(e) => { e.preventDefault(); if (!text.trim()) return; patch("comments", [...(proposal.comments || []), { author: "Sahil Kumar", text, created_at: new Date().toISOString() }]); setText(""); }}><textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Add a review comment" rows="3"/><button className="button secondary">Add comment</button></form></>;
}

function VersionHistory({ proposal, onRestore }) {
  const [versions, setVersions] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    jsonRequest(`/api/proposals/${proposal.id}/versions`).then((rows) => { if (active) setVersions(rows); }).catch((e) => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [proposal.id, proposal.updated_at]);
  return <section className="panel version-panel"><div className="panel-title"><div><span className="eyebrow">AUDITABLE EDITS</span><h2>Version history</h2></div><span className="chart-count">{versions.length} saved versions</span></div>{error && <p className="security-note">{error}</p>}{versions.length ? versions.map((version) => <div className="version-row" key={version.id}><div><strong>Version {version.version_number}</strong><small>{version.created_by} · {new Date(version.created_at).toLocaleString()}</small></div>{version.version_number !== versions[0]?.version_number && <button className="button secondary" onClick={() => onRestore(version.id)}>Restore</button>}</div>) : <div className="empty">Save an edit to start version history.</div>}</section>;
}
