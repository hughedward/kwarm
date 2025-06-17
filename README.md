# Swarm Visualization System

## Project Overview

The Swarm Visualization System is a real-time tool designed to monitor and visualize the operations of multi-agent systems built with the Swarm library (or a compatible framework). It captures key events from the Swarm backend—such as agent creation, tool calls, language model interactions, and inter-agent handoffs—and displays them dynamically as a graph on a web-based frontend. This provides developers and users with insights into the Swarm's behavior, agent states, and communication flows.

## Architecture

The system consists of two main modules:

1.  **Backend (`swarm_visualizer` package):** A Python application built with FastAPI. It monkey-patches a running Swarm instance to intercept operational events. These events are then serialized and broadcast over a WebSocket connection.
2.  **Frontend (`swarm_visualizer_frontend` package):** A React application. It connects to the backend's WebSocket server, receives the stream of Swarm events, and renders them as an interactive graph using the React Flow library.

**Interaction Diagram (Textual):**

```
  [Swarm Library (Real or Mock)]
           |
           v (Patched Methods Intercept Calls)
[Backend: swarm_visualizer (Python/FastAPI)]
  - MonkeyPatcher captures events
  - EventEmitter serializes & queues events
  - WebSocket Server broadcasts JSON events
           |
           v (WebSocket: ws://localhost:8000/ws/swarm_events)
           |
[Frontend: swarm_visualizer_frontend (React/React Flow)]
  - WebSocket client receives JSON events
  - Zustand store processes events & updates state (nodes/edges)
  - React Flow components render the graph
           |
           v
  [User's Browser: Interactive Visualization]
```

## Modules

*   **Backend: [`swarm_visualizer/README.md`](./swarm_visualizer/README.md)**
    *   Captures events from a Swarm instance using monkey-patching.
    *   Broadcasts events via a FastAPI WebSocket server.
    *   Can use mock Swarm objects if the actual library is unavailable.

*   **Frontend: [`swarm_visualizer_frontend/README.md`](./swarm_visualizer_frontend/README.md)**
    *   A React application that visualizes Swarm events in real-time.
    *   Uses React Flow for graph rendering and Zustand for state management.
    *   Connects to the backend WebSocket to receive event data.

## Getting Started / Full System Run

To run the complete Swarm Visualization System:

1.  **Start the Backend Server:**
    *   Navigate to the `swarm_visualizer` directory (or your project root).
    *   Ensure Python dependencies are installed (see `swarm_visualizer/README.md` for details, including creating/using `requirements.txt`).
        ```bash
        pip install -r swarm_visualizer/requirements.txt
        ```
    *   Run the FastAPI server:
        ```bash
        python -m uvicorn swarm_visualizer.main:app --reload --port 8000
        ```
    *   The backend server will start, and if using the default `main.py` setup, it will begin an example Swarm run, emitting events.

2.  **Start the Frontend Application:**
    *   Navigate to the `swarm_visualizer_frontend` directory.
    *   Ensure Node.js dependencies are installed (see `swarm_visualizer_frontend/README.md` for details).
        ```bash
        npm install
        ```
    *   Start the React development server:
        ```bash
        npm run dev
        ```
    *   This will typically open the application in your default web browser (e.g., at `http://localhost:5173`).

3.  **Expected Outcome:**
    *   The frontend application will load in your browser.
    *   It will attempt to connect to the backend WebSocket server.
    *   The connection status on the frontend should indicate "Connected (Live)".
    *   You will see the graph dynamically update as events from the backend's (example) Swarm run are received and visualized. Agents will appear as nodes, and handoffs as edges between them. Node styles will change based on agent activity.

## Key Technologies Used

*   **Backend:**
    *   Python 3.8+
    *   FastAPI (web framework, WebSocket handling)
    *   Uvicorn (ASGI server)
    *   Pydantic (data validation and serialization for events)
    *   (Optional) `devtalib/swarm` (the target Swarm library)
*   **Frontend:**
    *   React 18+
    *   Vite (build tool and development server)
    *   React Flow (graph visualization)
    *   Zustand (state management)
    *   Native WebSocket API (for client-side connection)
*   **Communication:**
    *   WebSockets

## Future Enhancements (Optional)

*   **Full Swarm Library Integration:** Rigorous testing and adaptation for use with the complete, actual `devtalib/swarm` library, including more complex scenarios.
*   **Advanced UI Controls:** Filters for event types, time-travel debugging (replaying event history), detailed node inspection panels.
*   **Layout Algorithms:** More sophisticated graph layout algorithms for larger, more complex swarms.
*   **Persistence:** Option to save and load swarm run visualizations or event logs.
*   **Error Reporting:** More detailed error display and diagnostics in the UI.
*   **Customizable Node/Edge Renderers:** Allow users to define custom appearances for different agent types or event categories.
*   **Performance Optimization:** For very high-frequency event streams or very large numbers of agents.
