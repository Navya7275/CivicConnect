# CivicConnect Frontend Walkthrough

This document provides an overview of the current **CivicConnect frontend**, including its architecture, implemented features, available pages, mock/API layer, current limitations, and instructions for running and testing the application locally.

CivicConnect is an AI-powered civic and legal assistant focused on helping citizens understand **Indian laws and government welfare schemes** through a conversational interface.

> **Current status:** The frontend shell and user-facing flows are implemented. The actual RAG/FastAPI backend is not connected yet. RAG processing and data are currently simulated through the frontend mock layer.

---

## 1. Technology Overview

The current frontend uses:

* **Astro** for the application/site framework
* **React** for interactive application components
* **TypeScript** for type-safe development
* Client-side state management for the assistant experience
* Mock service/data layer for development before backend integration

The intended architecture is:

```text
                    CivicConnect Frontend
                           │
              ┌────────────┴────────────┐
              │                         │
         Astro Pages              React Components
              │                         │
              └────────────┬────────────┘
                           │
                      API Service
                           │
                           ▼
                    Future FastAPI API
                           │
                           ▼
                    LangGraph + RAG
```

The frontend is intentionally separated from the RAG implementation so the backend can be connected later without rebuilding the UI.

---

# 2. Design & Theme

The design tokens live in `frontend/src/styles/global.css`; the component
patterns are in `frontend/src/components/`.

### Color System

* Background: `#0a0a0a`
* Card/background surfaces: `#191919`
* Border/separator: `#212327`
* No drop shadows

### Buttons & Controls

Interactive controls use the established outline-pill treatment:

* Rounded/full pill shape
* Semi-transparent white borders
* White border emphasis on hover

### Typography

The design uses:

* Sans-serif typography for major/display headings
* Tight negative letter spacing for display headings
* Geist Mono for structural labels and eyebrows
* Uppercase/tracked styling for technical or structural markers

> **Design rule:** Before changing a UI component or adding a style, read the
> tokens at the top of `frontend/src/styles/global.css` and reuse what is
> already there rather than introducing a parallel set.

---

# 3. Main Assistant Application

The main application is available at:

```text
/assistant
```

The assistant operates as a client-side application shell.

## Main responsibilities

The assistant currently manages:

* Current application view
* Conversations
* Selected jurisdiction/state
* User preferences
* Saved/bookmarked items
* Chat state
* Mock AI processing lifecycle

The main application coordinator is:

```text
src/components/AssistantApp.tsx
```

---

# 4. Conversation Sidebar

Component:

```text
src/components/Sidebar.tsx
```

The sidebar provides the primary navigation and conversation management interface.

### Current features

* Create a new conversation
* Display conversation history
* Search conversations
* Select/open a conversation
* Rename a conversation
* Delete a conversation
* Navigate to relevant application sections
* Access saved items/settings where applicable

The sidebar is designed to support the future backend conversation history API.

---

# 5. Chat Interface

Component:

```text
src/components/ChatView.tsx
```

The chat interface is the primary CivicConnect interaction.

### Current features

* User messages
* Assistant messages
* Conversation flow
* Message input
* Loading states
* AI processing states
* Citation display
* Response actions
* Retry/regeneration-related UI

The chat currently demonstrates the intended RAG lifecycle through simulated states.

---

# 6. Simulated RAG Processing Lifecycle

The frontend currently simulates the multi-stage processing workflow.

The current lifecycle is:

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

The interface displays the current stage using loading indicators and progress/status tags.

### Important

This is **only a frontend simulation**.

The actual CivicConnect RAG pipeline will eventually be handled by the backend using the project's planned retrieval, synthesis, and citation-verification pipeline.

When the FastAPI/RAG backend is available, the frontend should replace the simulated lifecycle with real API response states.

---

# 7. Citation Viewer

Component:

```text
src/components/CitationViewer.tsx
```

CivicConnect's answers are designed to provide supporting legal citations.

### Current UI features

Citation badges can display:

* Act/document name
* Section number
* Jurisdiction
* Verification status

Clicking a citation opens a detailed side drawer.

The drawer can display:

* Verification status
* Source excerpt
* Act/document information
* Official government URL
* Copy citation functionality

### Future backend integration

The citation data should eventually come from the FastAPI/RAG API.

The frontend should not perform citation verification itself.

The backend will provide the citation and verification information, and the frontend will render it.

---

# 8. Welfare Schemes

Component:

```text
src/components/WelfareSchemesView.tsx
```

Route:

```text
/welfare-schemes
```

The welfare scheme interface allows users to explore government welfare programs.

### Current features

* Browse available schemes
* Search schemes
* View scheme information
* Display relevant scheme details
* Ask the assistant about a selected scheme

The current information is provided by the mock data layer.

### Future integration

The mock scheme records will eventually be replaced with data returned from the backend/RAG system.

---

# 9. Legal Information

Component:

```text
src/components/LegalInfoView.tsx
```

Route:

```text
/legal-info
```

The legal information interface allows users to browse and search available legal information.

### Current features

* Search legal information
* Browse legal acts
* View act information
* View relevant sections
* Ask the assistant about a selected law/section

The current legal records are provided through the mock service layer.

---

# 10. Ask Assistant From Other Views

The welfare and legal information interfaces provide a direct way to move from browsing information to asking the assistant about it.

Example flow:

```text
Welfare Schemes
      ↓
Select Scheme
      ↓
Ask Assistant
      ↓
Assistant Chat
```

Similarly:

```text
Legal Information
      ↓
Select Act / Section
      ↓
Ask Assistant
      ↓
Assistant Chat
```

This allows the browsing experience and conversational experience to work together rather than functioning as isolated pages.

---

# 11. Bookmarks / Saved Items

The application supports saving useful information.

### Current functionality

Users can:

* Save items
* View saved items
* Remove saved items
* Accumulate saved bookmarks during the session

The current bookmark state is handled on the frontend.

### Future integration

Persistence can later be moved to the backend/database once authentication and backend APIs are implemented.

---

# 12. Public Website Pages

The project includes a public-facing informational website in addition to the assistant application.

The currently implemented routes are:

```text
/
├── /about
├── /how-it-works
├── /faq
├── /contact
├── /sources-methodology
├── /privacy
├── /terms
└── /disclaimer
```

These pages provide the public-facing context and supporting information around CivicConnect.

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

The homepage introduces CivicConnect and explains the overall user-facing workflow.

It includes:

* CivicConnect introduction
* Main application entry point
* Feature/workflow information
* Visual explanation of how the system works

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

Provides information about CivicConnect, its purpose, and the problem it aims to address.

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

Explains the CivicConnect workflow and how the assistant processes user questions.

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

Provides answers to common questions about CivicConnect and its functionality.

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

Provides the contact interface.

### Current features

* Form inputs
* Client-side validation
* Validation error states
* Submission/loading state
* Sending spinner
* Success/error handling

The actual email/contact backend can be integrated later.

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

Provides information about the sources and methodology behind CivicConnect.

This page is particularly useful because the project's core value is grounded legal and civic information rather than generic AI-generated answers.

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

The page should be reviewed and updated with the actual production data practices before deployment.

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

Provides the terms governing use of the CivicConnect platform.

The final production version should be reviewed and updated according to the actual application's policies and functionality.

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

Provides the legal/information disclaimer for CivicConnect.

Because CivicConnect deals with legal information, this page should remain accessible and should be kept consistent with the actual capabilities of the system.

---

# 13. API & Service Layer

File:

```text
src/services/api.ts
```

The API layer isolates frontend functionality from backend implementation.

It contains:

* API service methods
* TypeScript interfaces
* RAG-related request/response structures
* Search-related service methods
* Mock/real API switching

A developer toggle is currently available:

```text
USE_MOCK = true
```

### Current state

The application is using the mock implementation.

### Future state

When the FastAPI backend is ready, the API layer should be updated so the React components communicate with the real backend.

The UI components should not need to directly implement backend/RAG logic.

---

# 14. Mock Data

File:

```text
src/services/mockData.ts
```

This contains development data used to demonstrate the frontend before the backend is available.

Current mock records include examples such as:

### Welfare schemes

* Ayushman Bharat
* PM-Kisan
* Maharashtra Sanjay Gandhi pension-related scheme

### Legal information

* RTI Act
* BNS Act

### Important

These records exist only to support frontend development and demonstration.

They should not be treated as the production CivicConnect knowledge base.

When the backend/RAG system becomes available, the mock data should be disabled or removed from the production flow.

---

# 15. Backend Integration Plan

The frontend is designed so that the RAG backend can be connected later.

The intended architecture is:

```text
User
  │
  ▼
React UI
  │
  ▼
src/services/api.ts
  │
  │ HTTP request
  ▼
FastAPI
  │
  ▼
LangGraph
  │
  ├── Query Understanding
  ├── Hybrid Retrieval
  ├── Synthesis
  └── Citation Verification
  │
  ▼
FastAPI Response
  │
  ▼
React UI
```

The frontend should consume backend data such as:

* Answer
* Conversation ID
* Processing status
* Citations
* Source excerpts
* Jurisdiction
* Verification status
* Errors

The RAG implementation itself should remain outside the frontend.

---

# 16. Current Frontend vs Future Backend

| Feature              | Current State       | Future                       |
| -------------------- | ------------------- | ---------------------------- |
| Chat UI              | Implemented         | Connect to FastAPI           |
| Message input        | Implemented         | Send real API requests       |
| Conversation history | Frontend state      | Backend/database persistence |
| RAG lifecycle        | Simulated           | Real backend status          |
| Legal data           | Mock data           | RAG retrieval                |
| Welfare data         | Mock data           | RAG/backend data             |
| Citations            | Mock data           | Verified backend citations   |
| Source drawer        | Implemented         | Real source data             |
| Jurisdiction UI      | Implemented         | Backend-aware jurisdiction   |
| Bookmarks            | Frontend state      | Persistent backend storage   |
| Contact form         | Frontend validation | Backend/email integration    |
| Authentication       | UI-ready            | Backend authentication       |

---

# 17. Validation & Build Status

The current frontend has been checked successfully.

## Astro Diagnostics

Command:

```bash
npx astro check
```

Result:

```text
0 errors
14 warnings
```

The application currently contains no compiler errors according to the reported Astro diagnostics.

> Warnings should still be reviewed before production deployment.

---

## Production Build

Command:

```bash
npm run build
```

The current build successfully generates all reported pages.

Routes generated include:

```text
/
 /about
 /assistant
 /contact
 /disclaimer
 /faq
 /how-it-works
 /legal-info
 /privacy
 /sources-methodology
 /terms
 /welfare-schemes
```

Reported result:

```text
12 page(s) built successfully
```

---

# 18. Running the Project Locally

Install dependencies if required:

```bash
npm install
```

Start the development server:

```bash
npx astro dev
```

The application will normally be available at:

```text
http://localhost:4321
```

---

# 19. Recommended Frontend Testing Flow

After starting the development server, test the application in the following order.

### Assistant

1. Open `/assistant`.
2. Create a new conversation.
3. Send a question.
4. Confirm the processing lifecycle appears.
5. Confirm the final verified state appears.
6. Open a citation.
7. Check the citation drawer.
8. Test copying citation/source information.
9. Test retry/regeneration controls.

### Conversations

1. Create multiple conversations.
2. Search conversation history.
3. Open an existing conversation.
4. Rename a conversation.
5. Delete a conversation.
6. Create a new conversation again.

### Welfare Schemes

1. Open `/welfare-schemes`.
2. Search for a scheme.
3. Open scheme information.
4. Select **Ask Assistant**.
5. Confirm it navigates into the assistant flow.

### Legal Information

1. Open `/legal-info`.
2. Search for a law/act.
3. Open its information.
4. Select **Ask Assistant**.
5. Confirm the assistant flow receives the relevant context.

### Bookmarks

1. Save an item.
2. Open Saved Bookmarks.
3. Confirm the saved item appears.
4. Remove it.
5. Confirm it disappears.

### Responsive Testing

Test the application at:

* Desktop width
* Tablet width
* Mobile width

On mobile, verify:

* Hamburger navigation
* Sidebar overlay
* Chat usability
* Message composer
* Citation drawer
* Search interfaces
* Forms

---

# 20. Important Notes for Contributors

### Do not put RAG logic in the frontend

The frontend should not implement:

* Retrieval
* Embeddings
* BM25
* FAISS/ChromaDB
* RRF
* LangGraph
* LLM generation
* Citation verification

These belong to the backend/RAG implementation.

### Do not hardcode production legal information

Mock data is currently used only because the backend is not ready.

When the backend is available, update the service layer rather than rewriting the UI components.

### Use the API layer

New backend-dependent features should communicate through:

```text
src/services/api.ts
```

rather than making direct API calls from individual components.

### Follow the existing tokens

Before changing the UI, check:

```text
frontend/src/styles/global.css
```

Existing visual decisions should be preserved across new components and pages.

---

# 21. Current Project Status

The frontend currently provides a complete interactive application shell with:

* Public website
* AI assistant interface
* Conversation management
* Jurisdiction controls
* Simulated RAG processing states
* Citation/source interface
* Legal information browsing
* Welfare scheme browsing
* Saved/bookmarked information
* Contact and policy pages
* Responsive navigation
* API abstraction layer
* Mock data layer

The main remaining integration step is to connect the frontend service layer to the **actual FastAPI + RAG backend** once that implementation is available.

The frontend should therefore be treated as **UI-complete but backend-integration pending**.
