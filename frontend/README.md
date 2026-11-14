# CivicConnect — Frontend

The user-facing web application for CivicConnect, built with **Astro** for high-performance static pages and **React islands** for the interactive legal assistant.

---

## Architecture

The frontend lives entirely inside `frontend/` and produces a fully static build (`dist/`) that can be hosted on any static hosting platform (Vercel, Netlify, GitHub Pages, or S3/CloudFront).

```text
frontend/
├── dist/                  # Static build output (12 pages)
├── public/                # Static assets, icons, web manifest
├── src/
│   ├── components/        # React interactive UI components
│   │   ├── AssistantApp.tsx          # App shell, view router & state management
│   │   ├── ChatView.tsx              # Chat interface, verified badges, retrieval breakdown
│   │   ├── CitationViewer.tsx        # Citation pill list & detailed drawer overlay
│   │   ├── Composer.tsx              # Multi-line chat input with keyboard shortcuts
│   │   ├── FeedbackModal.tsx         # Citizen feedback & citation issue reporting
│   │   ├── JurisdictionSelector.tsx  # Central vs State/UT selection
│   │   ├── LegalInfoBrowser.tsx      # Act & section browsing component
│   │   ├── LegalInfoView.tsx         # In-assistant legal browser panel
│   │   ├── SavedItemsView.tsx        # Saved schemes and legal acts
│   │   ├── SettingsView.tsx          # Language selection & clear history
│   │   ├── Sidebar.tsx               # Conversations list & view switching
│   │   ├── WelfareSchemesBrowser.tsx # Welfare schemes directory browser
│   │   └── WelfareSchemesView.tsx    # In-assistant schemes panel
│   ├── layouts/
│   │   └── Layout.astro              # Base HTML layout, styling & metadata
│   ├── pages/                        # Astro static route pages
│   │   ├── index.astro               # Landing homepage
│   │   ├── assistant.astro           # Interactive legal assistant application
│   │   ├── about.astro               # Project mission & team overview
│   │   ├── how-it-works.astro        # RAG & verification pipeline explanation
│   │   ├── legal-info.astro          # Public legal browser directory
│   │   ├── welfare-schemes.astro     # Public welfare schemes directory
│   │   ├── sources-methodology.astro # Data provenance & statutory sources
│   │   ├── faq.astro                 # Frequently asked questions
│   │   ├── privacy.astro             # Privacy policy & data handling principles
│   │   ├── terms.astro               # Terms of service
│   │   ├── disclaimer.astro          # Legal disclaimer
│   │   └── contact.astro             # Contact & feedback page
│   ├── services/
│   │   ├── api.ts                    # API client matching backend POST /query contract
│   │   └── mockData.ts               # Offline developmental mock data & verification
│   └── styles/
│       └── global.css                # Tailwind CSS v4 styling & theme tokens
├── astro.config.mjs
├── package.json
└── tsconfig.json
```

---

## Headline Features

1. **"Verified" Statutory Citations Badge**:
   Answers verified by the backend verification agent display a visible "Verified Statutory Answer" banner directly on the message card without requiring the citizen to open a separate drawer.
2. **Hybrid Retrieval Breakdown**:
   When retrieval scores are returned (`dense_score`, `bm25_rank`, `rrf_rank`), a collapsible breakdown table displays how semantic search and keyword search were combined into the final Reciprocal Rank Fusion ranking.
3. **Citation Drawer**:
   Clicking any source pill opens a full drawer displaying the governing Act, section, quoted verbatim excerpt, jurisdiction, and direct link to the authoritative government portal.
4. **Clarification Flow**:
   When a question depends on state-specific legislation (e.g. rent control or minimum wages) and no state is selected, the UI prompts the user to select their state rather than displaying an ungrounded answer.
5. **In-Memory Privacy**:
   Conversations are maintained in memory for the session only, ensuring citizens' sensitive legal questions are never silently stored in browser storage.

---

## Configuration

Configuration is passed via environment variables (see `.env.example` in repo root):

| Variable | Default | Purpose |
|---|---|---|
| `PUBLIC_USE_MOCK` | `true` | When `false`, requests go to the real FastAPI backend. When `true`, runs standalone with mock data. |
| `PUBLIC_API_BASE` | `http://localhost:8000` | Base URL of the backend API. Baked into the build by Vite. |

---

## Development

```bash
# Install dependencies
npm install

# Start local development server (defaults to http://localhost:4321)
npm run dev

# Run TypeScript and Astro diagnostics
npx astro check

# Build production static bundle (outputs to dist/)
npm run build

# Preview production build locally
npm run preview
```

---

## Ownership

Maintained by **Harshit Garg** (`[Frontend, Database & Deployment]`), per `docs/PROJECT_PLAN.md` §1.
