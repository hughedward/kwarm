import functools
import time
import hashlib
from pydantic import BaseModel
import asyncio # Added for create_task

# Assuming swarm library is installed in the environment
try:
    from swarm import Swarm
    from swarm.agents import Agent
    # from swarm.tools import ToolInstance # Placeholder
except ImportError:
    # print("Warning: Swarm library not found. Monkey patching will use dummy classes.")
    class Swarm:
        def __init__(self, agents: list = None, *args, **kwargs): pass
        async def run(self, *args, **kwargs): pass # Made async for consistency with main.py mocks
        async def run_and_stream(self, *args, **kwargs): pass
        async def get_chat_completion(self, *args, **kwargs): pass # Made async
        def handle_tool_calls(self, *args, **kwargs): pass # Assuming sync, emits fire-and-forget
        def handle_function_result(self, *args, **kwargs): pass # Assuming sync, emits fire-and-forget

    class Agent:
        def __init__(self, id: str, name: str, description: str = None, instructions: str = "", tools: list = None, *args, **kwargs):
            self.id = id
            self.name = name
            self.description = description
            self.instructions = instructions
            self.tools = tools or []
        def get_tool_schema_for_messages(self):
            return [{"name": tool.name if hasattr(tool, 'name') else str(tool)} for tool in self.tools]
        async def get_chat_completion(self, messages, llm_metadata, *args, **kwargs): # Made async
            # This is the dummy's own method, not the patched one.
            print(f"Dummy Agent.get_chat_completion for {self.name}")
            await asyncio.sleep(0.01)
            return {"choices": [{"message": {"content": "Dummy LLM response"}}]}


from swarm_visualizer.event_emitter import emitter # emitter.emit is now async
from swarm_visualizer.event_definitions import (
    SwarmRunStartEvent, SwarmRunEndEvent, AgentDefinitionEvent,
    AgentActivateEvent, AgentDeactivateEvent, AgentHandoffEvent,
    ToolCallAttemptEvent, ToolCallResultEvent, LLMRequestEvent, LLMResponseEvent,
    ErrorEvent, AgentMessageEvent
)

original_methods = {}

def get_agent_id(agent_instance):
    if hasattr(agent_instance, 'id'):
        return str(agent_instance.id)
    return f"agent_instance_{id(agent_instance)}"

# Helper to safely call emitter.emit from sync or async patched functions
def safe_emit(event_name: str, data: BaseModel):
    try:
        # If an event loop is running, create a task.
        # This is for when a sync patched method calls emit.
        loop = asyncio.get_running_loop()
        asyncio.create_task(emitter.emit(event_name, data))
    except RuntimeError:
        # No running event loop, try to run it (e.g. for __init__ if called outside an async context)
        # This is less ideal and might not work in all scenarios (e.g. if Swarm is purely sync and used outside FastAPI)
        # For FastAPI, a loop should generally be running.
        # print("Warning: Emitting event outside of a running asyncio loop. This might not work as expected.")
        # asyncio.run(emitter.emit(event_name, data)) # This would block and might fail if loop is managed by FastAPI
        # Best effort: log and move on if no loop. FastAPI context should have a loop.
        print(f"Error: No running asyncio event loop to emit event {event_name}. Event dropped.")


def patch_swarm_init(original_init):
    @functools.wraps(original_init)
    def wrapper(self, *args, **kwargs): # __init__ must be synchronous
        # print(f"Patched Swarm.__init__ called for {self}")
        result = original_init(self, *args, **kwargs) # Call original first

        agents_list = []
        if 'agents' in kwargs and isinstance(kwargs['agents'], list):
            agents_list = kwargs['agents']
        elif args and isinstance(args[0], list) and all(isinstance(a, Agent) for a in args[0]):
            agents_list = args[0]
        elif hasattr(self, 'agents') and isinstance(self.agents, list): # If agents are set on self by original_init
             agents_list = self.agents

        for agent_instance in agents_list:
            if isinstance(agent_instance, Agent):
                try:
                    tools_schemas = getattr(agent_instance, 'get_tool_schema_for_messages', lambda: [])()
                    tool_names = [str(tool_schema.get('name', 'unknown_tool')) for tool_schema in tools_schemas]
                    instructions_hash = hashlib.md5(str(getattr(agent_instance, 'instructions', '')).encode()).hexdigest()

                    event_data = AgentDefinitionEvent(
                        agent_id=get_agent_id(agent_instance),
                        name=str(getattr(agent_instance, 'name', 'UnknownAgent')),
                        description=str(getattr(agent_instance, 'description', None)),
                        instructions_hash=instructions_hash,
                        tools=tool_names
                    )
                    safe_emit("AGENT_DEFINITION", event_data)
                except Exception as e:
                    error_event = ErrorEvent(
                        source="AgentDefinitionPatch",
                        error_message=f"Failed to emit AgentDefinitionEvent for {getattr(agent_instance, 'name', 'UnknownAgent')}: {str(e)}"
                    )
                    safe_emit("ERROR_EVENT", error_event)
        return result
    return wrapper

# Generic patcher for methods that might be sync or async
def universal_patch(original_method, event_start_type, event_end_type, error_source_name):

    if asyncio.iscoroutinefunction(original_method):
        @functools.wraps(original_method)
        async def async_wrapper(self, *args, **kwargs):
            # print(f"Patched async method {original_method.__name__} called for {self}")
            if event_start_type: # e.g. SwarmRunStartEvent
                config = {"class": self.__class__.__name__, "method": original_method.__name__}
                # TODO: Sanitize args/kwargs for config if they are too large or complex
                await emitter.emit(event_start_type.event_type, event_start_type(config=config))

            # Emit AGENT_ACTIVATE for the first agent in Swarm.run context
            # This is a heuristic and might need adjustment based on Swarm's actual logic
            if original_method.__name__ == 'run' and isinstance(self, Swarm):
                 # Try to determine the initial agent from args or kwargs or self state
                initial_agent_id_to_activate = None
                if len(args) > 1 and isinstance(args[1], str): # e.g. run(task, agent_id)
                    initial_agent_id_to_activate = args[1]
                elif 'agent_id' in kwargs:
                    initial_agent_id_to_activate = kwargs['agent_id']
                elif hasattr(self, 'initial_agent_id'): # Fictional attribute
                    initial_agent_id_to_activate = self.initial_agent_id
                elif hasattr(self, 'agents_list') and self.agents_list: # Use first agent if available
                    initial_agent_id_to_activate = get_agent_id(self.agents_list[0])

                if initial_agent_id_to_activate:
                    await emitter.emit("AGENT_ACTIVATE", AgentActivateEvent(agent_id=initial_agent_id_to_activate, swarm_run_id=str(id(self))))


            result = None
            try:
                result = await original_method(self, *args, **kwargs)
                return result
            except Exception as e:
                await emitter.emit("ERROR_EVENT", ErrorEvent(source=error_source_name, error_message=str(e)))
                raise
            finally:
                if event_end_type: # e.g. SwarmRunEndEvent
                    final_res_str = str(result) if result is not None else None
                    # Truncate if too long?
                    if final_res_str and len(final_res_str) > 200: final_res_str = final_res_str[:200] + "..."
                    await emitter.emit(event_end_type.event_type, event_end_type(final_result=final_res_str))
        return async_wrapper
    else: # Synchronous method
        @functools.wraps(original_method)
        def sync_wrapper(self, *args, **kwargs):
            # print(f"Patched sync method {original_method.__name__} called for {self}")
            if event_start_type:
                config = {"class": self.__class__.__name__, "method": original_method.__name__}
                safe_emit(event_start_type.event_type, event_start_type(config=config))

            if original_method.__name__ == 'run' and isinstance(self, Swarm):
                initial_agent_id_to_activate = None
                if len(args) > 1 and isinstance(args[1], str):
                    initial_agent_id_to_activate = args[1]
                elif 'agent_id' in kwargs:
                    initial_agent_id_to_activate = kwargs['agent_id']
                elif hasattr(self, 'initial_agent_id'):
                    initial_agent_id_to_activate = self.initial_agent_id
                elif hasattr(self, 'agents_list') and self.agents_list:
                    initial_agent_id_to_activate = get_agent_id(self.agents_list[0])
                if initial_agent_id_to_activate:
                    safe_emit("AGENT_ACTIVATE", AgentActivateEvent(agent_id=initial_agent_id_to_activate, swarm_run_id=str(id(self))))

            result = None
            try:
                result = original_method(self, *args, **kwargs)
                return result
            except Exception as e:
                safe_emit("ERROR_EVENT", ErrorEvent(source=error_source_name, error_message=str(e)))
                raise
            finally:
                if event_end_type:
                    final_res_str = str(result) if result is not None else None
                    if final_res_str and len(final_res_str) > 200: final_res_str = final_res_str[:200] + "..."
                    safe_emit(event_end_type.event_type, event_end_type(final_result=final_res_str))
        return sync_wrapper


def patch_get_chat_completion(original_method):
    if asyncio.iscoroutinefunction(original_method):
        @functools.wraps(original_method)
        async def async_wrapper(self, messages, llm_metadata: dict, *args, **kwargs):
            agent_id = get_agent_id(self) if isinstance(self, Agent) else kwargs.get("agent_id", "swarm_level_llm")
            model_name = llm_metadata.get("model_name", kwargs.get("model", "unknown_model"))
            prompt_str = "\n".join([str(msg.get("content", "")) for msg in messages if isinstance(msg, dict)])
            settings = {k: v for k, v in kwargs.items() if k not in ['messages', 'llm_metadata']}
            settings.update(llm_metadata)

            await emitter.emit("LLM_REQUEST", LLMRequestEvent(agent_id=agent_id, model_name=model_name, prompt=prompt_str, settings=settings))
            response = None
            try:
                response = await original_method(self, messages, llm_metadata, *args, **kwargs)
                response_text = ""
                if hasattr(response, 'choices') and response.choices: response_text = response.choices[0].message.content
                elif isinstance(response, str): response_text = response
                elif isinstance(response, dict) and 'choices' in response : # common openai client response structure
                    if response['choices'] and 'message' in response['choices'][0] and 'content' in response['choices'][0]['message']:
                         response_text = response['choices'][0]['message']['content']
                await emitter.emit("LLM_RESPONSE", LLMResponseEvent(agent_id=agent_id, model_name=model_name, response_text=response_text))
                return response
            except Exception as e:
                await emitter.emit("ERROR_EVENT", ErrorEvent(source="get_chat_completion", error_message=str(e)))
                raise
        return async_wrapper
    else: # Synchronous original method
        @functools.wraps(original_method)
        def sync_wrapper(self, messages, llm_metadata: dict, *args, **kwargs):
            agent_id = get_agent_id(self) if isinstance(self, Agent) else kwargs.get("agent_id", "swarm_level_llm")
            model_name = llm_metadata.get("model_name", kwargs.get("model", "unknown_model"))
            prompt_str = "\n".join([str(msg.get("content", "")) for msg in messages if isinstance(msg, dict)])
            settings = {k: v for k, v in kwargs.items() if k not in ['messages', 'llm_metadata']}
            settings.update(llm_metadata)

            safe_emit("LLM_REQUEST", LLMRequestEvent(agent_id=agent_id, model_name=model_name, prompt=prompt_str, settings=settings))
            response = None
            try:
                response = original_method(self, messages, llm_metadata, *args, **kwargs)
                response_text = ""
                if hasattr(response, 'choices') and response.choices: response_text = response.choices[0].message.content
                elif isinstance(response, str): response_text = response
                elif isinstance(response, dict) and 'choices' in response :
                    if response['choices'] and 'message' in response['choices'][0] and 'content' in response['choices'][0]['message']:
                         response_text = response['choices'][0]['message']['content']
                safe_emit("LLM_RESPONSE", LLMResponseEvent(agent_id=agent_id, model_name=model_name, response_text=response_text))
                return response
            except Exception as e:
                safe_emit("ERROR_EVENT", ErrorEvent(source="get_chat_completion", error_message=str(e)))
                raise
        return sync_wrapper


def patch_handle_tool_calls(original_method): # Assumed synchronous for now
    @functools.wraps(original_method)
    def wrapper(self, agent: Agent, tool_calls: list, *args, **kwargs):
        agent_id = get_agent_id(agent)
        for tool_call in tool_calls: # tool_calls is usually a list of dicts
            tool_name = tool_call.get("name", tool_call.get("function", {}).get("name"))
            arguments_str = tool_call.get("arguments", tool_call.get("function", {}).get("arguments", {}))
            try:
                arguments = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
            except json.JSONDecodeError:
                arguments = {"raw_arguments": str(arguments_str)}

            safe_emit("TOOL_CALL_ATTEMPT", ToolCallAttemptEvent(agent_id=agent_id, tool_name=tool_name, arguments=arguments))
        return original_method(self, agent, tool_calls, *args, **kwargs)
    return wrapper

def patch_handle_function_result(original_method): # Assumed synchronous for now
    @functools.wraps(original_method)
    def wrapper(self, agent: Agent, tool_name: str, tool_result: any, *args, **kwargs):
        agent_id = get_agent_id(agent)
        error_str = None
        if isinstance(tool_result, Exception): error_str = str(tool_result)

        # Sanitize tool_result for serialization
        serializable_result = tool_result
        if isinstance(tool_result, BaseModel): # Pydantic model
            serializable_result = tool_result.model_dump()
        elif not isinstance(tool_result, (dict, list, int, float, bool, str, type(None))):
            serializable_result = str(tool_result)
        if len(str(serializable_result)) > 500: # Truncate large results
             serializable_result = str(serializable_result)[:500] + "..."

        safe_emit("TOOL_CALL_RESULT", ToolCallResultEvent(agent_id=agent_id, tool_name=tool_name, result=serializable_result, error=error_str))
        return original_method(self, agent, tool_name, tool_result, *args, **kwargs)
    return wrapper


def apply_patches():
    global original_methods
    # print("Applying patches. Swarm and Agent classes being patched:")
    # print(f"  Swarm type: {Swarm}")
    # print(f"  Agent type: {Agent}")

    methods_to_patch = {
        Swarm: [
            ('__init__', patch_swarm_init),
            ('run', universal_patch, SwarmRunStartEvent, SwarmRunEndEvent, "Swarm.run"),
            # ('run_and_stream', universal_patch, SwarmRunStartEvent, SwarmRunEndEvent, "Swarm.run_and_stream"), # If distinct
            ('handle_tool_calls', patch_handle_tool_calls),
            ('handle_function_result', patch_handle_function_result),
        ],
        Agent: [ # Assuming get_chat_completion is an Agent method
            ('get_chat_completion', patch_get_chat_completion),
        ]
    }

    # Fallback if get_chat_completion is on Swarm not Agent
    if not hasattr(Agent, 'get_chat_completion') and hasattr(Swarm, 'get_chat_completion'):
        methods_to_patch[Swarm].append(('get_chat_completion', patch_get_chat_completion))
        if Agent in methods_to_patch and 'get_chat_completion' in [m[0] for m in methods_to_patch[Agent]]:
            methods_to_patch[Agent] = [m for m in methods_to_patch[Agent] if m[0] != 'get_chat_completion']


    for cls, patches in methods_to_patch.items():
        for patch_info in patches:
            method_name, patch_func, *args = patch_info
            if hasattr(cls, method_name):
                original_method = getattr(cls, method_name)
                key = f"{cls.__name__}.{method_name}"
                if key in original_methods: # Already patched
                    # print(f"Method {key} already patched. Skipping.")
                    continue
                original_methods[key] = original_method

                # The universal_patch takes additional args for event types
                if patch_func == universal_patch:
                    patched_method = patch_func(original_method, *args)
                else:
                    patched_method = patch_func(original_method)

                setattr(cls, method_name, patched_method)
                # print(f"Patched {key}")
            # else:
                # print(f"Method {cls.__name__}.{method_name} not found for patching.")

    # print("Swarm methods patched for visualization.")


def remove_patches():
    global original_methods
    for method_path, original_method in original_methods.items():
        try:
            cls_name, method_name = method_path.split('.')
            module_obj = None
            if cls_name == "Swarm": module_obj = Swarm
            elif cls_name == "Agent": module_obj = Agent

            if module_obj and hasattr(module_obj, method_name):
                setattr(module_obj, method_name, original_method)
        except Exception as e:
            print(f"Error restoring {method_path}: {e}")
    original_methods = {}
    # print("Original Swarm methods restored.")

# print("Swarm Visualizer Monkey Patcher initialized. Call apply_patches() to activate.")
