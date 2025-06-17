import { create } from 'zustand';
import { addEdge, applyNodeChanges, applyEdgeChanges } from 'reactflow';
import io from 'socket.io-client'; // Import socket.io-client

// Helper function to create a unique ID for edges if needed
const getEdgeId = (source, target, label) => `edge-${source}-${target}-${label?.replace(/\s+/g, '_')}`;

const SOCKET_SERVER_URL = 'ws://localhost:8000/ws/swarm_events'; // Ensure this matches your backend

let socket = null; // Hold the socket instance

export const useSwarmStore = create((set, get) => ({
  // Nodes representing agents
  nodes: [],
  // Edges representing handoffs or interactions
  edges: [],

  // React Flow specific state update functions
  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },
  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  // WebSocket connection status
  isConnected: false,
  setConnected: (status) => set({ isConnected: status }),
  connectionError: null,

  // Store raw events if needed for history or replay
  eventHistory: [],

  // Function to process incoming swarm events (from WebSocket or mocks)
  processEvent: (event) => {
    // console.log("Processing event:", event);
    set((state) => ({ eventHistory: [...state.eventHistory, event] }));

    switch (event.event_type) {
      case 'AGENT_DEFINITION': {
        const existingNode = get().nodes.find(node => node.id === event.agent_id);
        if (!existingNode) {
          const newNode = {
            id: event.agent_id,
            type: 'default', // Or 'agentNode' if using custom nodes
            data: {
              label: event.name || event.agent_id,
              name: event.name,
              description: event.description,
              instructions_hash: event.instructions_hash,
              tools: event.tools,
              status: 'defined',
            },
            position: { x: Math.random() * 400 + 50, y: Math.random() * 400 + 50 },
          };
          set({ nodes: [...get().nodes, newNode] });
        } else {
          set({
            nodes: get().nodes.map(node =>
              node.id === event.agent_id
                ? { ...node, data: { ...node.data, ...event, label: event.name || event.agent_id } }
                : node
            ),
          });
        }
        break;
      }
      case 'AGENT_ACTIVATE': {
        set({
          nodes: get().nodes.map(node =>
            node.id === event.agent_id
              ? { ...node, data: { ...node.data, status: 'active' }, style: { ...node.style, backgroundColor: '#90EE90', opacity: 1.0, border: '1px solid #777' } }
              : { ...node, style: { ...node.style, backgroundColor: node.data?.status === 'inactive' ? '#D3D3D3' : undefined } }
          ),
        });
        break;
      }
      case 'AGENT_DEACTIVATE': {
        set({
          nodes: get().nodes.map(node =>
            node.id === event.agent_id
              ? { ...node, data: { ...node.data, status: event.reason || 'inactive' }, style: { ...node.style, backgroundColor: '#D3D3D3', opacity: 0.8 } }
              : node
          ),
        });
        break;
      }
      case 'AGENT_HANDOFF': {
        const edgeId = getEdgeId(event.source_agent_id, event.target_agent_id, event.details?.tool_name || event.task_description);
        const newEdge = {
          id: edgeId,
          source: event.source_agent_id,
          target: event.target_agent_id,
          label: event.details?.tool_name || event.task_description?.substring(0,50) || 'Handoff',
          animated: true,
          style: { stroke: '#007bff', strokeWidth: 2 },
          markerEnd: { type: 'arrowclosed', color: '#007bff' },
        };
        if (!get().edges.find(edge => edge.id === newEdge.id)) {
          set({ edges: addEdge(newEdge, get().edges) });
        }
        break;
      }
      case 'SWARM_RUN_START': {
        console.log("Swarm Run Started:", event.config);
        // Clear nodes and edges from previous run for a fresh view
        set({ nodes: [], edges: [], eventHistory: [event] });
        break;
      }
      case 'SWARM_RUN_END': {
        console.log("Swarm Run Ended. Final result:", event.final_result);
        set({
          nodes: get().nodes.map(node =>
            ({ ...node, style: { ...node.style, backgroundColor: undefined, border: '1px solid #777', opacity: 1.0 } })
          ),
        });
        break;
      }
      case 'TOOL_CALL_ATTEMPT': {
        set({
          nodes: get().nodes.map(node =>
            node.id === event.agent_id
              ? { ...node, data: { ...node.data, last_tool_call: `${event.tool_name}(${JSON.stringify(event.arguments)})`, status: 'tool_calling' }, style: { ...node.style, border: '2px solid blue' } }
              : node
          ),
        });
        break;
      }
      case 'TOOL_CALL_RESULT': {
         set({
          nodes: get().nodes.map(node =>
            node.id === event.agent_id
              ? { ...node, data: { ...node.data, status: 'active', last_tool_result: event.result }, style: { ...node.style, border: '1px solid #777' } }
              : node
          ),
        });
        break;
      }
       case 'LLM_REQUEST': {
        set({
          nodes: get().nodes.map(node =>
            node.id === event.agent_id
              ? { ...node, data: { ...node.data, status: 'thinking' }, style: { ...node.style, opacity: 0.7, backgroundColor: '#ADD8E6' } }
              : node
          ),
        });
        break;
      }
      case 'LLM_RESPONSE': {
        set({
          nodes: get().nodes.map(node =>
            node.id === event.agent_id // Back to active, revert opacity and specific thinking color
              ? { ...node, data: { ...node.data, status: 'active' }, style: { ...node.style, opacity: 1.0, backgroundColor: '#90EE90' } }
              : node
          ),
        });
        break;
      }
      case 'SYSTEM_MESSAGE': // For messages from the server itself
        console.log("System Message:", event.message);
        // Could add to a message log in UI if desired
        break;
      default:
        // console.log("Unhandled event type:", event.event_type, event);
        break;
    }
  },

  // WebSocket connection management
  connectWebSocket: () => {
    if (socket && socket.connected) {
      console.log('WebSocket already connected.');
      return;
    }

    // Using native WebSocket API as FastAPI typically uses it directly.
    // socket.io-client might be overkill if backend is plain WebSocket.
    // The backend is FastAPI, which uses `websockets` library under the hood.
    // Native WebSocket should be compatible.
    socket = new WebSocket(SOCKET_SERVER_URL);

    socket.onopen = () => {
      console.log('WebSocket connection established.');
      set({ isConnected: true, connectionError: null });
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // console.log('WebSocket message received:', data);
        get().processEvent(data);
      } catch (error) {
        console.error('Error parsing WebSocket message or processing event:', error);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      set({ isConnected: false, connectionError: 'WebSocket error occurred. Check console.' });
    };

    socket.onclose = (event) => {
      console.log('WebSocket connection closed.', event.reason, event.code);
      set({ isConnected: false, connectionError: event.reason || 'Connection closed.' });
      // Optional: implement reconnection logic here
    };
  },

  disconnectWebSocket: () => {
    if (socket) {
      socket.close();
      socket = null; // Clear the instance
      console.log('WebSocket disconnected by user.');
      set({ isConnected: false, connectionError: 'Disconnected by user.' });
    }
  },

  // Mock event simulation (can be kept for testing, but not used by default)
  runMockEvents: (mockEventArray) => {
    set({ nodes: [], edges: [], eventHistory: [] }); // Clear state for mocks
    mockEventArray.forEach((event, index) => {
      setTimeout(() => {
        get().processEvent(event);
      }, index * 500); // Simulate events arriving faster for testing
    });
  },
}));
