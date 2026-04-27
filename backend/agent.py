"""
agent.py — The Agent Brain (LangGraph State Machine)
======================================================
This is the most important file. Here's how to think about it:

Normal chatbot:  User → LLM → Response (one shot, done)

Agent (this):    User → LLM → "I need to search" → calls search tool
                           ↓
                      reads result → "I need more info" → calls another tool
                           ↓
                      reads result → "I have enough" → writes final report
                           ↓
                         DONE

LangGraph models this as a GRAPH:
  - Nodes = functions (things that happen)
  - Edges = connections between nodes (what happens next)
  - State = shared memory that flows through all nodes

Graph structure:
  START → [agent_node] → (if tool call needed) → [tool_node] → back to [agent_node]
                       → (if done) → END
"""

from typing import Annotated, TypedDict   # Python type hints for state definition
from langgraph.graph import StateGraph, START, END   # core LangGraph classes
from langgraph.prebuilt import ToolNode, tools_condition  # prebuilt nodes
from langchain_groq import ChatGroq         # Claude via LangChain
from langchain_core.messages import HumanMessage, SystemMessage  # message types
from langgraph.graph.message import add_messages       # handles message list merging
from tools import ALL_TOOLS                            # our 5 custom tools
import os
from dotenv import load_dotenv

load_dotenv()  # load ANTHROPIC_API_KEY from .env


# ────────────────────────────────────────────────────────────────────────────
# STEP 1: Define the State
# ────────────────────────────────────────────────────────────────────────────
# State is like a shared notebook that gets passed between every node.
# Every node can READ from it and WRITE to it.
# 
# TypedDict means this is a dictionary with typed keys (like a TypeScript interface)
class AgentState(TypedDict):
    # messages: the full conversation history (user message + all LLM + tool responses)
    # Annotated[..., add_messages] means: when updating, APPEND new messages (not replace)
    messages: Annotated[list, add_messages]

    # company_name: stored here so any node can access it without re-parsing
    company_name: str

    # research_data: accumulates all tool results as a combined string
    research_data: str


# ────────────────────────────────────────────────────────────────────────────
# STEP 2: Set up the LLM (Claude) with tools bound to it
# ────────────────────────────────────────────────────────────────────────────
# ChatAnthropic is the LangChain wrapper around Claude API
# claude-3-5-sonnet is fast + smart, good balance for agents


llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # best free model on Groq
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
    max_tokens=4096
)

# bind_tools() tells Claude: "you can call these functions"
# When Claude decides to call a tool, it returns a special AIMessage with tool_calls
# LangGraph reads those tool_calls and routes to ToolNode
llm_with_tools = llm.bind_tools(ALL_TOOLS)


# ────────────────────────────────────────────────────────────────────────────
# STEP 3: Define the Agent Node
# ────────────────────────────────────────────────────────────────────────────
# This is a NODE in our graph. It runs Claude and returns what Claude says.
# If Claude says "call a tool" → the edge routes to ToolNode
# If Claude says "I'm done" → the edge routes to END

def agent_node(state: AgentState) -> dict:
    """
    The main agent node. Runs Claude with the full conversation history.
    Claude decides: call a tool OR generate final answer.

    Args:
        state: the current state (messages so far, company name, etc.)

    Returns:
        dict with updated messages (gets merged into state via add_messages)
    """
    # Build the system prompt - this tells Claude its role and what to do
    system_prompt = SystemMessage(content=f"""You are an expert business analyst and researcher.
Your task is to research "{state['company_name']}" comprehensively and gather:

1. Company overview (what they do, founding story, business model, size)
2. Financial data (revenue, funding, valuation, growth)
3. Recent news and developments (last 30 days)
4. Competitor landscape
5. SWOT analysis signals (strengths, weaknesses, opportunities, threats)

Use your available tools to gather this information. Be thorough - call multiple tools.
After gathering enough data, synthesize everything into a structured research summary.

IMPORTANT: 
- Always call search_company_info FIRST
- Then call search_financials, search_recent_news, search_competitors
- Use scrape_page only if you find a very relevant URL worth reading deeply
- After 4-5 tool calls, you have enough data - write your synthesis
""")

    # Combine system prompt + all previous messages (conversation history)
    # This gives Claude full context of what's been searched so far
    messages_to_send = [system_prompt] + state["messages"]

    # Call Claude! llm_with_tools.invoke() sends the messages and gets a response
    # The response is an AIMessage object
    response = llm_with_tools.invoke(messages_to_send)

    # We return a dict - LangGraph merges this into the state
    # add_messages will APPEND response to state["messages"]
    return {"messages": [response]}


# ────────────────────────────────────────────────────────────────────────────
# STEP 4: Build the Graph
# ────────────────────────────────────────────────────────────────────────────

def build_agent():
    """
    Builds and compiles the LangGraph agent.
    Returns a compiled graph that can be invoked with state.
    """

    # StateGraph(AgentState) creates a new graph that uses AgentState as its state type
    graph = StateGraph(AgentState)

    # ── Add Nodes ────────────────────────────────────────────────────────────
    # "agent" node → runs agent_node() function
    graph.add_node("agent", agent_node)

    # "tools" node → ToolNode is prebuilt by LangGraph
    # It reads the tool_calls from Claude's response and actually EXECUTES the tools
    # It automatically calls the right tool with the right arguments
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    # ── Add Edges ────────────────────────────────────────────────────────────
    # START → agent (always start with the agent node)
    graph.add_edge(START, "agent")

    # agent → (conditional) → tools OR END
    # tools_condition is a prebuilt function that checks:
    #   - if last message has tool_calls → go to "tools"
    #   - if last message has no tool_calls → go to END
    graph.add_conditional_edges("agent", tools_condition)

    # tools → agent (after tool runs, always go back to agent so it can decide next step)
    graph.add_edge("tools", "agent")

    # Compile the graph - this validates the graph and prepares it for execution
    return graph.compile()


# ────────────────────────────────────────────────────────────────────────────
# STEP 5: The main function that FastAPI will call
# ────────────────────────────────────────────────────────────────────────────

async def run_research_agent(company_name: str) -> str:
    """
    Main entry point. FastAPI calls this function.
    Runs the agent and returns the full research as a string.

    Args:
        company_name: e.g. "Stripe" or "Zepto" or "OpenAI"

    Returns:
        A comprehensive research string ready to be turned into a report
    """
    # Build the agent (compile the graph)
    agent = build_agent()

    # Initial state: one HumanMessage asking the agent to research the company
    initial_state = {
        "messages": [
            HumanMessage(content=f"Research {company_name} comprehensively. "
                                  f"Use all your tools to gather complete information.")
        ],
        "company_name": company_name,
        "research_data": ""
    }

    # ── Run the graph! ────────────────────────────────────────────────────────
    # agent.ainvoke() runs the full graph asynchronously (async = non-blocking)
    # The graph will loop: agent → tools → agent → tools → agent → END
    # until Claude stops calling tools and gives a final answer
    final_state = await agent.ainvoke(
        initial_state,
        config={"recursion_limit": 25}  # max 25 node visits to prevent infinite loops
    )

    # Extract the last message - that's Claude's final research summary
    # final_state["messages"] is a list of all messages
    # [-1] gets the last one (Claude's final response after all tool calls)
    last_message = final_state["messages"][-1]

    # .content gets the text content of the message
    return last_message.content