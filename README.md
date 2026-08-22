# CivicConnect

### A multi-agent, hybrid-RAG assistant for Indian law and welfare schemes

CivicConnect is an AI-powered civic and legal information assistant designed to help non-lawyers understand **Indian laws and government welfare schemes** in plain language.

The system is being designed to ground its answers in actual legal and government sources, reducing common problems with general-purpose AI systems such as fabricated section numbers, unsupported claims, and confusion between central and state-specific laws.

> 🚧 **Status: Early Development**
>
> CivicConnect is currently being developed in stages. The frontend application shell is under active development, while the backend RAG pipeline is being implemented separately.

---

## Problem

Many people in India cannot easily access legal assistance or do not know which government welfare schemes they may qualify for. As a result, rights and benefits that may be available to them can go unclaimed.

General-purpose AI assistants can make this problem worse when used for legal or civic questions. They may:

* Invent legal section numbers
* Provide unsupported legal claims
* Mix up central and state laws
* Give outdated scheme information
* Present uncertain information with excessive confidence

CivicConnect aims to address these problems by grounding responses in relevant source documents and providing supporting citations.

---

## Core Idea

CivicConnect is designed around three main ideas:

### 1. Hybrid Retrieval

Combine multiple retrieval approaches to find relevant source material:

* **Semantic retrieval** for understanding the meaning of a question
* **BM25 keyword retrieval** for exact terms and section numbers
* **Metadata/jurisdiction filtering** to distinguish central and state-specific information
* **Reciprocal Rank Fusion (RRF)** to combine retrieval results

### 2. Multi-Agent Pipeline

Use **LangGraph** to organize the AI workflow into separate stages:

```text
User Question
      ↓
Query Understanding
      ↓
Hybrid Retrieval
      ↓
Answer Synthesis
      ↓
Citation Verification
      ↓
Verified Answer
```

If a citation cannot be verified against the underlying source, the system is designed to regenerate the response rather than present an unverified citation.

### 3. Plain-Language Answers

The goal is not simply to retrieve legal text.

CivicConnect is intended to explain relevant laws and welfare schemes in language that ordinary citizens can understand while retaining links to the underlying sources.

---

# Current Development Status

The project is being developed by multiple team members across frontend and backend/RAG work.

## Progress

* [x] Project repository and initial setup
* [x] Frontend project structure
* [x] Public website pages
* [x] Interactive assistant frontend shell
* [x] Chat interface
* [x] Conversation management UI
* [x] Jurisdiction selection UI
* [x] Legal information browsing UI
* [x] Welfare scheme browsing UI
* [x] Citation/source interface
* [x] Saved items UI
* [x] Frontend API/service abstraction
* [x] Development mock data layer
* [ ] FastAPI backend integration
* [ ] Data ingestion and document processing
* [ ] Hybrid retrieval
* [ ] Dense retrieval
* [ ] BM25 retrieval
* [ ] RRF fusion
* [ ] Query understanding agent
* [ ] Answer synthesis agent
* [ ] Citation verification loop
* [ ] PostgreSQL integration
* [ ] Authentication
* [ ] Evaluation with RAGAS
* [ ] Citation accuracy evaluation

> **Note:** The current frontend contains development/mock data and simulated processing states so that frontend work can continue while the backend is being implemented. These are not the production RAG system.

---

# Technology Stack

## Current Frontend

| Technology   | Purpose                                  |
| ------------ | ---------------------------------------- |
| Astro        | Public website and application framework |
| React        | Interactive assistant application        |
| TypeScript   | Type-safe frontend development           |
| Tailwind CSS | Styling and design system                |
| Lucide React | Interface icons                          |

The current architecture uses Astro for public-facing pages and React for the interactive assistant.

```text
Astro
├── Public informational pages
│
└── React Assistant
        │
        ▼
   API Service Layer
```

## Planned Backend

| Technology            | Purpose                          |
| --------------------- | -------------------------------- |
| FastAPI               | Backend/API                      |
| PostgreSQL            | Application and metadata storage |
| LangGraph             | Multi-agent orchestration        |
| Groq / Llama          | Answer generation                |
| sentence-transformers | Semantic embeddings              |
| FAISS / ChromaDB      | Vector retrieval                 |
| rank_bm25             | Keyword retrieval                |
| RAGAS                 | RAG evaluation                   |

The frontend and backend are intentionally separated so that the RAG implementation can be integrated through the API layer later.

---

# Frontend

The current frontend provides the user-facing CivicConnect application.

## Main Assistant

The `/assistant` application provides:

* Conversational chat
* Multi-turn conversations
* Conversation history
* New conversations
* Message composer
* Jurisdiction selection
* AI processing states
* Citation display
* Source/evidence panels
* Feedback controls
* Saved items
* Legal information browsing
* Welfare scheme browsing
* Settings

The frontend currently simulates the intended processing lifecycle:

```text
Sending
   ↓
Understanding
   ↓
Searching
   ↓
Generating
   ↓
Verifying
   ↓
Verified
```

The actual processing will eventually be handled by the FastAPI/RAG backend.

---

# Public Website

The project also includes public informational pages:

```text
/
├── /about
├── /how-it-works
├── /faq
├── /contact
├── /sources-methodology
├── /legal-info
├── /welfare-schemes
├── /privacy
├── /terms
└── /disclaimer
```

These pages provide information about CivicConnect, its methodology, legal/welfare information, and important policies.

---

# Frontend Architecture

The current frontend is organized approximately as:

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
│   ├── legal-info.astro
│   ├── welfare-schemes.astro
│   ├── privacy.astro
│   ├── terms.astro
│   └── disclaimer.astro
│
├── services/
│   ├── api.ts
│   └── mockData.ts
│
└── styles/
    └── global.css
```

---

# API Integration

The frontend communicates with backend functionality through a dedicated service layer:

```text
src/services/api.ts
```

This layer defines the data structures and service methods required by the frontend.

The intended architecture is:

```text
React / Astro
      ↓
API Service
      ↓
FastAPI
      ↓
LangGraph
      ↓
RAG Pipeline
      ↓
Verified Response
      ↓
Frontend
```

The frontend should not contain RAG implementation logic.

The following belong to the backend:

* Embedding generation
* Vector search
* BM25
* RRF
* Query understanding
* LLM generation
* Citation verification
* Document processing
* RAGAS evaluation
* Database operations

---

# Development Mock Layer

Until the backend is available, the frontend uses a development mock layer:

```text
src/services/mockData.ts
```

The mock layer allows the team to test:

* Chat interactions
* Legal browsing
* Welfare scheme browsing
* Citation UI
* Source panels
* Loading states
* Verification states
* Saved items
* Other frontend interactions

Mock data should remain isolated from production API logic.

Once the backend is ready, the API service should be switched from mock data to the real FastAPI endpoints without requiring major changes to the UI components.

---

# Design System

The frontend follows the project's `DESIGN.md`.

The design is based on a dark, minimal interface with:

* Near-black canvas
* Charcoal surfaces
* Hairline borders
* Outline-pill controls
* Sans-serif display typography
* Geist Mono for structural labels
* Minimal/no drop shadows
* Responsive layouts

Before modifying existing UI components, contributors should review:

```text
DESIGN.md
```

The design document should be treated as the source of truth for the visual language.

---

# Project Structure

At the repository level, the project currently follows this general structure:

```text
CivicConnect/
├── public/
├── src/
├── DESIGN.md
├── README.md
├── package.json
├── astro.config.mjs
├── tsconfig.json
└── ...
```

Backend components will be added as the RAG implementation progresses.

---

# Getting Started

## Prerequisites

Make sure you have:

* Node.js
* npm
* Git

Backend-specific requirements will be documented when the FastAPI/RAG implementation is integrated.

---

## Install Dependencies

From the project root:

```bash
npm install
```

---

## Start Development Server

```bash
npm run dev
```

The Astro development server will normally be available at:

```text
http://localhost:4321
```

---

## Build for Production

```bash
npm run build
```

This generates the production build in:

```text
dist/
```

---

## Preview Production Build

```bash
npm run preview
```

---

## Astro Commands

You can also run Astro CLI commands through npm:

```bash
npm run astro ...
```

For help:

```bash
npm run astro -- --help
```

For type and Astro diagnostics:

```bash
npx astro check
```

---

# Development Workflow

CivicConnect is being developed in parallel across frontend and backend/RAG work.

When working on the frontend:

1. Check `DESIGN.md` before modifying the UI.
2. Keep frontend components independent of RAG implementation.
3. Use `src/services/api.ts` for backend communication.
4. Keep development mock data inside `src/services/mockData.ts`.
5. Do not hardcode production legal or welfare information into UI components.
6. Add appropriate loading, empty, success, and error states.
7. Test responsive behavior.
8. Run `npx astro check`.
9. Run `npm run build`.
10. Commit changes to the appropriate feature branch.

---

# Backend Integration

When the FastAPI/RAG backend becomes available, the frontend integration should follow:

```text
                    Frontend
                       │
                       ▼
                src/services/api.ts
                       │
                       │ HTTP
                       ▼
                    FastAPI
                       │
                       ▼
                   LangGraph
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Query       Retrieval     Synthesis
     Understanding                │
                                  ▼
                         Citation Verification
                                  │
                                  ▼
                           Verified Response
                                  │
                                  ▼
                              Frontend
```

The frontend should consume structured API responses rather than knowing how the RAG pipeline works internally.

---

# Planned RAG Pipeline

The intended backend pipeline is:

```text
User Question
      ↓
Query Understanding
      ↓
Jurisdiction Filtering
      ↓
Dense Retrieval + BM25
      ↓
RRF Fusion
      ↓
Relevant Source Passages
      ↓
Answer Synthesis
      ↓
Citation Verification
      ↓
      ├── Verification Failed → Regenerate
      │
      └── Verification Passed
                    ↓
              Final Answer
```

The goal is to ensure that answers are grounded in retrieved source material and that cited legal sections can be checked against their underlying documents.

---

# Data & Sources

The planned system will use legal and government source documents, including relevant central and state materials and welfare scheme information.

The data ingestion pipeline is still under development.

Planned work includes:

* Source collection
* Document cleaning
* Chunking
* Metadata extraction
* Jurisdiction labeling
* Embedding generation
* Keyword indexing
* Retrieval evaluation

Production source coverage will be documented as the data pipeline is implemented.

---

# Evaluation

The project will eventually evaluate the RAG system using metrics such as:

* RAGAS faithfulness
* Answer relevance
* Retrieval quality
* Citation accuracy
* Citation verification success rate

The evaluation pipeline is not yet implemented.

---

# Roadmap

## Phase 1: Foundation

* [x] Repository setup
* [x] Initial frontend setup
* [x] Design system
* [x] Public website
* [x] Assistant UI
* [x] Frontend service layer
* [x] Development mock layer

## Phase 2: Backend & Data

* [ ] Data ingestion
* [ ] Document cleaning/chunking
* [ ] Metadata and jurisdiction processing
* [ ] Dense retrieval
* [ ] BM25 retrieval
* [ ] RRF fusion
* [ ] FastAPI API

## Phase 3: Agent Pipeline

* [ ] Query understanding agent
* [ ] Retrieval agent
* [ ] Synthesis agent
* [ ] Citation verification
* [ ] Regeneration loop
* [ ] End-to-end RAG integration

## Phase 4: Persistence & Users

* [ ] PostgreSQL integration
* [ ] Authentication
* [ ] Conversation persistence
* [ ] Saved items persistence
* [ ] Feedback persistence

## Phase 5: Evaluation

* [ ] RAGAS evaluation
* [ ] Citation accuracy testing
* [ ] Retrieval evaluation
* [ ] End-to-end testing

---

# Contributing

CivicConnect is being developed as a team project.

Before contributing:

1. Pull the latest changes.
2. Create or switch to the appropriate feature branch.
3. Review `DESIGN.md` for frontend work.
4. Keep changes focused on the assigned feature.
5. Avoid modifying another team's work unless necessary.
6. Test your changes locally.
7. Run:

```bash
npx astro check
npm run build
```

8. Commit with a clear message.
9. Push your branch.
10. Open a pull request when the feature is ready for review.

Example:

```bash
git checkout -b frontend/chat-ui
git add .
git commit -m "Add chat interface"
git push -u origin frontend/chat-ui
```

---

# Project Status

> 🚧 **Early Development**

The frontend foundation and interactive application shell are currently under development.

The backend RAG pipeline is being developed separately and will be integrated through the frontend API service layer once available.

The project is **not yet production-ready**.

---

# License

License information will be added when the project license is finalized.
