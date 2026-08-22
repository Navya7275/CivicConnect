# CivicConnect Frontend Implementation Plan

This document describes the implementation plan for the **CivicConnect frontend**, an AI-powered civic and legal information assistant focused on Indian laws and government welfare schemes.

The frontend is built on the existing **Astro project**, with **React** used for interactive application components. The implementation follows the visual and interaction guidelines defined in `DESIGN.md`.

> **Current architecture:** Astro + React + TypeScript + Tailwind CSS v4
> **Future backend:** FastAPI + LangGraph + RAG
> **Current data source:** Frontend mock/service layer
> **Production data source:** Future FastAPI/RAG API

---

# 1. Architecture Overview

CivicConnect uses Astro for the public-facing website and React for the highly interactive assistant application.

```text
                         CivicConnect
                              │
              ┌───────────────┴───────────────┐
              │                               │
       Public Website                    Assistant App
            Astro                            React
              │                               │
              └───────────────┬───────────────┘
                              │
                         API Service
                              │
                              ▼
                       Future FastAPI
                              │
                              ▼
                       LangGraph / RAG
```

### Public Website

Astro is responsible for:

* Landing page
* About
* How It Works
* FAQ
* Contact
* Sources/Methodology
* Privacy Policy
* Terms
* Disclaimer
* Public legal directory
* Public welfare scheme directory

These pages are primarily static and are intended to be lightweight and SEO-friendly.

### Interactive Assistant

React is responsible for the `/assistant` application.

It handles:

* Chat
* Conversation state
* Jurisdiction selection
* Citation interactions
* Feedback
* Bookmarks
* Legal browsing
* Welfare scheme browsing
* Application-level navigation

The assistant is mounted in Astro using the React integration.

---

# 2. Important Architectural Decisions

## React Integration in Astro

The project uses `@astrojs/react`.

The public pages remain Astro pages, while the complex assistant interface is implemented with React.

The `/assistant` page renders the React application as a client-side application using:

```text
client:only="react"
```

This is useful because the assistant relies on browser-side functionality such as:

* Client-side state
* `localStorage`
* Browser dimensions
* Interactive navigation
* Conversation state

This keeps the public website lightweight while allowing the assistant to behave like a full interactive application.

---

# 3. Styling & Design System

The frontend follows the existing `DESIGN.md` specification.

## Tailwind CSS

Tailwind CSS v4 is integrated through:

```text
@tailwindcss/vite
```

The Vite plugin is configured through the Astro configuration.

## Global Design Tokens

The central stylesheet is:

```text
src/styles/global.css
```

It contains:

* Tailwind imports
* Custom design tokens
* Application colors
* Typography
* Spacing
* Border/radius values
* Scrollbar styles
* Input overrides
* Animation utilities

The design uses a near-black/xAI-inspired visual system including:

* Canvas: `#0a0a0a`
* Cards: `#191919`
* Hairline borders: `#212327`
* Primary text: `#ffffff`

The exact visual implementation should always follow `DESIGN.md`.

---

# 4. Dependencies & Build Configuration

## `package.json`

The project requires:

* `react`
* `react-dom`
* `@astrojs/react`
* `tailwindcss`
* `@tailwindcss/vite`
* `lucide-react`

### Purpose

| Dependency          | Purpose                      |
| ------------------- | ---------------------------- |
| React               | Interactive application UI   |
| React DOM           | React browser rendering      |
| `@astrojs/react`    | React integration with Astro |
| Tailwind CSS        | Utility-based styling        |
| `@tailwindcss/vite` | Tailwind v4 Vite integration |
| Lucide React        | Interface icons              |

---

# 5. Astro Configuration

File:

```text
astro.config.mjs
```

The configuration integrates:

* React
* Tailwind CSS v4
* Vite configuration

This allows Astro pages and React components to coexist within the same project.

---

# 6. Global Layout

File:

```text
src/layouts/Layout.astro
```

The global layout is used by the public website pages.

It provides:

* HTML document structure
* Viewport configuration
* SEO title
* Meta descriptions
* Global styles
* Font imports
* Navigation header
* Footer

## Navigation

The public navigation provides access to relevant areas such as:

* Home
* Assistant
* Welfare Schemes
* Laws
* FAQ
* About

## Footer

The footer provides access to:

* Terms
* Privacy Policy
* Disclaimer

Additional links can be added as the project evolves.

---

# 7. Public Website Pages

The public-facing website provides useful information about CivicConnect in addition to the interactive assistant.

---

## Home

File:

```text
src/pages/index.astro
```

Route:

```text
/
```

The homepage introduces CivicConnect and directs users toward the assistant.

It includes:

* Main CivicConnect introduction
* Primary call-to-action
* Overview of legal capabilities
* Overview of welfare capabilities
* Explanation of the general workflow
* Visual workflow/timeline

---

## About

File:

```text
src/pages/about.astro
```

Route:

```text
/about
```

Explains:

* CivicConnect's purpose
* The problem being addressed
* Accessibility of legal information
* Welfare scheme discoverability
* Intended users
* Project/team context where appropriate

---

## How It Works

File:

```text
src/pages/how-it-works.astro
```

Route:

```text
/how-it-works
```

Explains the CivicConnect workflow in plain language.

The intended flow is:

```text
User Question
      ↓
Question Understanding
      ↓
Relevant Information Retrieval
      ↓
Answer Generation
      ↓
Citation Verification
      ↓
Verified Answer
```

The page should explain this without requiring users to understand RAG or AI terminology.

---

## FAQ

File:

```text
src/pages/faq.astro
```

Route:

```text
/faq
```

Provides answers to common questions about:

* CivicConnect
* Legal information
* Welfare schemes
* Sources
* Citations
* Accuracy
* Limitations
* Appropriate use of the assistant

A legal/information disclaimer should remain accessible from this page.

---

## Contact

File:

```text
src/pages/contact.astro
```

Route:

```text
/contact
```

Provides a contact form.

Fields include:

* Name
* Email
* Message

The frontend should provide:

* Input validation
* Required-field validation
* Email validation
* Focus states
* Validation errors
* Loading/submission state
* Success state
* Error state

The actual contact submission service can be integrated later.

---

## Sources & Methodology

File:

```text
src/pages/sources-methodology.astro
```

Route:

```text
/sources-methodology
```

Explains the general information-retrieval methodology used by CivicConnect.

The page can discuss:

* Legal and government sources
* Central and state sources
* Document retrieval
* Citation-based answers
* Verification methodology

Production content should accurately reflect the actual backend implementation once the RAG system is completed.

---

## Privacy Policy

File:

```text
src/pages/privacy.astro
```

Route:

```text
/privacy
```

Provides the application's privacy information.

The final production version must accurately describe the actual data collection, storage, cookies, analytics, authentication, and logging practices used by the application.

---

## Terms of Service

File:

```text
src/pages/terms.astro
```

Route:

```text
/terms
```

Provides the rules governing use of CivicConnect.

The final version should be reviewed against the actual production functionality.

---

## Disclaimer

File:

```text
src/pages/disclaimer.astro
```

Route:

```text
/disclaimer
```

Provides a clear legal/information disclaimer.

It should explain that CivicConnect is an informational tool and does not replace professional legal advice.

---

## Welfare Schemes Directory

File:

```text
src/pages/welfare-schemes.astro
```

Route:

```text
/welfare-schemes
```

Provides a public directory for exploring welfare schemes.

Features include:

* Search
* Browse schemes
* State filtering
* Category filtering
* Scheme list
* Scheme information

Actual production scheme information should eventually come from the backend/data layer.

---

## Legal Information Directory

File:

```text
src/pages/legal-info.astro
```

Route:

```text
/legal-info
```

Provides a public directory for exploring legal information.

Features include:

* Search
* Browse laws
* Central/state filtering
* Act information
* Section information

Actual production legal information should eventually come from the backend/data layer.

---

# 8. API & Service Layer

File:

```text
src/services/api.ts
```

The API service layer separates frontend components from backend implementation.

It defines TypeScript contracts for objects such as:

* `Message`
* `Citation`
* `Conversation`
* `WelfareScheme`
* `LegalAct`
* `Jurisdiction`

It also provides service methods for operations such as:

* Sending chat messages
* Searching laws
* Searching welfare schemes
* Sending feedback
* Managing application data

---

# 9. Mock Data Layer

File:

```text
src/services/mockData.ts
```

The mock data layer exists because the actual RAG/FastAPI backend is not yet available.

It provides development data for:

* Legal documents
* Welfare schemes
* Citations
* Eligibility information
* Benefits
* Other UI states

Examples include:

* Ayushman Bharat PM-JAY
* PM-KISAN
* State welfare schemes
* RTI-related legal information
* BNS-related legal information

## Important

Mock data is for **frontend development and visual testing only**.

It should not be treated as the production CivicConnect knowledge base.

When the real backend becomes available, the frontend should switch from mock services to the real API through `api.ts`.

---

# 10. Mock/Real API Switching

The frontend service layer uses a development toggle:

```text
USE_MOCK = true
```

### Current development mode

```text
React
  ↓
api.ts
  ↓
Mock Data
```

### Future production mode

```text
React
  ↓
api.ts
  ↓
FastAPI
  ↓
LangGraph + RAG
```

This approach allows frontend development to continue independently while the backend is being implemented.

---

# 11. Interactive Assistant

File:

```text
src/pages/assistant.astro
```

Route:

```text
/assistant
```

The Astro page mounts:

```text
AssistantApp.tsx
```

using the React integration.

The assistant acts as the main interactive CivicConnect application.

---

# 12. Assistant Application Shell

File:

```text
src/components/AssistantApp.tsx
```

This is the main application orchestrator.

It manages application-level state including:

* Current view
* Active conversation
* Conversation history
* Saved items
* Language preference
* Active jurisdiction
* Navigation state

Current views include:

```text
chat
schemes
laws
saved
settings
```

The application switches between these views without requiring a full page reload.

---

# 13. Sidebar

File:

```text
src/components/Sidebar.tsx
```

The sidebar provides application navigation and conversation management.

Features include:

* CivicConnect branding
* New Chat
* Conversation search
* Recent conversations
* Active conversation indicator
* Browse schemes
* Browse laws
* Saved items
* Settings
* Profile information

Conversation actions include:

* Rename
* Delete
* Open/select

---

# 14. Chat View

File:

```text
src/components/ChatView.tsx
```

The chat view handles the main conversation interface.

It provides:

* Message list
* User messages
* Assistant messages
* Timestamps
* Markdown-rendered responses
* Copy response action
* Helpful/not helpful controls
* Citation badges
* Processing states
* Verification states
* Empty chat state

The chat interface is designed for multi-turn conversations.

---

# 15. Message Composer

File:

```text
src/components/Composer.tsx
```

The composer is responsible for user message input.

Features include:

* Multi-line input
* Auto-growing text area
* Enter to submit
* Shift + Enter for a new line
* Submit/loading state
* Input clearing after submission
* Disabled state when appropriate

The component should remain independent from RAG implementation.

---

# 16. Jurisdiction Selector

File:

```text
src/components/JurisdictionSelector.tsx
```

CivicConnect needs to distinguish between central and state-specific information.

The component provides:

* Central jurisdiction option
* State jurisdiction option
* State selector
* Searchable state list
* Current jurisdiction indicator

Example states include:

* Maharashtra
* Karnataka
* Tamil Nadu
* Delhi
* Bihar

The selected jurisdiction is frontend state and will eventually be sent to the backend API.

The frontend should not implement legal jurisdiction detection.

---

# 17. Citation Viewer

File:

```text
src/components/CitationViewer.tsx
```

The citation viewer displays supporting information for assistant responses.

Features include:

* Inline citation badges
* Act/document name
* Section number
* Jurisdiction
* Verification status
* Supporting excerpt
* Official source URL
* Copy citation
* Drawer/sidebar source panel

The actual verification process belongs to the backend.

The frontend only renders the verification result returned by the API.

---

# 18. Feedback Modal

File:

```text
src/components/FeedbackModal.tsx
```

Provides a structured feedback interface for AI responses.

Possible predefined feedback categories include:

* Inaccurate citation
* Confusing language
* Outdated welfare information
* Other issue

Users can also provide optional written feedback.

The component should provide:

* Validation
* Submission state
* Success state
* Error state

The actual feedback persistence can be connected to the backend later.

---

# 19. Welfare Schemes View

File:

```text
src/components/WelfareSchemesView.tsx
```

Provides an interactive welfare scheme browsing experience.

Features include:

* Scheme cards
* Search
* Eligibility filters
* Scheme information
* Benefits
* Required documents
* Citations
* "Ask CivicConnect about this scheme"

The current data can come from `mockData.ts`.

Production data should eventually come from the backend.

---

# 20. Legal Information View

File:

```text
src/components/LegalInfoView.tsx
```

Provides interactive legal information browsing.

Features include:

* Search laws
* Browse acts
* View sections
* Jurisdiction information
* Source information
* "Ask CivicConnect about this law"

Selecting "Ask CivicConnect" should:

1. Switch to the chat view.
2. Preserve relevant context.
3. Pre-fill the message composer where appropriate.

---

# 21. Saved Items View

File:

```text
src/components/SavedItemsView.tsx
```

Displays saved user information.

Possible saved content includes:

* Welfare schemes
* Laws
* Citations
* AI answers

Features include:

* Saved item list/grid
* Open saved item
* Remove saved item
* Empty state

Current persistence may remain client-side until backend authentication/storage is available.

---

# 22. Settings View

File:

```text
src/components/SettingsView.tsx
```

Provides application settings.

Features include:

* Profile information
* Language selection
* Text sizing/preferences where supported
* Account settings
* Logout

Potential language options include:

* English
* Hindi
* Bengali
* Other supported languages

Actual localization should only be enabled once the corresponding translations are available.

---

# 23. Accessibility & Interface Guidelines

All components should follow basic accessibility requirements.

## Focus States

Interactive controls should have visible focus states.

Example:

```text
focus-visible:ring-2
```

or the equivalent design-system implementation.

## Icon Buttons

Icon-only buttons should include appropriate:

* `aria-label`
* Tooltip where appropriate
* Keyboard accessibility

## Semantic HTML

Use appropriate semantic elements:

* `header`
* `nav`
* `main`
* `aside`
* `section`
* `footer`
* `button`
* `form`

Avoid using clickable `<div>` elements where a semantic interactive element is appropriate.

## Forms

Forms should provide:

* Labels
* Validation
* Error messages
* Accessible input states
* Keyboard navigation

---

# 24. Backend Integration Boundary

The frontend should not implement the RAG pipeline.

The intended responsibility split is:

```text
                 FRONTEND
                    │
                    ▼
              User Question
                    │
                    ▼
              API Service
                    │
                    ▼
                 FASTAPI
                    │
                    ▼
               LANGGRAPH
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
     Query       Retrieval   Synthesis
   Understanding               │
                                ▼
                         Citation Verification
                                │
                                ▼
                           API Response
                                │
                                ▼
                             Frontend
```

The backend/RAG team owns:

* Query understanding
* Embeddings
* FAISS/ChromaDB
* BM25
* Reciprocal Rank Fusion
* LangGraph
* LLM generation
* Citation verification
* RAGAS evaluation
* Database integration

The frontend owns:

* User input
* UI state
* API requests
* Response rendering
* Citation display
* Source display
* Error/loading states
* Navigation
* User interactions

---

# 25. No Hardcoded Fake RAG Responses

The frontend should not pretend that the RAG system is already operational.

During development, mock data can be used for:

* UI development
* Interaction testing
* Empty states
* Loading states
* Citation UI
* Scheme/law browsing

However:

* Do not present mock answers as production AI responses.
* Do not build RAG logic inside React.
* Do not hardcode citations into production components.
* Do not implement legal verification in the frontend.

The mock layer should remain isolated and easy to remove or disable.

---

# 26. Responsive Design

The application should support:

* Desktop
* Tablet
* Mobile

The assistant should remain usable on smaller screens.

Important mobile behavior includes:

* Collapsible/hamburger sidebar
* Sidebar overlay
* Responsive chat area
* Responsive message composer
* Citation drawer/overlay
* Responsive search/filter controls
* Accessible forms

All responsive behavior should remain consistent with `DESIGN.md`.

---

# 27. Verification Plan

## Automated Verification

Run:

```bash
npm run build
```

to verify the production build.

Also run:

```bash
npx astro check
```

to verify Astro and TypeScript diagnostics.

Both should complete without compiler/type errors.

Warnings should be reviewed where relevant.

---

# 28. Manual Verification

Start the development server:

```bash
npm run dev
```

Then verify the following.

## Public Website

Check:

* Homepage
* Navigation
* Footer
* About
* FAQ
* How It Works
* Contact
* Sources/Methodology
* Privacy
* Terms
* Disclaimer
* Legal Information
* Welfare Schemes

## Assistant

Check:

* `/assistant`
* New conversation
* Conversation switching
* Message input
* Multi-line messages
* Loading states
* RAG processing animation
* Verification state
* Citation badges
* Citation drawer
* Copy actions
* Feedback

## Jurisdiction

Check:

* Central selection
* State selection
* State search
* State changes
* Current jurisdiction indicator

## Legal Information

Check:

1. Search for a law.
2. Open the law.
3. View section information.
4. Select "Ask CivicConnect".
5. Confirm navigation to chat.
6. Confirm relevant context is preserved/prefilled.

## Welfare Schemes

Check:

1. Search for a scheme.
2. Open scheme details.
3. Review eligibility/benefits/documents.
4. Select "Ask CivicConnect".
5. Confirm navigation to chat.

## Saved Items

Check:

1. Save a scheme, law, citation, or answer.
2. Open Saved Items.
3. Confirm it appears.
4. Remove the item.
5. Confirm it disappears.

## Responsive Testing

Test:

* Desktop
* Tablet
* Mobile

Pay particular attention to:

* Sidebar
* Chat composer
* Citation drawer
* Search interfaces
* Forms
* Navigation

---

# 29. Project Development Workflow

When adding a new frontend feature:

1. Check `DESIGN.md`.
2. Determine whether the feature belongs to Astro or React.
3. Create/reuse a dedicated component.
4. Add required TypeScript types.
5. Keep API interaction inside `src/services/api.ts`.
6. Add loading/empty/error states.
7. Test desktop and mobile behavior.
8. Run `npx astro check`.
9. Run `npm run build`.
10. Test the feature manually before committing.

---

# 30. Current Development Status

The frontend is structured as an **Astro + React application**.

The current implementation provides:

* Public informational pages
* Interactive React assistant
* Conversation management
* Jurisdiction controls
* Legal information browsing
* Welfare scheme browsing
* Citation/source UI
* Feedback UI
* Saved items
* Settings
* Responsive behavior
* Mock API/data layer
* Future-ready API boundary

The primary remaining integration is connecting:

```text
src/services/api.ts
```

to the actual **FastAPI + LangGraph/RAG backend**.

Once the backend is ready, the frontend should be able to replace the mock implementation with real API calls while preserving the existing UI and component architecture.

---

# 31. Key Files at a Glance

```text
src/
├── components/
│   ├── AssistantApp.tsx
│   ├── Sidebar.tsx
│   ├── ChatView.tsx
│   ├── Composer.tsx
│   ├── JurisdictionSelector.tsx
│   ├── CitationViewer.tsx
│   ├── FeedbackModal.tsx
│   ├── WelfareSchemesView.tsx
│   ├── LegalInfoView.tsx
│   ├── SavedItemsView.tsx
│   └── SettingsView.tsx
│
├── layouts/
│   └── Layout.astro
│
├── pages/
│   ├── index.astro
│   ├── assistant.astro
│   ├── about.astro
│   ├── how-it-works.astro
│   ├── faq.astro
│   ├── contact.astro
│   ├── sources-methodology.astro
│   ├── privacy.astro
│   ├── terms.astro
│   ├── disclaimer.astro
│   ├── welfare-schemes.astro
│   └── legal-info.astro
│
├── services/
│   ├── api.ts
│   └── mockData.ts
│
└── styles/
    └── global.css
```

---

# 32. Final Architecture

The current project should be understood as:

```text
                         CIVICCONNECT
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
      Public Website                       AI Assistant
          Astro                              React
            │                                   │
            │                                   │
            └─────────────────┬─────────────────┘
                              │
                         API Service
                       src/services/api.ts
                              │
                   ┌──────────┴──────────┐
                   │                     │
              Current Mock          Future API
                   │                     │
              mockData.ts             FastAPI
                                         │
                                         ▼
                                  LangGraph + RAG
                                         │
                              ┌──────────┴──────────┐
                              │                     │
                         Retrieval             Verification
                              │                     │
                              └──────────┬──────────┘
                                         │
                                         ▼
                                  Verified Response
                                         │
                                         ▼
                                  CivicConnect UI
```

The key principle is to keep the **frontend and RAG loosely coupled**. The frontend should provide the complete citizen-facing experience while the backend team independently implements retrieval, generation, verification, and persistence.
