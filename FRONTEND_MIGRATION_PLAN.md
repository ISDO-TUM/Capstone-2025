# Frontend Framework Migration Plan
## From HTML/CSS/JS to React 19 + TypeScript + Vite + Tailwind

---

## 📋 Executive Summary

**Current State:**
- Server-rendered HTML templates (Jinja2) with vanilla JavaScript
- Single `script.js` file (~1600 lines) handling all client-side logic
- Custom CSS file (~1900 lines) with glassmorphism design
- No build process, direct file serving

**Target State:**
- React 19 SPA with TypeScript
- Vite 7 for dev/build tooling
- TailwindCSS 3 for styling
- Component-based architecture
- Type-safe API interactions

---

## 🔍 Detailed Feature Analysis

### **1. Pages/Routes**

#### **Dashboard (`/`)**
- **Features:**
  - Project list display (grid layout, 2 columns desktop, 1 column mobile)
  - Search bar (filters by title, description, tags)
  - Empty state when no projects
  - Project cards with:
    - Title, truncated description (4 lines max)
    - Tags display
    - Creation date (formatted with CET timezone)
    - Click to navigate to project
  - Scroll animations for cards
  - Responsive design

- **API Calls:**
  - `GET /api/getProjects` - Fetch all user projects

- **Key Functions:**
  - `loadProjectsFromAPI()`
  - `renderProjects(projects, isSearchResult)`
  - `filterProjectsBySearch(projects, searchValue)`
  - `animateCardsOnScroll()`

#### **Create Project (`/create-project`)**
- **Features:**
  - Form with title and description fields
  - Info tooltip explaining filter options
  - PDF upload (drag & drop or file picker)
  - PDF text extraction (auto-appends to description)
  - File validation (PDF only, max 50MB)
  - File preview with remove option
  - Form submission creates project and redirects

- **API Calls:**
  - `POST /api/extract-pdf-text` - Extract text from uploaded PDF
  - `POST /api/projects` - Create new project

- **Key Functions:**
  - `setupPDFUpload()`
  - `handleFileSelection(file)`
  - `extractPDFText(file)`
  - `removeFile()`

#### **Project Overview (`/project/:projectId`)**
- **Features:**
  - Project header with collapsible description (if >500 words)
  - Agent thoughts section (streaming updates)
  - Latest Papers section (PubSub/Newsletter papers)
  - Recommendations section with:
    - Search panel (title search, sort, filter)
    - Paper cards with:
      - Title, description, authors, year, venue
      - Metrics: Citations, FWCI, Percentile badges
      - Star rating (1-5)
      - Open Access badges
      - PDF/Read Paper links
    - Load More button
    - Results count
  - Out-of-scope handling (with new query input)
  - No-results handling (with filter details)
  - Paper replacement on low ratings (≤2 stars)
  - Notification popups for replacements/ratings

- **API Calls:**
  - `GET /api/project/:projectId` - Get project metadata
  - `POST /api/recommendations` - Stream recommendations (SSE)
  - `POST /api/load_more_papers` - Load additional papers (SSE)
  - `POST /api/rate_paper` - Rate a paper
  - `POST /api/pubsub/update_newsletter_papers` - Update newsletter papers
  - `GET /api/pubsub/get_newsletter_papers` - Get newsletter papers
  - `POST /api/project/:projectId/update_prompt` - Update project description

- **Key Functions:**
  - `loadProjectOverviewData(projectId, description, updateRecommendations)`
  - `fetchRecommendationsStream(...)` - SSE streaming
  - `createPaperCard(paper)` - Paper card rendering
  - `renderRecommendations(recommendations, container)`
  - `loadMorePapers(...)` - SSE streaming
  - `filterAndSortPapers()` - Client-side filtering/sorting
  - `renderOutOfScopeInThoughts(...)`
  - `renderNoResultsInThoughts(...)`
  - `setupCollapsibleDescription(description)`

---

### **2. UI Components**

#### **Header Component** (from `templates/components/header.html`)
- Logo and title
- "Create Project" button
- Clerk authentication user button
- Sticky header with glassmorphism

#### **Paper Card Component**
- Complex component with:
  - Title row with metrics (Citations, FWCI, Percentile)
  - Star rating (interactive, hover effects)
  - Description
  - Metadata (authors, year, venue)
  - Access badges (Open Access, PDF links)
  - Highlighting for new replacements
  - Data attributes for filtering (`data-paper-hash`, `data-title`, `data-rating`)

#### **Search Panel Component**
- Search input with clear button
- Sort dropdown (title, rating, relevance, year, citations, FWCI, percentile, OA)
- Filter dropdown (rated, unrated, open-access, closed-access)
- Results count display
- Clear buttons for each control

#### **Agent Thoughts Component**
- Streaming list of agent thoughts
- Icons for different thought types (🧠, 🛠️, ✅, 👤, 🏁)
- Out-of-scope subunit with expandable details
- No-results subunit with filter details
- New query input forms

#### **Notification System**
- Toast-style notifications
- Replacement notifications
- Rating confirmation notifications
- Auto-dismiss after 4 seconds

---

### **3. Styling System**

#### **Design System:**
- Glassmorphism (backdrop blur, semi-transparent backgrounds)
- Gradient backgrounds
- Custom color palette:
  - Primary: `#007bff` (blue)
  - Text: `#1a237e` (dark blue)
  - Background: Gradient from `#e3e9f0` to `#f7fafd`
- Border radius: 18-32px for buttons, 8-24px for cards
- Shadows: Multiple layers with rgba colors
- Animations: Fade-in, slide-in, scale transforms

#### **Key CSS Classes:**
- `.container` - Main content wrapper with glassmorphism
- `.project-card` - Project list cards
- `.recommendation-card` - Paper recommendation cards
- `.btn.btn-primary` - Primary button style
- `.search-panel` - Search controls container
- `.agent-thoughts-list` - Agent thoughts container
- Responsive breakpoints: 480px, 768px, 1100px, 1200px

---

### **4. State Management**

**Current (Vanilla JS):**
- Global variables: `window.currentRecommendations`, `window.currentDisplayCount`, `window.originalCardOrder`
- DOM-based state (data attributes on elements)
- No centralized state management

**Target (React):**
- React hooks for local state
- React Query for server state (recommendations, projects)
- Context API for global state if needed

---

### **5. API Integration**

**Endpoints Used:**
1. `GET /api/getProjects` - List projects
2. `POST /api/projects` - Create project
3. `GET /api/project/:projectId` - Get project details
4. `POST /api/project/:projectId/update_prompt` - Update project
5. `POST /api/recommendations` - Stream recommendations (SSE)
6. `POST /api/load_more_papers` - Load more papers (SSE)
7. `POST /api/rate_paper` - Rate paper
8. `POST /api/extract-pdf-text` - Extract PDF text
9. `POST /api/pubsub/update_newsletter_papers` - Update newsletter
10. `GET /api/pubsub/get_newsletter_papers` - Get newsletter papers

**SSE Streaming:**
- Two endpoints use Server-Sent Events
- Need to handle streaming in React (use `fetch` with `ReadableStream` or `EventSource`)

---

## 📐 Migration Strategy

### **Phase 1: Foundation Setup** ✅
- [x] Delete old frontend
- [x] Analyze old frontend completely
- [ ] Create new React project structure
- [ ] Set up Vite + TypeScript + Tailwind
- [ ] Install dependencies
- [ ] Set up routing (React Router)
- [ ] Create basic layout component

### **Phase 2: Core Infrastructure**
- [ ] Set up API client utilities
- [ ] Create React Query setup
- [ ] Set up SSE streaming utilities
- [ ] Create base UI components (Button, Card, Input, etc.)
- [ ] Set up Tailwind theme matching old design

### **Phase 3: Page Migration (One at a time)**

#### **3.1 Dashboard Page**
- [ ] Create Dashboard component
- [ ] Implement project list display
- [ ] Add search functionality
- [ ] Implement empty state
- [ ] Add project card component
- [ ] Add scroll animations
- [ ] Test responsive design

#### **3.2 Create Project Page**
- [ ] Create CreateProject component
- [ ] Implement form with validation
- [ ] Add PDF upload component
- [ ] Implement drag & drop
- [ ] Add PDF extraction integration
- [ ] Add tooltip component
- [ ] Test form submission

#### **3.3 Project Overview Page**
- [ ] Create ProjectOverview component
- [ ] Implement project header with collapsible description
- [ ] Create AgentThoughts component with SSE streaming
- [ ] Create LatestPapers component
- [ ] Create Recommendations component
- [ ] Create PaperCard component
- [ ] Create SearchPanel component
- [ ] Implement filtering and sorting
- [ ] Add Load More functionality
- [ ] Implement paper rating
- [ ] Add replacement logic
- [ ] Add out-of-scope handling
- [ ] Add no-results handling
- [ ] Add notification system

### **Phase 4: Styling Migration**
- [ ] Convert CSS classes to Tailwind
- [ ] Create custom Tailwind theme
- [ ] Add glassmorphism utilities
- [ ] Match animations and transitions
- [ ] Test responsive breakpoints
- [ ] Polish visual details

### **Phase 5: Integration & Testing**
- [ ] Integrate with backend APIs
- [ ] Test SSE streaming
- [ ] Test all user flows
- [ ] Fix bugs and edge cases
- [ ] Performance optimization
- [ ] Accessibility audit

### **Phase 6: Cleanup & Documentation**
- [ ] Remove old templates (keep as backup initially)
- [ ] Update backend to serve React build
- [ ] Update documentation
- [ ] Create component documentation

---

## 🎯 Component Architecture

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Base UI components (shadcn/ui style)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── select.tsx
│   │   │   ├── tooltip.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   └── Header.tsx
│   │   ├── project/
│   │   │   ├── ProjectCard.tsx
│   │   │   ├── ProjectList.tsx
│   │   │   └── ProjectSearch.tsx
│   │   ├── paper/
│   │   │   ├── PaperCard.tsx
│   │   │   ├── PaperMetrics.tsx
│   │   │   ├── StarRating.tsx
│   │   │   └── PaperList.tsx
│   │   ├── agent/
│   │   │   ├── AgentThoughts.tsx
│   │   │   ├── OutOfScopeSubunit.tsx
│   │   │   └── NoResultsSubunit.tsx
│   │   └── search/
│   │       ├── SearchPanel.tsx
│   │       └── FilterControls.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── CreateProject.tsx
│   │   └── ProjectOverview.tsx
│   ├── hooks/
│   │   ├── useRecommendationsStream.ts
│   │   ├── usePaperRating.ts
│   │   ├── usePDFUpload.ts
│   │   └── useSSE.ts
│   ├── lib/
│   │   ├── api.ts           # API client functions
│   │   ├── sse.ts            # SSE utilities
│   │   └── utils.ts
│   ├── types/
│   │   ├── project.ts
│   │   ├── paper.ts
│   │   └── api.ts
│   └── App.tsx
```

---

## 🔧 Technical Decisions

### **State Management:**
- **React Query** for server state (recommendations, projects)
- **React hooks** for local component state
- **Context API** only if needed for global UI state

### **SSE Streaming:**
- Use `fetch` with `ReadableStream` API
- Create custom hook `useSSE` or `useRecommendationsStream`
- Handle reconnection logic
- Clean up on unmount

### **Styling Approach:**
- TailwindCSS for utility-first styling
- Custom theme matching old design
- CSS variables for colors
- Custom utilities for glassmorphism effects

### **Type Safety:**
- Full TypeScript coverage
- Type definitions for all API responses
- Type-safe API client functions

---

## ⚠️ Risks & Considerations

1. **SSE Streaming Complexity:**
   - Need robust error handling
   - Reconnection logic
   - Memory management for long streams

2. **State Synchronization:**
   - Paper ratings need to sync with server
   - Filter/sort state vs. server state
   - Optimistic updates for ratings

3. **Performance:**
   - Large paper lists (virtualization if needed)
   - Search debouncing
   - Image/asset optimization

4. **Backward Compatibility:**
   - Ensure API contracts remain the same
   - Test with existing backend
   - Gradual migration possible?

---

## 📝 Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Start Phase 1** - Set up project structure
3. **Execute phase by phase** - One page at a time
4. **Test incrementally** - After each component/page
5. **Iterate** - Adjust plan as needed

---

## 🎨 Design System Notes

**Colors to preserve:**
- Primary Blue: `#007bff` / `#0056b3`
- Dark Blue: `#1a237e`
- Background Gradient: `#e3e9f0` → `#f7fafd`
- Text: `#222`, `#495057`, `#6c757d`
- Success: `#28a745`
- Warning: `#ffc107`
- Error: `#dc3545`

**Spacing:**
- Container padding: 20-60px (responsive)
- Card padding: 20-40px
- Gap between cards: 24-40px

**Typography:**
- Font: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`
- Headings: 700 weight
- Body: 400-500 weight

---

**Plan Created:** 2025-12-08
**Status:** Ready for Review

