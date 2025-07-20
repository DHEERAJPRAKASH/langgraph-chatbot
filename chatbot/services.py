import os
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, ToolMessage
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from typing import Annotated
from django.conf import settings

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class ChatbotService:
    def __init__(self):
        # Set environment variables from Django settings
        os.environ['TAVILY_API_KEY'] = settings.TAVILY_API_KEY
        os.environ['GROQ_API_KEY'] = settings.GROQ_API_KEY

        self.tools = self._setup_tools()
        self.llm = self._setup_llm()
        self.graph = self._build_graph()

    def _setup_tools(self):
        """Initialize all the tools"""
        # Arxiv Tool
        api_wrapper_arxiv = ArxivAPIWrapper(top_k_results=2, doc_content_chars_max=500)
        arxiv = ArxivQueryRun(api_wrapper=api_wrapper_arxiv, description="Query arxiv papers")

        # Wikipedia Tool
        api_wrapper_wikipedia = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500)
        wikipedia = WikipediaQueryRun(api_wrapper=api_wrapper_wikipedia, description="Query wikipedia")

        # Tavily Search Tool - explicitly pass the API key
        tavily_search = TavilySearchResults(
            api_key=settings.TAVILY_API_KEY,
            max_results=2
        )

        return [tavily_search, wikipedia, arxiv]

    def _setup_llm(self):
        """Initialize the LLM with tools"""
        llm = ChatGroq(
            model="qwen/qwen3-32b",
            groq_api_key=settings.GROQ_API_KEY
        )
        return llm.bind_tools(tools=self.tools)

    def _build_graph(self):
        """Build the LangGraph workflow"""
        def tool_calling_llm(state: State):
            return {
                "messages": [self.llm.invoke(state["messages"])]
            }

        # Build the graph
        builder = StateGraph(State)

        # Add nodes
        builder.add_node("tool_calling_llm", tool_calling_llm)
        builder.add_node("tools", ToolNode(self.tools))

        # Add edges
        builder.add_edge(START, "tool_calling_llm")
        builder.add_conditional_edges("tool_calling_llm", tools_condition)
        builder.add_edge("tools", "tool_calling_llm")

        # Compile the graph
        return builder.compile()

    def process_message(self, message: str, conversation_history: list = None):
        """Process a message with simplified conversation history"""
        messages = []

        # Build message history from simplified format (only human and AI messages)
        if conversation_history:
            for msg in conversation_history:
                if msg['type'] == 'human':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['type'] == 'ai':
                    # Create simple AI message without tool_calls since we're not storing them
                    messages.append(AIMessage(content=msg['content']))
                # Note: We're ignoring any tool messages since they're not stored in DB

        # Add the new human message
        messages.append(HumanMessage(content=message))

        try:
            # Let LangGraph handle the full conversation with tools
            result = self.graph.invoke({"messages": messages})
            final_messages = result.get("messages", [])

            # Process and return all messages (for internal use by LangGraph)
            # But the calling code will only store the final AI response
            processed_messages = []
            for msg in final_messages:
                if isinstance(msg, AIMessage):
                    # Ensure tool_calls is always a list
                    tool_calls = msg.tool_calls or []
                    processed_messages.append({
                        'type': 'ai',
                        'content': msg.content,
                        'tool_calls': [dict(tc) for tc in tool_calls]  # Convert tool calls to dict
                    })
                elif isinstance(msg, ToolMessage):
                    processed_messages.append({
                        'type': 'tool',
                        'content': msg.content,
                        'tool_call_id': msg.tool_call_id
                    })

            return processed_messages

        except Exception as e:
            return [{
                'type': 'ai',
                'content': f"I encountered an error: {str(e)}",
                'tool_calls': []  # Return empty list instead of None
            }]