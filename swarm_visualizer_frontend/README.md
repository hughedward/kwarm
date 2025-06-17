# Swarm Visualizer Frontend

## Overview

The Swarm Visualizer Frontend is a React application designed to connect to the Swarm Visualizer backend via WebSockets. It receives real-time event data from the backend and renders a dynamic graph visualization of Swarm agent interactions, definitions, and status changes. This allows users to observe the behavior of a Swarm system as it operates.

## Key Components

*   **`App.jsx`**:
    *   **Role:** The main application component.
    *   **Responsibilities:**
        *   Manages the overall page layout (header, main content area for the canvas, footer).
        *   Handles WebSocket connection logic: initiating the connection to the backend, and managing connection status display. It uses methods from the Zustand store (`store.js`) for this.
        *   Provides UI controls, such as a button to switch between live WebSocket data and local mock event data for testing or demonstration.
        *   Displays global information like connection status and the number of active agents.

*   **`components/SwarmCanvas.jsx`**:
    *   **Role:** Renders the interactive graph visualization of the Swarm.
    *   **Technology:** Uses `React Flow` ([https://reactflow.dev/](https://reactflow.dev/)), a library for building node-based editors and interactive diagrams.
    *   **Functionality:**
        *   Displays agents as nodes and interactions (primarily handoffs) as edges.
        *   Receives node and edge data directly from the Zustand store (`store.js`).
        *   React Flow handles the rendering, layout updates, and user interactions like panning, zooming, and dragging nodes.
        *   Includes React Flow sub-components like `MiniMap`, `Controls`, and `Background` for enhanced usability.

*   **`store/store.js`**:
    *   **Role:** Centralized state management using Zustand.
    *   **Responsibilities:**
        *   **WebSocket Management:** Contains functions to `connectWebSocket` and `disconnectWebSocket`. It manages the WebSocket object instance and its event handlers (`onopen`, `onmessage`, `onerror`, `onclose`).
        *   **State:** Holds the core application state:
            *   `nodes`: An array of objects representing agents, compatible with React Flow.
            *   `edges`: An array of objects representing connections/handoffs between agents.
            *   `isConnected`: Boolean indicating the WebSocket connection status.
            *   `connectionError`: Stores any error messages related to the WebSocket connection.
            *   `eventHistory`: An array to store all received events, useful for debugging or potential future replay features.
        *   **Event Processing (`processEvent` function):** This crucial function is called when a new event is received (either via WebSocket or from mock data). It updates the `nodes` and `edges` arrays based on the event type and payload. For example:
            *   `AGENT_DEFINITION`: Creates or updates a node.
            *   `AGENT_ACTIVATE`: Changes a node's style (e.g., color) to indicate it's active.
            *   `AGENT_HANDOFF`: Creates an edge between two nodes.
            *   Other events modify node data or visual appearance.
        *   **React Flow Handlers:** Includes `onNodesChange` and `onEdgesChange` which are passed to the React Flow component to handle internal changes (like node dragging) and keep the store's state synchronized.

*   **`mockEvents.js`**:
    *   **Purpose:** Provides an array of sample event objects that mimic the data structure of events defined in the backend's `event_definitions.py`.
    *   **Usage:** Used for testing the frontend components independently of a running backend, or for demonstration purposes. The `App.jsx` can be toggled to use these mock events, which are processed by the store's `runMockEvents` and `processEvent` functions.

## Features

*   **Real-time Visualization:** Dynamically renders agents and their interactions as they occur based on events from the backend.
*   **Node Customization:** Agent nodes change their appearance (color, border, opacity) to reflect their current status (e.g., active, inactive, thinking, tool calling).
*   **Edge Representation:** Agent handoffs are visualized as animated, directed edges between agents, often labeled with the tool or task involved.
*   **WebSocket Integration:** Connects to the backend WebSocket server to receive live event streams.
*   **Connection Status:** Clearly displays the current status of the WebSocket connection (Connected, Disconnected, Error).
*   **Mock Data Mode:** Allows switching to a local mock event stream for development and testing without a backend.
*   **Interactive Canvas:** Users can pan, zoom, and drag nodes on the canvas, thanks to React Flow.

## Setup and Running

1.  **Prerequisites:**
    *   Node.js (v18.x or later recommended) and npm (or yarn).

2.  **Installation:**
    *   Navigate to the `swarm_visualizer_frontend` directory.
    *   Install dependencies:
        ```bash
        npm install
        ```
        or if using yarn:
        ```bash
        yarn install
        ```
    This will install React, React Flow, Zustand, and other necessary packages as defined in `package.json`. (Note: While `socket.io-client` might be in `package.json`, the current implementation in `store.js` uses the native `WebSocket` API for direct compatibility with FastAPI's WebSocket handling).

3.  **Running the Development Server:**
    ```bash
    npm run dev
    ```
    or
    ```bash
    yarn dev
    ```
    This will start the Vite development server, typically on `http://localhost:5173`. Open this URL in your browser to view the application. The Hot Module Replacement (HMR) will ensure changes in the code are reflected quickly in the browser.

## Event Handling

1.  **Connection:** The `App.jsx` component, through `store.js`, initiates a WebSocket connection to the backend server (default: `ws://localhost:8000/ws/swarm_events`).
2.  **Receiving Messages:** The `onmessage` handler in `store.js` listens for incoming messages from the WebSocket.
3.  **Parsing:** Each message is expected to be a JSON string representing a single Swarm event. It's parsed into a JavaScript object.
4.  **Processing:** The parsed event object is passed to the `processEvent(event)` function in `store.js`.
5.  **State Update:** `processEvent` analyzes the `event.event_type` and updates the `nodes` and `edges` arrays in the Zustand store. This involves adding new nodes/edges or modifying existing ones (e.g., changing a node's style or data payload).
6.  **Re-rendering:** React Flow components (`SwarmCanvas.jsx`) are subscribed to changes in the `nodes` and `edges` state from the store. When this state updates, React Flow efficiently re-renders the graph to reflect the changes.
