import React, { useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { AlertTriangle, CalendarDays, Check, Clock, Download, FileText, GraduationCap, Loader2, Pencil, Plus, Sparkles, Upload, X } from 'lucide-react'
import './styles.css'

type EventType = 'assignment' | 'exam' | 'project' | 'presentation' | 'other'
type Deadline = {
  id: string
  title: string
  course: string
  due_date: string
  event_type: EventType
  effort_hours: number
  source_text: string
  confidence: number
  approved: boolean
  suggested_start: string | null
}
type Conflict = { severity: 'low' | 'medium' | 'high'; title: string; description: string; event_ids: string[] }

const API = import.meta.env.VITE_API_URL || ''
const SAMPLE = `CS 301 — Software Engineering, Fall 2026
Assignment 1: Requirements analysis — due September 23, 2026
Team proposal due: September 25, 2026
Midterm Exam — September 25, 2026
Project prototype due October 2, 2026
Final presentation: October 5, 2026
Final report due October 5, 2026`

function App() {
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [academicYear, setAcademicYear] = useState(2026)
  const [semesterStart, setSemesterStart] = useState('2026-09-01')
  const [semesterEnd, setSemesterEnd] = useState('2026-12-20')
  const [events, setEvents] = useState<Deadline[]>([])
  const [conflicts, setConflicts] = useState<Conflict[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState<Deadline | null>(null)
  const [addingNew, setAddingNew] = useState(false)
  const approved = events.filter(event => event.approved)
  const reviewed = events.length > 0
  const workload = useMemo(() => approved.reduce((sum, event) => sum + event.effort_hours, 0), [approved])

  async function parse() {
    setError('')
    setLoading(true)
    try {
      const form = new FormData()
      if (semesterEnd < semesterStart) throw new Error('Semester end date must be after the start date.')
      form.set('text', text)
      form.set('default_year', String(academicYear))
      form.set('semester_start', semesterStart)
      form.set('semester_end', semesterEnd)
      if (file) form.set('file', file)
      const response = await fetch(`${API}/api/parse`, { method: 'POST', body: form })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Could not process this syllabus.')
      setEvents(data.events)
      setConflicts(data.conflicts)
      if (!data.events.length) setError('No deadlines were found. Try pasting lines that include a title and date.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Something went wrong.')
    } finally { setLoading(false) }
  }

  async function reanalyze(next: Deadline[]) {
    setEvents(next)
    const response = await fetch(`${API}/api/analyze`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events: next, semester_start: semesterStart, semester_end: semesterEnd })
    })
    if (response.ok) setConflicts((await response.json()).conflicts)
  }

  function patch(id: string, values: Partial<Deadline>) {
    void reanalyze(events.map(event => event.id === id ? { ...event, ...values } : event))
  }

  function openNewDeadline() {
    setAddingNew(true)
    setEditing({
      id: crypto.randomUUID(), title: '', course: 'Course', due_date: semesterStart,
      event_type: 'assignment', effort_hours: 5, source_text: 'Added manually by student',
      confidence: 1, approved: true, suggested_start: null,
    })
  }

  function saveEditor() {
    if (!editing || !editing.title.trim() || !editing.due_date) return
    const next = addingNew
      ? [...events, { ...editing, title: editing.title.trim() }]
      : events.map(event => event.id === editing.id ? { ...editing, title: editing.title.trim() } : event)
    setEditing(null)
    setAddingNew(false)
    void reanalyze(next)
  }

  function closeEditor() {
    setEditing(null)
    setAddingNew(false)
  }

  async function downloadCalendar() {
    const response = await fetch(`${API}/api/export/ics`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ events })
    })
    if (!response.ok) return setError('Calendar export failed.')
    const url = URL.createObjectURL(await response.blob())
    const anchor = document.createElement('a')
    anchor.href = url; anchor.download = 'courseflow-calendar.ics'; anchor.click()
    URL.revokeObjectURL(url)
  }

  return <div className="app-shell">
    <header className="nav">
      <a className="brand" href="#top"><span className="brand-mark"><GraduationCap size={20}/></span>CourseFlow</a>
      <span className="badge">FirstCommit 2026</span>
    </header>

    <main id="top">
      <section className="hero">
        <div className="eyebrow"><Sparkles size={15}/> From syllabus to study plan</div>
        <h1>See deadline collisions<br/><span>before they become crises.</span></h1>
        <p>Paste syllabus text or upload a PDF. CourseFlow extracts deadlines, flags workload conflicts, and exports an approved calendar.</p>
        <div className="trust-row"><span><Check size={15}/> Review before export</span><span><Check size={15}/> Deterministic conflict checks</span><span><Check size={15}/> Calendar-ready output</span></div>
      </section>

      <section className="workspace">
        <div className="stepper">
          {['Import', 'Review', 'Resolve', 'Export'].map((label, index) => <div className={`step ${reviewed || index === 0 ? 'active' : ''}`} key={label}><b>{index + 1}</b><span>{label}</span></div>)}
        </div>

        <div className="input-grid">
          <div className="panel input-panel">
            <div className="panel-heading"><div><span className="section-kicker">01 · IMPORT</span><h2>Add your syllabus</h2></div><FileText/></div>
            <div className="semester-settings">
              <div className="settings-title"><div><span>Semester settings</span><small>Used for missing years and boundary warnings</small></div>{reviewed && <button onClick={() => void reanalyze(events)}>Update warnings</button>}</div>
              <div className="settings-grid">
                <label><span>Academic year</span><select value={academicYear} onChange={event => setAcademicYear(Number(event.target.value))}>{[2025, 2026, 2027, 2028].map(year => <option key={year} value={year}>{year}</option>)}</select></label>
                <label><span>Starts</span><input type="date" value={semesterStart} onChange={event => setSemesterStart(event.target.value)}/></label>
                <label><span>Ends</span><input type="date" value={semesterEnd} onChange={event => setSemesterEnd(event.target.value)}/></label>
              </div>
              {semesterEnd < semesterStart && <div className="settings-error"><AlertTriangle size={14}/>End date must be after the start date.</div>}
            </div>
            <label htmlFor="syllabus-text">Paste syllabus text</label>
            <textarea id="syllabus-text" value={text} onChange={event => setText(event.target.value)} placeholder="Paste assignment, exam, and project dates here…" />
            <div className="or"><span>or upload</span></div>
            <label className="dropzone">
              <Upload size={22}/><span>{file ? file.name : 'Choose a syllabus PDF'}</span><small>PDF · maximum 8 MB</small>
              <input type="file" accept="application/pdf" onChange={event => setFile(event.target.files?.[0] || null)} />
            </label>
            <div className="button-row">
              <button className="secondary" onClick={() => { setText(SAMPLE); setFile(null) }}>Use sample</button>
              <button className="primary" onClick={parse} disabled={loading || (!text.trim() && !file)}>{loading ? <><Loader2 className="spin" size={17}/>Analyzing…</> : <><Sparkles size={17}/>Find deadlines</>}</button>
            </div>
            {error && <div className="error"><AlertTriangle size={17}/>{error}</div>}
          </div>

          <aside className="panel insight-panel">
            <span className="section-kicker">LIVE SUMMARY</span><h2>Your semester at a glance</h2>
            <div className="metrics">
              <div><strong>{approved.length}</strong><span>approved deadlines</span></div>
              <div><strong>{conflicts.length}</strong><span>items to review</span></div>
              <div><strong>{workload}h</strong><span>estimated workload</span></div>
            </div>
            <div className="mini-timeline">
              {approved.slice(0, 5).map(event => <div key={event.id}><i className={event.event_type}/><span><b>{event.title}</b><small>{formatDate(event.due_date)}</small></span></div>)}
              {!approved.length && <div className="empty-mini"><CalendarDays/><p>Your extracted timeline will appear here.</p></div>}
            </div>
          </aside>
        </div>
      </section>

      {reviewed && <>
        <section className="results-section">
          <div className="section-title"><div><span className="section-kicker">02 · REVIEW</span><h2>Verify every deadline</h2><p>CourseFlow never silently exports uncertain dates. Edit, add, or reject anything that looks wrong.</p></div><div className="review-actions"><span className="count">{events.length} found</span><button className="add-button" onClick={openNewDeadline}><Plus size={16}/>Add missing deadline</button></div></div>
          <div className="event-list">
            {events.map(event => <article className={`event-card ${!event.approved ? 'rejected' : ''}`} key={event.id}>
              <div className={`type-icon ${event.event_type}`}><CalendarDays size={20}/></div>
              <div className="event-summary">
                <div className="event-title-row"><span className="event-type-label">{event.event_type}</span><h3>{event.title}</h3></div>
                <div className="event-meta"><span><CalendarDays size={14}/>{formatDate(event.due_date)}</span><span><Clock size={14}/>{event.effort_hours} hours</span><span>Start by {event.suggested_start ? formatDate(event.suggested_start) : 'after review'}</span></div>
                <div className="source">Source: “{event.source_text}”</div>
              </div>
              <div className="card-actions"><button className="edit-button" onClick={() => { setAddingNew(false); setEditing({ ...event }) }}><Pencil size={15}/>Edit</button><button className={`approval ${event.approved ? 'approved' : ''}`} onClick={() => patch(event.id, { approved: !event.approved })} title={event.approved ? 'Reject deadline' : 'Approve deadline'}>{event.approved ? <Check/> : <X/>}</button></div>
            </article>)}
          </div>
        </section>

        <section className="conflict-section">
          <div className="section-title"><div><span className="section-kicker">03 · RESOLVE</span><h2>Workload warnings</h2></div></div>
          <div className="conflict-grid">
            {conflicts.map((conflict, index) => <article className={`conflict ${conflict.severity}`} key={`${conflict.title}-${index}`}><AlertTriangle/><div><span>{conflict.severity} priority</span><h3>{conflict.title}</h3><p>{conflict.description}</p></div></article>)}
            {!conflicts.length && <article className="all-clear"><Check/><div><h3>No conflicts detected</h3><p>Your approved deadlines are reasonably distributed.</p></div></article>}
          </div>
        </section>

        <section className="export-section">
          <div><span className="section-kicker">04 · EXPORT</span><h2>Your reviewed calendar is ready.</h2><p>Download {approved.length} approved deadlines as a standard calendar file.</p></div>
          <button className="export-button" disabled={!approved.length} onClick={downloadCalendar}><Download/>Download .ICS calendar</button>
        </section>
      </>}

      {editing && <div className="modal-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) closeEditor() }}>
        <div className="modal" role="dialog" aria-modal="true" aria-labelledby="editor-title">
          <div className="modal-heading"><div><span className="section-kicker">{addingNew ? 'ADD DEADLINE' : 'EDIT DEADLINE'}</span><h2 id="editor-title">{addingNew ? 'Add a missing deadline' : 'Update this deadline'}</h2></div><button className="close-button" onClick={closeEditor} aria-label="Close"><X/></button></div>
          <div className="modal-grid">
            <label className="modal-field full"><span>Deadline title</span><input autoFocus value={editing.title} onChange={event => setEditing({ ...editing, title: event.target.value })} placeholder="e.g. Final project"/></label>
            <label className="modal-field"><span>Due date</span><input type="date" value={editing.due_date} onChange={event => setEditing({ ...editing, due_date: event.target.value })}/><small>Click the calendar icon to choose a date.</small></label>
            <label className="modal-field"><span>Type</span><select value={editing.event_type} onChange={event => setEditing({ ...editing, event_type: event.target.value as EventType })}><option value="assignment">Assignment</option><option value="exam">Exam or quiz</option><option value="project">Project</option><option value="presentation">Presentation</option><option value="other">Other</option></select></label>
            <label className="modal-field"><span>Estimated effort</span><div className="effort-input"><input type="number" min="1" max="100" value={editing.effort_hours} onChange={event => setEditing({ ...editing, effort_hours: Number(event.target.value) })}/><b>hours</b></div></label>
            <label className="modal-field"><span>Course</span><input value={editing.course} onChange={event => setEditing({ ...editing, course: event.target.value })}/></label>
          </div>
          <div className="modal-note"><Check size={16}/>Saving will recalculate workload warnings automatically.</div>
          <div className="modal-actions"><button className="secondary" onClick={closeEditor}>Cancel</button><button className="primary" onClick={saveEditor} disabled={!editing.title.trim() || !editing.due_date}>{addingNew ? 'Add deadline' : 'Save changes'}</button></div>
        </div>
      </div>}
    </main>
    <footer><span>CourseFlow · Built for students</span><span>Review → Resolve → Export</span></footer>
  </div>
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`))
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>)
