import React, { useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge as rfAddEdge, // renamed to avoid conflict with store's addEdge
} from 'reactflow';
import 'reactflow/dist/style.css'; // Main React Flow styles
import { useSwarmStore } from '../store/store';

// Optional: Custom node styling or types can be defined here
// const agentNodeStyle = (nodeData) => ({
//   background: nodeData.status === 'active' ? '#90EE90' : (nodeData.status === 'thinking' ? '#ADD8E6' : '#fff'),
//   border: '1px solid #777',
//   padding: 10,
//   borderRadius: 5,
//   opacity: nodeData.status === 'thinking' ? 0.7 : 1,
// });

// Example for custom node if needed later:
// const AgentNode = ({ data }) => {
//   return (
//     <div style={agentNodeStyle(data)}>
//       <div>Name: <strong>{data.label}</strong></div>
//       {data.description && <small><em>{data.description}</em></small>}
//       <div>Status: {data.status}</div>
//       {data.last_tool_call && <div>Tool Call: {data.last_tool_call}</div>}
//     </div>
//   );
// };
// const nodeTypes = { agentNode: AgentNode };


const SwarmCanvas = () => {
  // Get state and actions from the Zustand store
  const storeNodes = useSwarmStore((state) => state.nodes);
  const storeEdges = useSwarmStore((state) => state.edges);
  const onStoreNodesChange = useSwarmStore((state) => state.onNodesChange);
  const onStoreEdgesChange = useSwarmStore((state) => state.onEdgesChange);
  // processEvent is available in the store if we need to send events from here,
  // but typically App.jsx will handle receiving events and calling processEvent.

  // React Flow's internal state hooks, synchronized with Zustand store
  // This seems redundant if store handles onNodesChange/onEdgesChange directly from RF.
  // Let's simplify: React Flow will use nodes/edges directly from the store.
  // The store's onNodesChange/onEdgesChange are the callbacks for React Flow.

  const onConnect = useCallback(
    (params) => {
      // This is if user manually creates an edge.
      // For swarm visualization, edges are typically created by AGENT_HANDOFF events.
      // We can either disable manual connection or use the store's addEdge logic.
      // For now, let's use a simple version that adds it to the store.
      // This might create non-event-driven edges, use with caution.
      // const newEdge = { ...params, id: `manual-${params.source}-${params.target}` };
      // useSwarmStore.setState(prevState => ({ edges: rfAddEdge(newEdge, prevState.edges) }));
      console.log("Manual connection attempted (disabled by default for swarm viz):", params);
    },
    [] // No direct store dependency here, but good to keep useCallback
  );

  // useEffect to log node/edge changes for debugging
  useEffect(() => {
    console.log("SwarmCanvas: Nodes updated", storeNodes);
  }, [storeNodes]);

  useEffect(() => {
    console.log("SwarmCanvas: Edges updated", storeEdges);
  }, [storeEdges]);

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <ReactFlow
        nodes={storeNodes}
        edges={storeEdges}
        onNodesChange={onStoreNodesChange} // Pass store's handler
        onEdgesChange={onStoreEdgesChange} // Pass store's handler
        onConnect={onConnect}
        // nodeTypes={nodeTypes} // Uncomment if using custom node components
        fitView // Zooms out to fit all nodes initially
        attributionPosition="bottom-left"
      >
        <MiniMap nodeStrokeColor={(n) => {
          if (n.style?.background) return n.style.background;
          if (n.type === 'input') return '#0041d0';
          if (n.type === 'output') return '#ff0072';
          if (n.type === 'default') return '#1a192b';
          return '#eee';
        }} nodeColor={(n) => {
          if (n.style?.background) return n.style.background;
          return '#fff';
        }} nodeBorderRadius={2} />
        <Controls />
        <Background color="#aaa" gap={16} />
      </ReactFlow>
    </div>
  );
};

export default SwarmCanvas;
