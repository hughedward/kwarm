import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware # To allow frontend dev server
import uvicorn
import os

# Import from our swarm_visualizer package
from swarm_visualizer.event_emitter import emitter # FastAPI will use this global emitter
from swarm_visualizer.monkey_patcher import apply_patches, remove_patches
# Import mock objects for standalone demonstration if Swarm library is not installed
# This logic is largely from the previous main.py for the example run

try:
    from swarm import Swarm
    from swarm.agents import Agent
    print("Actual Swarm library found. Patches will be applied to it.")
    # If actual Swarm is found, the example below should use actual Swarm objects.
except ImportError:
    print("Actual Swarm library not found. Using mock objects for demonstration.")
    # Use the dummy Agent and Swarm from monkey_patcher for the example run
    from swarm_visualizer.monkey_patcher import Agent as DummyAgent, Swarm as DummySwarm

    class MockTool: # Definition for the example
        def __init__(self, name):
            self.name = name
        def get_schema(self):
            return {"name": self.name}

    class MockAgent(DummyAgent):
        def __init__(self, id, name, instructions, tools_instances=None, description=None):
            super().__init__(id=id, name=name, description=description, instructions=instructions, tools=tools_instances or [])
            self._tools = tools_instances or []
        def get_tool_schema_for_messages(self):
            return [tool.get_schema() for tool in self._tools]
        async def get_chat_completion(self, messages, llm_metadata, *args, **kwargs): # Made async
            print(f"Original MockAgent.get_chat_completion called by {self.name}")
            from swarm_visualizer.event_definitions import AgentMessageEvent # Emitter is global
            await emitter.emit("AGENT_MESSAGE", AgentMessageEvent(agent_id=self.id, message_type="thought", content="Thinking about response..."))
            await asyncio.sleep(0.1) # Simulate async work
            return {"choices": [{"message": {"content": "Mocked LLM response from MockAgent"}}]}

    class MockSwarm(DummySwarm):
        def __init__(self, agents=None, agents_list=None, *args, **kwargs):
            actual_agents = agents if agents is not None else agents_list
            super().__init__(agents=actual_agents, *args, **kwargs)
            self.agents_list = actual_agents or []
            print(f"Original MockSwarm.__init__ called with {len(self.agents_list)} agents.")

        async def run(self, task: str, agent_id: str = None): # Made async
            print(f"Original MockSwarm.run called for task: {task}, agent: {agent_id}")
            active_agent = None
            if agent_id:
                active_agent = next((a for a in self.agents_list if hasattr(a, 'id') and a.id == agent_id), None)
            if not active_agent and self.agents_list:
                active_agent = self.agents_list[0]

            if not active_agent:
                print("No agent to run in MockSwarm.")
                return "No agent found"

            # Emit AGENT_ACTIVATE (this should be handled by the patch on Swarm.run)
            # Forcing a direct emit here for clarity if patches don't cover it for mock.
            # from swarm_visualizer.event_definitions import AgentActivateEvent
            # await emitter.emit("AGENT_ACTIVATE", AgentActivateEvent(agent_id=active_agent.id, swarm_run_id="mock_run_fastapi"))


            if hasattr(active_agent, 'get_chat_completion'):
                 await active_agent.get_chat_completion(messages=[{"role":"user", "content":task}], llm_metadata={"model_name":"mock_model_in_swarm_run"})

            tool_calls_sample = [{"name": "mock_tool_example", "arguments": {"query": task}}]
            if hasattr(self, 'handle_tool_calls'):
                # Assuming handle_tool_calls and handle_function_result are also patched and will emit
                # If they were async, they would need await. For mocks, assume patches handle sync emit.
                # The patches themselves are synchronous. Emitter.emit is async.
                # This means patched methods need to become async or run emitter.emit in a task.
                # For simplicity, we'll assume patches are updated or Swarm lib is async.
                # For now, we'll call original methods which are sync, and rely on patches being smart.
                # This is a tricky part: Patched sync methods calling async emitter.emit.
                # The patcher needs to handle this, e.g. by asyncio.create_task(emitter.emit(...))
                # For now, let's assume the patcher is updated or we make the mock methods async.
                # I made MockAgent.get_chat_completion async.
                # The patches in monkey_patcher.py need to be async-aware for their original_method calls
                # and how they call emitter.emit.
                # This is a significant change to monkey_patcher.py that is implied by using FastAPI.
                # I will proceed assuming the user is aware and will adapt monkey_patcher.py.
                # For this step, the focus is on main.py structure.

                # To avoid blocking, we can run synchronous patched methods in a thread pool
                # if they call asyncio.run or similar for emitter.emit.
                # Or, make original_methods themselves async if they interact with emitter.

                # Simplification for this subtask: Assume patches/emitter handle the sync/async bridge.
                # A more robust way: make the patched methods async if they call emitter.emit()

                self.handle_tool_calls(agent=active_agent, tool_calls=tool_calls_sample) # Patched

            if hasattr(self, 'handle_function_result'):
                self.handle_function_result(agent=active_agent, tool_name="mock_tool_example", tool_result="Mock tool result from run") # Patched

            print(f"MockSwarm: Task potentially completed by {active_agent.name}")
            return f"Task '{task}' completed by {active_agent.name} in MockSwarm"

    # Override Swarm and Agent for the monkey_patcher if using mocks
    import swarm_visualizer.monkey_patcher as mp
    mp.Swarm = MockSwarm
    mp.Agent = MockAgent
    # This ensures apply_patches() targets these async-compatible mocks.


app = FastAPI()

# CORS Middleware for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print("Applying Swarm patches...")
    apply_patches() # Patches Swarm methods to use our emitter

    # Example: Run a Swarm interaction on startup to generate events
    # This should be run as a background task to not block server startup,
    # especially if it's a long-running process.
    print("Starting example Swarm run in background...")
    asyncio.create_task(run_swarm_example())


async def run_swarm_example():
    await asyncio.sleep(1) # Give a moment for potential clients to connect
    print("--- Backend: Running Patched Swarm Example ---")
    research_tool = MockTool(name="web_search_example")
    writer_tool = MockTool(name="document_writer_example")
    researcher = MockAgent(
        id="researcher_example_1", name="ResearcherExampleAgent",
        instructions="Research various fascinating topics.", tools_instances=[research_tool]
    )
    writer = MockAgent(
        id="writer_example_1", name="WriterExampleAgent",
        instructions="Write captivating summaries of research.", tools_instances=[writer_tool]
    )

    # Initialize Swarm (AGENT_DEFINITION events should be emitted by patched __init__)
    # The patch_swarm_init in monkey_patcher.py expects 'agents' kwarg.
    # And it calls original_init. MockSwarm.__init__ takes 'agents' or 'agents_list'.
    # emitter.emit in patch_swarm_init needs to be handled with asyncio.create_task if __init__ is sync.
    # For now, assuming __init__ patch handles this.
    swarm_instance = mp.Swarm(agents=[researcher, writer], some_other_config="fastapi_example")

    # Run Swarm (triggers other events)
    try:
        # Make sure agent_id matches one of the agents.
        await swarm_instance.run(task="Explain quantum entanglement.", agent_id=researcher.id)
    except Exception as e:
        print(f"Error during Swarm example run: {e}")
        from swarm_visualizer.event_definitions import ErrorEvent
        await emitter.emit("ERROR_EVENT", ErrorEvent(source="MainExampleRun", error_message=str(e)))

    print("--- Backend: Swarm Example Run Complete ---")


@app.websocket("/ws/swarm_events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await emitter.add_client(websocket)
    try:
        # Send a welcome message or initial state if desired
        await websocket.send_text(json.dumps({"event_type": "SYSTEM_MESSAGE", "message": "Connected to Swarm Visualizer WebSocket."}))
        while True:
            # Keep the connection alive, listen for any client messages (optional)
            # For this app, primarily server-to-client.
            data = await websocket.receive_text()
            # If client sends messages, you can process them here.
            # For example, client might request historical events or trigger actions.
            print(f"Received message from client (not currently processed): {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        emitter.remove_client(websocket)


# Serve static files from the frontend build directory (optional)
# This is useful if you build the React app and want FastAPI to serve it.
# For development, you'll likely run Vite dev server separately.
# To use this:
# 1. Build your React app: `npm run build` in `swarm_visualizer_frontend`
# 2. Ensure the path is correct relative to where FastAPI server runs.
#    If main.py is in /app/swarm_visualizer, and frontend is /app/swarm_visualizer_frontend,
#    the path might be "../swarm_visualizer_frontend/dist".
# frontend_build_path = os.path.join(os.path.dirname(__file__), "..", "swarm_visualizer_frontend", "dist")
# if os.path.exists(frontend_build_path):
#    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static")
#    print(f"Serving static files from: {frontend_build_path}")
# else:
#    print(f"Frontend build directory not found at {frontend_build_path}. Run 'npm run build' in frontend.")


@app.on_event("shutdown")
async def shutdown_event():
    print("Removing Swarm patches...")
    remove_patches() # Clean up patches

if __name__ == "__main__":
    # Note: Uvicorn should be run with the app instance, e.g., uvicorn main:app --reload
    # This block is for conceptual understanding; direct `python main.py` might not work as expected for FastAPI.
    print("Starting FastAPI server with Uvicorn. Access at http://localhost:8000")
    print("WebSocket endpoint at ws://localhost:8000/ws/swarm_events")

    # This is not the standard way to run FastAPI for production/development.
    # Use: uvicorn swarm_visualizer.main:app --reload --port 8000
    # However, for the purpose of this tool, this might be how it's invoked.
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Key considerations for the async conversion:
# 1. `monkey_patcher.py`:
#    - Patched methods that call `emitter.emit()`: Since `emitter.emit()` is now async,
#      the patched wrapper functions need to handle this.
#      If the original Swarm method being patched is synchronous, the wrapper might do:
#      `asyncio.create_task(emitter.emit(...))` to not block the synchronous flow.
#      Or, the original Swarm methods themselves would need to become async.
#    - Example:
#      def patch_sync_method(original_sync_method):
#          @functools.wraps(original_sync_method)
#          def wrapper(self, *args, **kwargs):
#              result = original_sync_method(self, *args, **kwargs) # Original is sync
#              event_data = ...
#              asyncio.create_task(emitter.emit("EVENT_TYPE", event_data)) # Fire-and-forget async emit
#              return result
#          return wrapper
#
#      def patch_async_method(original_async_method):
#          @functools.wraps(original_async_method)
#          async def wrapper(self, *args, **kwargs): # Wrapper is async
#              result = await original_async_method(self, *args, **kwargs) # Original is async
#              event_data = ...
#              await emitter.emit("EVENT_TYPE", event_data) # Await emit
#              return result
#          return wrapper
#
#    - The current `monkey_patcher.py` was written for a synchronous Swarm.
#      Using it with an async framework like FastAPI for the emitter means these sync/async
#      boundaries need careful management. The MockSwarm and MockAgent in this `main.py`
#      have been made `async` for their `run` and `get_chat_completion` methods.
#      The `apply_patches` will patch these async mock methods.
#      If a real, synchronous Swarm library is used, its methods patched by the current
#      `monkey_patcher.py` would call `emitter.emit()` in a fire-and-forget manner.
#      The `patch_swarm_init` is a particular challenge if `Swarm.__init__` is sync,
#      as `__init__` cannot be async directly. The `asyncio.create_task` approach is crucial there.
#
# 2. The example `run_swarm_example()` is triggered on startup. This is for demonstration.
#    In a real application, this might be triggered by an API call or other logic.
#
# This `main.py` provides the server structure. The `monkey_patcher.py` would need
# adjustments as described if the actual Swarm library is synchronous.
# For the mock objects used here, I've made them async where they interact with the emitter.
# The `apply_patches` function in `monkey_patcher.py` will need to correctly patch
# these async mock methods or use `asyncio.create_task` for sync methods.
# The current `monkey_patcher.py` does not make its wrappers async, so it would implicitly
# use the fire-and-forget `asyncio.create_task` approach if the global event loop is running,
# or `emitter.emit` would need to be callable from sync code (e.g. by `asyncio.run_coroutine_threadsafe`
# if emitter runs in a separate thread, or by `loop.call_soon_threadsafe`).
#
# For this subtask, I will assume the existing `monkey_patcher.py` will work by having its
# synchronous wrappers call the async `emitter.emit` in a way that's compatible with the
# FastAPI event loop (e.g., implicitly via `asyncio.create_task` if FastAPI's loop is current,
# or `emitter.emit` is designed to be callable from sync code using `asyncio.run`).
# The simplest fix for `monkey_patcher.py` would be to change `emitter.emit(...)` calls
# to `asyncio.create_task(emitter.emit(...))` within its synchronous wrappers.
# I will make this change to `monkey_patcher.py` next.`swarm_visualizer/main.py` has been overwritten to set up a FastAPI server with a WebSocket endpoint. It also includes logic to run a mock Swarm example on startup, which should now emit events through the updated WebSocket-aware emitter.

The crucial point raised in the comments of the generated `main.py` is that `monkey_patcher.py`'s synchronous wrapper functions will be calling the now-asynchronous `emitter.emit()`. This requires careful handling. The simplest way to address this is to modify `monkey_patcher.py` so that its calls to `emitter.emit()` are wrapped in `asyncio.create_task()`. This will allow the synchronous patched methods to schedule the async `emit` call on FastAPI's event loop without blocking.

I will now modify `monkey_patcher.py` to make this change. This is a critical adjustment for the backend to work correctly with FastAPI.
