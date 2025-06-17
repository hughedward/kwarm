// Mock event data based on event_definitions.py

export const mockEvents = [
  {
    timestamp: Date.now() / 1000 - 60,
    event_type: "SWARM_RUN_START",
    config: { llm: "gpt-4-mock", details: "Initial swarm setup for demo" },
  },
  {
    timestamp: Date.now() / 1000 - 55,
    event_type: "AGENT_DEFINITION",
    agent_id: "agent_1_researcher",
    name: "ResearcherAgent",
    description: "Gathers information from various sources.",
    instructions_hash: "abcdef123456",
    tools: ["web_search", "document_reader"],
  },
  {
    timestamp: Date.now() / 1000 - 50,
    event_type: "AGENT_DEFINITION",
    agent_id: "agent_2_writer",
    name: "WriterAgent",
    description: "Compiles information into reports.",
    instructions_hash: "fedcba654321",
    tools: ["text_formatter", "report_generator"],
  },
  {
    timestamp: Date.now() / 1000 - 45,
    event_type: "AGENT_DEFINITION",
    agent_id: "agent_3_editor",
    name: "EditorAgent",
    description: "Reviews and refines reports.",
    instructions_hash: "12345abcdef",
    tools: ["grammar_check", "style_enhancer"],
  },
  {
    timestamp: Date.now() / 1000 - 40,
    event_type: "AGENT_ACTIVATE",
    agent_id: "agent_1_researcher",
    swarm_run_id: "mock_run_1",
  },
  {
    timestamp: Date.now() / 1000 - 35,
    event_type: "LLM_REQUEST",
    agent_id: "agent_1_researcher",
    model_name: "gpt-4-mock",
    prompt: "Find information on benefits of AI.",
    settings: { temperature: 0.7 }
  },
  {
    timestamp: Date.now() / 1000 - 30,
    event_type: "LLM_RESPONSE",
    agent_id: "agent_1_researcher",
    model_name: "gpt-4-mock",
    response_text: "AI offers benefits in automation, efficiency, and new capabilities."
  },
  {
    timestamp: Date.now() / 1000 - 25,
    event_type: "TOOL_CALL_ATTEMPT",
    agent_id: "agent_1_researcher",
    tool_name: "web_search",
    arguments: { query: "benefits of AI" },
  },
  {
    timestamp: Date.now() / 1000 - 20,
    event_type: "TOOL_CALL_RESULT",
    agent_id: "agent_1_researcher",
    tool_name: "web_search",
    result: "Found 10 documents on AI benefits.",
    error: null,
  },
  {
    timestamp: Date.now() / 1000 - 15,
    event_type: "AGENT_HANDOFF",
    source_agent_id: "agent_1_researcher",
    target_agent_id: "agent_2_writer",
    task_description: "Summarize the found information on AI benefits.",
    details: { tool_name: "text_formatter", arguments_for_target: {} } // Example detail
  },
  {
    timestamp: Date.now() / 1000 - 10,
    event_type: "AGENT_ACTIVATE",
    agent_id: "agent_2_writer",
    swarm_run_id: "mock_run_1",
  },
  {
    timestamp: Date.now() / 1000 - 5,
    event_type: "AGENT_DEACTIVATE", // Researcher completes its current task segment
    agent_id: "agent_1_researcher",
    reason: "handoff_completed",
  },
   {
    timestamp: Date.now() / 1000 - 4,
    event_type: "LLM_REQUEST",
    agent_id: "agent_2_writer",
    model_name: "gpt-4-mock",
    prompt: "Summarize: AI offers benefits in automation, efficiency, and new capabilities. Found 10 documents on AI benefits.",
    settings: { temperature: 0.5 }
  },
  {
    timestamp: Date.now() / 1000 - 3,
    event_type: "LLM_RESPONSE",
    agent_id: "agent_2_writer",
    model_name: "gpt-4-mock",
    response_text: "AI significantly enhances operational efficiency and enables new functionalities through automation."
  },
  {
    timestamp: Date.now() / 1000 - 2,
    event_type: "AGENT_HANDOFF",
    source_agent_id: "agent_2_writer",
    target_agent_id: "agent_3_editor",
    task_description: "Review and refine the summary.",
    details: { tool_name: "grammar_check" }
  },
  {
    timestamp: Date.now() / 1000 - 1,
    event_type: "AGENT_ACTIVATE",
    agent_id: "agent_3_editor",
    swarm_run_id: "mock_run_1",
  },
  // SWARM_RUN_END would be the final event, not included here to keep the simulation "running" or ready for more events.
  // {
  //   timestamp: Date.now() / 1000,
  //   event_type: "SWARM_RUN_END",
  //   final_result: "Report on AI benefits compiled and edited.",
  // },
];
