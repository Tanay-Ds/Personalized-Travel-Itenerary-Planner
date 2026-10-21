# Personalized Travel Itinerary Planner

> AI-powered, full-stack web application that generates personalized day-by-day travel itineraries using Google Gemini & Groq LLMs.

---

## 🔗 Live Links

| Resource | URL |
|----------|-----|
| 🌐 **Live Web App** | [personalized-travel-itenerary-planner-ob42m5s4v-tanay-e4be.vercel.app](https://personalized-travel-itenerary-planner-ob42m5s4v-tanay-e4be.vercel.app/) |
| ⚙️ **Backend API** | [personalized-travel-itenerary-planner.onrender.com](https://personalized-travel-itenerary-planner.onrender.com) |
| 📖 **Interactive API Docs (Swagger)** | [personalized-travel-itenerary-planner.onrender.com/docs](https://personalized-travel-itenerary-planner.onrender.com/docs) |
| 🗄️ **Database (Supabase Project)** | Project ID: `vskaghlmvjqambnrshhy` |
| 💻 **GitHub Repository** | [Tanay-Ds/Personalized-Travel-Itenerary-Planner](https://github.com/Tanay-Ds/Personalized-Travel-Itenerary-Planner) |

---

## 📌 Project Overview

The **Personalized Travel Itinerary Planner** is a full-stack, AI-powered web application that simplifies travel planning through intelligent automation and personalized recommendations. Built with a React frontend, FastAPI backend, and Supabase integration, it generates customized day-by-day itineraries based on user preferences, budget, and travel style using prompt engineering and generative AI. The system delivers optimized plans that include attractions, dining, accommodations, and transportation in a clear and structured format.

With a modern SaaS-style dashboard, smart trip builder, and interactive itinerary view, the platform reduces decision fatigue and saves planning time. Users can quickly generate, save, edit, and regenerate trips while receiving curated recommendations tailored to their needs.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS v4, shadcn/ui |
| **Backend** | Python, FastAPI, Pydantic, Uvicorn |
| **Database** | Supabase (PostgreSQL + Row-Level Security) |
| **Authentication** | Supabase Auth (JWT / JWKS) |
| **AI — Primary** | Google Gemini 2.5 Flash |
| **AI — Fallback** | Groq LLama 3.3 70B |
| **State Management** | TanStack React Query |
| **Forms & Validation** | React Hook Form + Zod |
| **Drag & Drop** | dnd-kit |
| **Deployment — Frontend** | Vercel |
| **Deployment — Backend** | Render |

---

## ✨ Key Features

- 🤖 **AI Itinerary Generation** — Complete day-by-day plan generated in 10–30 seconds
- 💰 **Budget Tracking** — Per-activity, per-day, and total trip cost estimation
- 🎯 **Personalization** — Travel style (relaxed / balanced / packed), interests, group size
- 🔄 **Day Regeneration** — Regenerate any single day without touching the rest
- ✏️ **Activity Management** — Edit, delete, drag-and-drop reorder activities
- 🔐 **Secure & Private** — JWT auth + 14 Row-Level Security policies
- 🔁 **LLM Fallback** — Auto-switches Gemini → Groq on failure
- 📱 **Responsive** — Works on mobile and desktop

---

## 👥 Use Case Scenarios

* **Scenario 1: Solo Traveler Planning a Weekend Getaway**
  A solo traveler enters their destination, budget, travel dates, and interests. Within seconds, the system generates a balanced itinerary that optimizes travel time, suggests nearby attractions, and recommends affordable dining spots — no hours of cross-site research needed.

* **Scenario 2: Couple Planning a Personalized Vacation**
  A couple selects preferences like relaxed pacing, scenic spots, and premium stays. The platform uses AI to create a day-wise itinerary including curated restaurants, unique experiences, and optimized travel routes. They can modify activities, regenerate specific days, and track estimated costs.

* **Scenario 3: Small Group Coordinating a Multi-Day Trip**
  A group of friends inputs group size and combines preferences such as adventure, culture, and budget limits. The system automatically structures activities, allocates time efficiently, and provides logistics suggestions to minimize conflicts and travel delays.

---

## 📁 Project Documentation

All 22 project documents (SmartBridge / SkillWallet template format) are included in this repository:

| Phase | Documents |
|-------|-----------|
| **1. Brainstorming & Ideation** | Define Problem Statements, Empathy Map, Brainstorming & Idea Prioritization |
| **2. Requirement Analysis** | Solution Requirements, Customer Journey Map, Technology Stack, Data Flow Diagram |
| **3. Project Design Phase** | Problem-Solution Fit, Proposed Solution, Solution Architecture |
| **4. Project Planning Phase** | Project Planning |
| **5. Project Development Phase** | Coding & Solution, Code Layout Readability & Reusability, Functional Features |
| **6. Project Testing** | Performance Testing |
| **7. Project Documentation** | Project Executable Files, Sample Project Documentation |
| **8. Project Demonstration** | Demo Planning, Feature Demonstration, Scalability & Future Plan, Team Involvement, Communication |

---

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `profiles` | User profile with display name and preferences |
| `trips` | Trip metadata (destination, dates, budget, style) |
| `itinerary_days` | Per-day summaries and costs |
| `activities` | Individual activities with times, locations, costs |
| `trip_members` | Collaborative access (editor / viewer roles) |
| `generation_logs` | AI generation audit trail |

---

## 🚀 Local Setup

### Backend
```bash
git clone https://github.com/Tanay-Ds/Personalized-Travel-Itenerary-Planner.git
cd Personalized-Travel-Itenerary-Planner/backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
# Create .env from .env.example and fill in Supabase + LLM keys
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
# Create .env from .env.example
npm run dev
```

### Run Tests
```bash
cd backend && pytest tests/ -v
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/me` | Current user profile |
| `POST` | `/api/trips/generate` | **Generate AI itinerary** |
| `GET` | `/api/trips` | List all trips |
| `GET` | `/api/trips/{id}` | Trip detail with full itinerary |
| `PATCH` | `/api/trips/{id}` | Update trip metadata |
| `DELETE` | `/api/trips/{id}` | Delete trip |
| `POST` | `/api/trips/{id}/days/{n}/regenerate` | Regenerate single day |
| `POST` | `/api/trips/{id}/days/{n}/reorder` | Reorder activities |
| `PATCH` | `/api/activities/{id}` | Edit an activity |
| `DELETE` | `/api/activities/{id}` | Delete an activity |

> Full interactive docs with live testing: [Swagger UI →](https://personalized-travel-itenerary-planner.onrender.com/docs)

---

## 📋 Setup & Execution Instructions

1. **Set Up the Development Environment** — Install Node.js, Python 3.11+, and configure Supabase.
2. **Design the System Architecture** — React frontend ↔ FastAPI backend ↔ Supabase DB ↔ Gemini/Groq AI.
3. **Prepare User Input Handling** — Forms capture destination, budget, dates, interests, travel style, group size.
4. **Implement the AI Itinerary Generator** — Prompt engineering with Gemini/Groq produces structured JSON itineraries.
5. **Develop Backend APIs with FastAPI** — RESTful endpoints with JWT auth, Pydantic validation, RLS-scoped DB queries.
6. **Integrate Supabase Database** — Auth, RLS policies, and 6-table schema for secure data management.
7. **Build the React Frontend Dashboard** — Trip dashboard, smart trip builder, interactive day viewer, drag-and-drop.
8. **Implement Itinerary Customization Features** — Edit, delete, reorder activities; regenerate individual days.
9. **Optimize Itinerary Logic** — Budget-aware scheduling, travel style compliance, duplicate avoidance.
10. **Deploy and Test** — Frontend on Vercel, backend on Render, E2E tested with all deployed services.
