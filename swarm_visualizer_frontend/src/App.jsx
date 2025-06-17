import React, { useEffect, useState } from 'react';
import './App.css';
import SwarmCanvas from './components/SwarmCanvas';
import { useSwarmStore } from './store/store';
import { mockEvents } from './mockEvents'; // Still needed for manual mock run

function App() {
  const {
    connectWebSocket,
    disconnectWebSocket,
    isConnected,
    connectionError,
    runMockEvents // For manual mock triggering
  } = useSwarmStore(state => ({
    connectWebSocket: state.connectWebSocket,
    disconnectWebSocket: state.disconnectWebSocket,
    isConnected: state.isConnected,
    connectionError: state.connectionError,
    runMockEvents: state.runMockEvents,
  }));

  const nodes = useSwarmStore((state) => state.nodes);

  // Default to trying WebSocket connection, allow switching to mocks
  const [useMocks, setUseMocks] = useState(false);

  useEffect(() => {
    if (!useMocks) {
      connectWebSocket(); // Attempt to connect on component mount or when not using mocks
    } else {
      disconnectWebSocket(); // Ensure WebSocket is disconnected if we switch to mocks
    }

    // Cleanup function for when component unmounts or before re-running due to useMocks change
    return () => {
      if (!useMocks) { // Only disconnect if we were in WebSocket mode
        // This might be too aggressive if component re-renders often.
        // Consider if disconnect should only happen on true unmount or explicit action.
        // For now, let's keep it to disconnect if we switch away from WebSocket mode.
      }
    };
  }, [useMocks, connectWebSocket, disconnectWebSocket]);

  const handleToggleDataSource = () => {
    setUseMocks(prev => {
      const newUseMocks = !prev;
      if (newUseMocks) {
        // Switched to Mocks: disconnect WebSocket, then run mocks
        disconnectWebSocket();
        console.log("App: Switched to Mock Data mode. Running mock events...");
        runMockEvents(mockEvents); // Run mocks after state update
      } else {
        // Switched to Live: clear nodes/edges, then connect WebSocket
        useSwarmStore.setState({ nodes: [], edges: [], eventHistory: [] }, true, "App/toggleDataSource/switchToLive");
        connectWebSocket();
      }
      return newUseMocks;
    });
  };

  let statusMessage = "Unknown";
  let statusClass = "status-unknown";

  if (useMocks) {
    statusMessage = "Using Mock Data";
    statusClass = "status-mock";
  } else if (isConnected) {
    statusMessage = "Connected (Live)";
    statusClass = "status-connected";
  } else if (connectionError) {
    statusMessage = `Error: ${connectionError}`;
    statusClass = "status-error";
  } else {
    statusMessage = "Disconnected (Live)";
    statusClass = "status-disconnected";
  }


  return (
    <div className="App">
      <header className="App-header">
        <h1>Swarm Visualizer</h1>
        <div className="controls">
          <button onClick={handleToggleDataSource}>
            {useMocks ? 'Switch to Live Data (WebSocket)' : 'Switch to Mock Data'}
          </button>
          <p className={`status-indicator ${statusClass}`}>Status: {statusMessage}</p>
          <p>Agents: {nodes.length}</p>
        </div>
      </header>
      <main className="App-main">
        <SwarmCanvas />
      </main>
      <footer className="App-footer">
        <p>Swarm Visualization Prototype</p>
      </footer>
    </div>
  );
}

export default App;
