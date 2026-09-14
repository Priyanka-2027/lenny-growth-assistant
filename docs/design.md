# Design Document
## The Lenny Growth Assistant — UI/UX

**Version:** 1.0  
**Date:** September 2026

---

## 1. Design Principles

**1. Trust through transparency**  
Every assistant response shows where the answer came from. Source citations are a first-class UI element, not an afterthought. Users should never wonder "did the AI make this up?"

**2. Low friction to value**  
The skill selector is visible before every message. No hidden commands, no prompt engineering required from the user. The four skills cover the four things users actually want: ask, write, document, visualize.

**3. Context preservation**  
The sidebar shows all sessions. Switching sessions reloads history instantly. The user's work is never lost — it's always one click away.

**4. Output, not interface**  
The artifact viewer opens beside the chat rather than replacing it. The user sees the generated content immediately without losing conversational context.

**5. Honest failure states**  
Loading spinners, streaming indicators, and error messages are explicit. The app never silently fails or pretends to work when it isn't.

---

## 2. Information Architecture

```
App Layout (three-column on wide screens)
├── Sidebar (260px, fixed)
│   ├── Brand / logo
│   ├── New Chat button (CTA)
│   ├── Session list (scrollable)
│   │   └── Session item [title, message count, delete]
│   └── Knowledge base status [chunk count, Index button]
│
├── Main panel (flex-1)
│   ├── Header bar [session title, ModelBadge]
│   ├── Message list (scrollable)
│   │   ├── User bubble [text]
│   │   └── Assistant bubble [markdown, skill badge, sources, model used]
│   └── Input area
│       ├── Skill selector [Ask Lenny | Ship 30 | Markdown | HTML]
│       ├── Textarea (auto-resize)
│       └── Send button
│
└── Artifact Viewer (45%, slides in)
    ├── Header [type badge, title, copy/download/close]
    ├── Security notice (HTML only)
    └── Content area
        ├── HTML → sandboxed iframe
        └── Markdown → react-markdown renderer
```

---

## 3. Visual Design

### Color palette (dark theme)

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-base` | `#0f0f0f` | Page background |
| `--bg-surface` | `#1a1a1a` | Sidebar, header, input area |
| `--bg-elevated` | `#232323` | Cards, skill buttons, source items |
| `--accent` | `#f5a623` | Primary actions, headings in markdown, active states |
| `--user-bubble` | `#1e3a5f` | User message bubble |
| `--text-primary` | `#f0f0f0` | Body text |
| `--text-secondary` | `#a0a0a0` | Labels, descriptions |
| `--text-muted` | `#666` | Timestamps, sub-labels |
| `--error` | `#e05260` | Error states, destructive actions |
| `--success` | `#4caf7d` | Knowledge base status indicator |

The amber accent (`#f5a623`) was chosen to evoke the warmth of Lenny's brand without copying it directly. It creates clear affordance contrast against the dark background.

### Typography

- Body: system-ui font stack — loads instantly, no font request
- Code/mono: JetBrains Mono → Fira Code → Cascadia Code → monospace fallback
- Base size: 15px / 1.6 line-height — comfortable for longer AI responses

### Border radius scale
- `--radius-sm`: 6px — buttons, source items
- `--radius-md`: 10px — code blocks, skill buttons
- `--radius-lg`: 14px — message bubbles
- `--radius-xl`: 20px — pill tags, badges

---

## 4. Key Interaction States

### Message sending
```
Idle → [user types] → Send enabled → [user sends]
  → User bubble appears immediately (optimistic)
  → Assistant bubble shows spinner + "Thinking…"
  → Response arrives → spinner replaced with markdown content
  → Sources expand toggle appears if sources exist
```

### Session lifecycle
```
No session selected → empty state with example questions
  → [click New Chat] → session created → cursor focused in input
  → [send messages] → sidebar message count increments (debounced refresh)
  → [click ✕] → confirm-on-second-click pattern (no modal needed)
  → [click again] → session deleted, chat cleared
```

### Artifact viewer
```
Artifact generated → viewer slides in from right
  → Chat panel narrows to accommodate (flex layout)
  → Artifact header shows type badge + title
  → HTML: sandboxed iframe renders immediately
  → Markdown: react-markdown renders with styled headings
  → [copy] → clipboard API, no visual feedback needed (browser default)
  → [download] → blob URL download, file named from title
  → [✕] → viewer closes, chat returns to full width
```

### LLM unavailable
```
User sends message → API call fails
  → Assistant bubble shows error state: "⚠ [error message]"
  → Error is in-line, not a toast or modal
  → User can retry immediately
```

---

## 5. Responsive Behavior

| Breakpoint | Behavior |
|-----------|---------|
| > 1280px | Three columns: sidebar + chat + artifact viewer |
| 900–1280px | Sidebar collapsed to icons on mobile; chat + artifact viewer share space |
| < 900px | Single column; artifact viewer overlays full width |

The current implementation targets desktop (1280px+). The CSS uses flex layout with `min-width: 0` throughout to prevent overflow. Mobile layout is a planned improvement.

---

## 6. Accessibility

| Concern | Implementation |
|---------|---------------|
| Keyboard navigation | All interactive elements reachable by Tab; Enter activates buttons |
| Screen reader support | `role="log"` + `aria-live="polite"` on message list; `role="radiogroup"` + `aria-checked` on skill selector; `aria-label` on all icon buttons |
| Focus management | After sending, focus returns to textarea automatically |
| Color contrast | Primary text `#f0f0f0` on `#1a1a1a` background: contrast ratio ≈ 14:1 (WCAG AAA) |
| Semantic HTML | `<aside>` for sidebar, `<header>`, `<main>`, `<nav>` used appropriately |
| Artifact iframe | `title` attribute on iframe for screen reader context |
| `.sr-only` utility | Used for visually-hidden labels where icon-only buttons are used |

> Note: Full WCAG 2.1 AA compliance requires manual testing with assistive technologies (NVDA, VoiceOver) and an expert accessibility audit beyond what's covered here.

---

## 7. Design Decisions and Rationale

**Why dark theme?**  
Developers and growth practitioners using this tool are often in code-heavy environments. Dark theme reduces eye strain in extended sessions and is the standard for dev tools. It also gives the amber accent more visual impact.

**Why a sidebar instead of a top navigation?**  
Session management is a persistent concern — users frequently switch between conversations. A sidebar makes all sessions always visible without taking up vertical space from the message area. This is the pattern established by Claude.ai, ChatGPT, and Perplexity.

**Why open the artifact viewer inline rather than in a modal?**  
A modal would interrupt the conversation. The inline panel lets users reference the chat while reading the artifact — especially useful for Ship 30 essays where the user may want to compare the essay against the Q&A that informed it.

**Why a confirm-on-second-click delete vs. a modal?**  
Modals interrupt flow for a low-frequency action. A "click once to prime, click again to confirm" pattern (with a 3-second reset) provides safety without context-switching overhead. The button color change to red is a clear visual signal.

**Why the skill selector is always visible?**  
Research from Hiten Shah's onboarding principles (one of our transcripts) shows that surfacing value paths before the action reduces drop-off. If skill selection were hidden in a menu, most users would never discover Ship 30 or artifact generation.
