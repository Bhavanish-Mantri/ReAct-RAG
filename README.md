# CineAgent 🎬 - Interactive ReAct Movie Recommendation Agent

CineAgent is a production-ready, interactive **ReAct (Reasoning and Acting) Agent** built with **Langchain** and **FastAPI**, designed to deliver precise movie recommendations. Instead of generating a generic static list of recommendations, CineAgent translates natural language user queries (e.g., *"horror from the 90s rated R"*) into precise filters, queries a live movie database (TMDB), verifies availability on streaming platforms, and validates age certifications before outputting verified results.

To ensure out-of-the-box submit-readiness, the project is engineered with a **dual-mode movie provider**: it connects to the live TMDB API if configured, but automatically falls back to a rich local mock database of popular movies if no TMDB API key is provided, printing detailed warning logs for transparency.

---

## 🚀 Key Features

*   **Langchain ReAct Agent Loop**: Utilizes a step-by-step reasoning trace (`Thought` ➔ `Action` ➔ `Observation` ➔ `Final Answer`) using Gemini.
*   **Decade and Constraint Translation**: Translates queries like "90s" to release year ranges (1990–1999), maps genre names to TMDB genre IDs, maps rating levels (G, PG, PG-13, R) and resolves watch provider platforms (Netflix, Max, Hulu, Prime Video).
*   **Dual-Mode database client**: Interacts with the real TMDB API or a fallback Mock Database containing pre-mapped records.
*   **Interactive Trace Console**: A glassmorphic web dashboard that showcases the agent's real-time step-by-step reasoning, tool calls, and observations.
*   **Rich Visual Layout**: Movie recommendations are displayed as structured cards with real poster images, rating badges, genre tags, and streaming platform badges.
*   **Developer-Friendly Runner**: Single-script startup that automatically handles `.env` creation, packages installation verification, and launches the default web browser.

---

## 🛠️ Architecture Overview

The application follows a decoupled client-server pattern:

```mermaid
graph TD
    User([User Prompt]) -->|1. Submit Query| Frontend[HTML5/CSS3 Web UI]
    Frontend -->|2. POST Request| API[FastAPI Server]
    API -->|3. Run Agent| Executor[Langchain Agent Executor]
    Executor -->|4. Reasoning| LLM[Google Gemini 1.5 Flash]
    LLM -->|5. Decide Tool Action| Tool[discover_movies tool]
    
    subgraph Database Layer
        Tool -->|6. Query (Live TMDB)| TMDB[TMDB API Client]
        Tool -->|6. Query (Fallback)| MockDB[Mock Database]
    end
    
    TMDB -->|7. Return Movies| Tool
    MockDB -->|7. Return Movies| Tool
    Tool -->|8. Observation| Executor
    Executor -->|9. Final Answer Synthesis| LLM
    LLM -->|10. Response Payload| API
    API -->|11. JSON Response| Frontend
    Frontend -->|12. Render Trace & Cards| User
```

---

## 📁 Project Structure

```text
React-RAG/
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── config.py         # Configuration loader (Pydantic settings)
│       ├── main.py           # FastAPI routes & static file mounting
│       └── agent/
│           ├── __init__.py
│           ├── movie_agent.py# Langchain ReAct Agent configuration & callback trace
│           └── tools.py      # TMDB API Integration & Fallback Mock DB
├── frontend/
│   ├── index.html            # Main web UI structure (glassmorphism design)
│   └── static/
│       ├── app.js            # Frontend orchestrator & UI renderer
│       └── style.css         # Dark theme custom stylesheet
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
├── run.py                    # Project launcher script
└── README.md                 # Project Documentation (This file)
```

---

## ⚙️ Installation & Setup

### Prerequisites
*   Python 3.10 or higher.
*   A Gemini API Key (obtain from [Google AI Studio](https://aistudio.google.com/)).
*   *(Optional)* A TMDB API Key (obtain from [The Movie Database](https://www.themoviedb.org/)).

### Quick Installation

1.  **Clone the Repository** and navigate to the directory:
    ```bash
    cd d:/DSA/React-RAG
    ```

2.  **Run the Launcher Script**:
    The easiest way to initialize the virtual environment, install dependencies, and run the app is using the provided `run.py`:
    ```bash
    python run.py
    ```

3.  **Configure Environment Variables**:
    On its first run, `run.py` will generate a `.env` file in the root folder. Open `.env` and fill in your keys:
    ```env
    # Google Gemini API Key (Required for ReAct Agent LLM)
    GEMINI_API_KEY=your_gemini_api_key_here

    # TMDB API Key (Optional - If left blank, it falls back to the mock database)
    TMDB_API_KEY=your_tmdb_api_key_here
    ```

4.  **Restart the Launcher**:
    ```bash
    python run.py
    ```
    The launcher will automatically open `http://127.0.0.1:8000` in your default web browser.

---

## 🔍 The ReAct Loop in Action

When a user submits: **"Recommend a horror movie from the 90s rated R"**, the agent performs the following steps:

1.  **Reasoning (Thought)**:
    *   *Agent Action*: Reads user request.
    *   *Constraint Parsing*:
        *   `90s` ➔ `start_year = 1990`, `end_year = 1999`
        *   `horror` ➔ `genre = "Horror"`
        *   `rated R` ➔ `certification = "R"`
2.  **Acting (Action)**:
    *   *Action Call*: Invokes the `discover_movies` tool with parameters:
        ```json
        {"genre": "Horror", "start_year": 1990, "end_year": 1999, "certification": "R"}
        ```
3.  **Observation**:
    *   The tool intercepts the call, checks if a TMDB key exists (if not, runs local mock DB query), executes filters, and returns movie matches:
        *   *Scream (1996)*, *The Silence of the Lambs (1991)*, *The Blair Witch Project (1999)*.
4.  **Synthesis (Thought & Final Answer)**:
    *   The agent processes the observations and generates a rich user-facing response:
        *   *"Based on your request, I recommend two landmark 90s horror movies rated R: **Scream (1996)** (a meta-slasher available on Paramount+) and **The Silence of the Lambs (1991)** (a psychological thriller available on Prime Video)..."*

The frontend captures these intermediate thoughts and displays them inside the console panel so the user can audit the reasoning process.
