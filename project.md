# CivicConnect — Project Reference

> **Audience:** AI agents and human contributors working on this repo. Read this before making changes.

CivicConnect is a dark-themed web assistant that helps Indian citizens navigate government **welfare schemes** and **legal acts** through a citation-verified AI chat ("citations over hallucinations"), plus browsable public directories of schemes and legislation. It currently runs **entirely on a mock frontend service layer**; a FastAPI RAG backend is planned but not yet connected.

---

## 1. Tech Stack & Tooling

| Concern | Choice | Notes |
|---|---|---|
| Framework | **Astro 7** (`astro.config.mjs`) | Static-first; React islands for interactive parts |
| UI islands | **React 19** via `@astrojs/react` | All `.tsx` files in `src/components/` |
| Styling | **Tailwind CSS v4** via `@tailwindcss/vite` | Tokens defined in `src/styles/global.css` `@theme` |
| Language | TypeScript, `astro/tsconfigs/strict` | `jsx: react-jsx`, `jsxImportSource: react` |
| Icons | Inline SVGs only | `lucide-react` is installed but **unused** (dead dep) |
| Node | `>=22.12.0` | Enforced in `package.json` engines |

### Commands

```sh
npm run dev        # dev server at localhost:4321  (see AGENTS.md for background mode)
npm run build      # production build → ./dist/
npm run preview    # preview the build
npm run astro check   # typecheck (.astro) — no test suite or linter configured yet
```

Per root `AGENTS.md`: manage the dev server with `astro dev --background`, `astro dev stop`, `astro dev status`, `astro dev logs`.

Agent skills available in-repo (use them): `astro`, `tailwind-4-docs`, `web-design-guidelines`, `vercel-react-best-practices`. `DESIGN.md` is the design source of truth.

---

## 2. Architecture Overview

```
src/
├── layouts/Layout.astro          # Base shell: <head>, OG meta, public header/footer,
│                                 # Ctrl/Cmd+K shortcut → /assistant, skip-link
├── styles/global.css             # Google Fonts import, Tailwind @theme tokens, utilities
├── services/
│   ├── api.ts                    # CivicConnectApi class + ALL shared types (single source)
│   └── mockData.ts               # Seed data + simulateAiResponse() keyword router
├── components/                   # React islands (see §4)
└── pages/*.astro                 # Static marketing/legal pages + thin island hosts
```

**Two rendering contexts share one component family:**

1. **Public directory pages** (`/welfare-schemes`, `/legal-info`) mount `*Browser.tsx` islands with `client:load`. They deep-link into the chat via plain anchors: `/assistant?query=<question>`.
2. **The app page** (`/assistant`) mounts `<AssistantApp client:only="react" />` (**note: `client:only`, not `client:load`** — deliberately skips SSR/hydration mismatch because `AssistantApp` touches `localStorage` in its constructor path). `Layout.astro` hides the public header/footer when `pathname.startsWith('/assistant')`.

`AssistantApp.tsx` (~320 lines) is the app root: owns all state (conversations, active view, jurisdiction, saved items, submitting/status flags) and passes callbacks down. Views: `'chat' | 'schemes' | 'laws' | 'saved' | 'settings'`.

### URL param integration

On load, `AssistantApp` reads `?query=` from the URL, strips it via `history.replaceState`, and sends it as a chat message into the active conversation. Any new surface that wants "ask the assistant about X" must link to `/assistant?query=...`.

---

## 3. Data Layer (`src/services/api.ts`)

- `const USE_MOCK = true;` (api.ts:70) — **the backend switch.** When `false`, `sendMessageStream` POSTs to `/api/chat`. Everything else stays mocked regardless.
- Persistence is **localStorage only**, written by `saveToStorage()`:

| Key | Contents |
|---|---|
| `civicconnect_history` | Full `Conversation[]` (seeded from `mockConversations` on first visit) |
| `civicconnect_saved_schemes` | Bookmarked `WelfareScheme[]` |
| `civicconnect_saved_acts` | Bookmarked `LegalAct[]` |

Language preference (en/hi/mr/ta/te in SettingsView) is **not persisted** — known gap.

### Core types (all exported from api.ts)

- `MessageStatus = 'sending' | 'understanding' | 'searching' | 'generating' | 'verifying' | 'verified' | 'error'`
- `Citation { id, actName, sectionNumber, jurisdiction, verified, excerpt, sourceUrl? }`
- `Message { id, role, content, timestamp, status?, citations?, feedback?, feedbackComment?, feedbackIssues? }`
- `Conversation { id, title, messages[], jurisdiction: 'central'|'state', stateName: string|null, timestamp }`
- `WelfareScheme { id, name, description, eligibility, benefits, requiredDocuments[], state, category, applicationProcess, sources: Citation[] }`
- `LegalSection { number, title, content }`; `LegalAct { id, name, description, sections[], jurisdiction, stateName? }`

Jurisdiction convention: `'central' | 'state'` + `stateName` (e.g. `"Maharashtra"`). Citation `jurisdiction` is free text (`"Central"` / `"State - <StateName>"`). State coverage in mock data: **Central + Maharashtra only** — filter dropdowns hardcode these strings.

---

## 4. RAG Pipeline Status Lifecycle ⭐

The chat simulates (and is wired for) a Retrieval-Augmented Generation backend. `sendMessageStream()` (api.ts:149) drives a **multi-step animated status flow** via `onUpdate(status)` callbacks consumed by `AssistantApp.setActiveStatus` → rendered by `ChatView.getStatusText` (ChatView.tsx:71):

| Order | Status | Sim delay | ChatView label | Meaning |
|---|---|---|---|---|
| 1 | `sending` | — | *(user msg renders)* | User message accepted, persisted |
| 2 | `understanding` | 1200 ms | `analyzing query context…` | Query intent parsing step |
| 3 | `searching` | 1500 ms | `retrieving legislative references…` | Vector/document retrieval step |
| 4 | `generating` | 1500 ms | `compiling context summary…` | LLM answer generation step |
| 5 | `verifying` | 1800 ms | `verifying citation alignments…` | Citation cross-check step |
| ✅ | `verified` | terminal | `sources verified` | Answer + citations committed to conversation |
| ❌ | `error` | terminal | error bubble | Any failure above |

Rules agents must preserve when touching chat code:

- Terminal states are **only** `verified` and `error` — `AssistantApp` clears `submitting` exclusively on those (AssistantApp.tsx:94).
- After every status update, `AssistantApp` re-fetches conversations to re-render streaming state.
- A `Message.status === 'verified'` gates the citation viewer + feedback buttons in `ChatView`.
- Citations carry their own boolean `verified` flag surfaced as "verified source"/"unverified" badges in `CitationViewer`.
- First user message auto-titles the conversation (25-char truncate, api.ts:171).

**Planned production contract** (USE_MOCK=false): `POST /api/chat` with `{ conversation_id, message, jurisdiction, state }` expecting `{ answer, citations[] }`. Error copy references the "FastAPI RAG server". No such backend exists yet.

### `simulateAiResponse()` keyword router (mockData.ts:193)

Mock answers are matched by lowercase substring rules, in order:
1. `ayushman | pmjay | pm-jay | health cover` → PM-JAY answer + citation
2. `rti | right to information | thirty days | respond` → RTI timelines + §7(1) citation
3. `kisan | farmer | pm-kisan` → PM-KISAN answer
4. `sanjay | pension` **and** `stateName === 'maharashtra'` → state pension answer
5. fallback → "offline/API-ready mode" message listing demo prompts, empty citations

When adding mock content, extend this router AND keep answers consistent with `mockData.ts` records — several UI tests are manual and rely on these prompts.

### Mock data inventory (mockData.ts)

- 2 seeded conversations (PM-JAY eligibility w/ 2 citations + feedback sample; RTI response times w/ 1 citation)
- 3 welfare schemes: PM-JAY (Central/Healthcare), PM-KISAN (Central/Agriculture), Sanjay Gandhi Niradhar Pension (Maharashtra/Social Welfare & Pension)
- 2 legal acts: RTI Act 2005 (3 sections), Bharatiya Nyaya Sanhita 2023 (2 sections)

Categories hardcoded in filters: Healthcare, Agriculture, Social Welfare & Pension.

---

## 5. Page Routes (`src/pages/`)

| Route | Island | Purpose |
|---|---|---|
| `/` | none | Marketing home: hero, capability cards, 4-step process |
| `/assistant` | `AssistantApp` (`client:only`) | The full chat application |
| `/welfare-schemes` | `WelfareSchemesBrowser` (`client:load`) | Scheme directory + detail modal |
| `/legal-info` | `LegalInfoBrowser` (`client:load`) | Acts directory + section modal |
| `/about`, `/how-it-works`, `/faq`, `/contact` | none | Static info pages (contact form submit is faked client-side) |
| `/sources-methodology` | none | Data sources + retrieval pipeline explanation |
| `/disclaimer`, `/privacy`, `/terms` | none | Legal notices (privacy documents localStorage behavior) |

All pages use `Layout.astro` (`title`/`description` props). FAQ uses native `<details>/<summary>`.

---

## 6. Component Map

In-app views (props-driven, used inside AssistantApp):
`Sidebar` (conversation list CRUD, nav tabs) · `ChatView` (message list, status animation, markdown-lite renderer, feedback triggers) · `Composer` (input + send) · `CitationViewer` (citation cards/excerpt modal) · `FeedbackModal` (helpful/not-helpful + 6 checkbox issues; fake 1200 ms submit) · `JurisdictionSelector` (central/state + state picker) · `WelfareSchemesView` · `LegalInfoView` · `SavedItemsView` (pure presentational) · `SettingsView` (profile/language/clear-data).

Public islands (self-contained, fetch nothing): `WelfareSchemesBrowser`, `LegalInfoBrowser`.

**Deliberate duplication:** `*View.tsx` (in-app, bookmarking callbacks) vs `*Browser.tsx` (public, modals, deep-links). They share mock data imports but not code. Keep feature parity in mind when changing either.

Both directories import `mockData` directly instead of calling `CivicConnectApi.search*/get*Details` — those service methods are currently **dead code** kept for the future API swap.

---

## 7. Design System

Source of truth: **`DESIGN.md`** (xAI-inspired near-black theme) implemented as Tailwind v4 tokens in `global.css`:

- Canvas `#0a0a0a` · card `#191919` · soft `#1a1c20` · hairline border `#212327`
- Text ramp: ink `#ffffff`, body `#dadbdf`, mute `#7d8187`
- Accents (rare, illustrative): sunset `#ff7a17`, dusk `#7c3aed`, twilight `#c4b5fd`, breeze `#a0c3ec`
- Fonts: **Inter** (sans, weight 400 display w/ tight negative tracking) + **Geist Mono** (uppercase tracked eyebrows) via Google Fonts import
- Every button is a **pill** (`rounded-full`); cards are 8px radius, hairline borders, **no shadows**
- Custom utilities live in `global.css` `@utility` blocks (`text-display-*`, `text-caption-mono`, `button-pill*`)
- Dark mode only — do not add light themes

---

## 8. Implementation Status Matrix

| Area | Status | Detail |
|---|---|---|
| Static pages + Layout | 🟢 Done | All 12 routes render; a11y skip-link, meta, manifest present |
| App shell / chat UI | 🟢 Done | Sidebar, chat, composer, citations, feedback, settings |
| Mock service layer | 🟢 Done | Full CRUD conversations + simulated RAG stream |
| localStorage persistence | 🟢 Done | History + bookmarks (language pref missing) |
| Directory pages | 🟢 Done | Search/filter/modal, deep-links into assistant |
| Real RAG backend | 🔴 Not started | Contract stubbed behind `USE_MOCK`; needs FastAPI + `/api/chat` |
| Auth | 🔴 Not started | Settings logout is `alert('Logout simulated…')`; Firebase/OAuth hinted |
| i18n | 🟡 Partial | Language selector exists (5 langs), never persisted, no translations |
| Tests / lint / CI | 🔴 None | Only `astro check` typecheck available |
| Multi-state coverage | 🟡 Partial | Central + Maharashtra only; filter lists hardcoded |

---

## 9. Known Quirks & Gotchas (read before editing)

1. **Stale-closure risk:** `handleJurisdictionChange` writes `JSON.stringify(conversations)` straight to localStorage (AssistantApp.tsx:143), bypassing `api.saveToStorage()` — can clobber authoritative storage. Route persistence changes through `CivicConnectApi`.
2. **Markdown renderer is minimal:** ChatView hand-renders headings/lists only; `**bold**` shows literally; single newlines collapse. Improve carefully — it's regex-based.
3. **`selectedScheme` in WelfareSchemesView is dead state** (declared, never rendered).
4. **Hardcoded filter options:** state names ('All', 'Central', 'Maharashtra') and categories duplicated as string literals across Browsers/Views instead of derived from data.
5. **`client:only` vs `client:load`:** don't switch AssistantApp to `client:load` without handling SSR guards (`typeof window` checks exist throughout api.ts).
6. **No comments culture:** codebase has zero TODO/FIXME markers and minimal comments — match existing style; don't add comment noise.
7. Timestamps are display strings (`toLocaleTimeString`), not ISO — sorting relies on array order.
8. `favicon.svg` is 71 KB (oversized); logo lives separately in `public/logo.svg`.

---

## 10. Contribution Workflow for Agents

1. Load the required skills first: `astro`, `tailwind-4-docs`, `web-design-guidelines`, `vercel-react-best-practices`; consult `DESIGN.md` for any visual work.
2. Shared types come **only** from `src/services/api.ts` — extend types there, never redefine locally.
3. New chat behavior must respect the status lifecycle in §4 (terminal states, callback refetch pattern).
4. New user-facing surfaces that reference topics should deep-link via `/assistant?query=...`.
5. New mock content = update `mockData.ts` **and** the `simulateAiResponse` router together.
6. Verify with `npm run astro check` after changes; there are no tests yet.
7. Never commit unless explicitly asked; follow existing dark-theme-only, pill-shaped, hairline-border design language.
