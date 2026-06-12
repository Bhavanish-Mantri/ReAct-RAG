import logging
import json
from typing import List, Dict, Any, Optional
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.app.config import settings
from backend.app.agent.tools import discover_movies

logger = logging.getLogger(__name__)

class AgentExecutionCallbackHandler(BaseCallbackHandler):
    """Callback handler to intercept ReAct agent execution steps and record them."""
    def __init__(self):
        super().__init__()
        self.steps: List[Dict[str, str]] = []

    def on_agent_action(self, action: AgentAction, **kwargs) -> Any:
        # Extract Thought before the Action if present
        log = action.log
        thought = log
        if "Action:" in thought:
            thought = thought.split("Action:")[0]
        thought = thought.replace("Thought:", "").strip()
        
        if thought:
            self.steps.append({
                "type": "thought",
                "title": "Agent Thought",
                "content": thought
            })
            
        # Record the Tool Call Action
        self.steps.append({
            "type": "tool_call",
            "title": "Calling Tool",
            "content": f"Tool: {action.tool}\nInput: {action.tool_input}"
        })

    def on_tool_end(self, output: str, **kwargs) -> Any:
        # Record the Tool Output Observation
        self.steps.append({
            "type": "observation",
            "title": "Observation",
            "content": output
        })

    def on_agent_finish(self, finish: AgentFinish, **kwargs) -> Any:
        # Extract final Thought if present
        log = finish.log
        thought = log
        if "Final Answer:" in thought:
            thought = thought.split("Final Answer:")[0]
        thought = thought.replace("Thought:", "").strip()
        
        if thought:
            self.steps.append({
                "type": "thought",
                "title": "Agent Thought",
                "content": thought
            })


def get_movie_agent_executor() -> AgentExecutor:
    """Initialize the Langchain ReAct Agent and Executor."""
    # 1. Instantiate the LLM (Gemini 2.5 Flash)
    google_api_key = settings.get_gemini_api_key()
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=google_api_key,
        temperature=0.0  # Deterministic for reasoning
    )
    
    # 2. Gather tools
    tools = [discover_movies]
    
    # 3. Define ReAct Prompt Template
    # Langchain's create_react_agent expects variables: {tools}, {tool_names}, {input}, {agent_scratchpad}
    template = (
        "You are a helpful, professional, and intelligent Movie Recommendation Assistant.\n"
        "Your goal is to help users find movies matching their criteria. You have access to a database search tool.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Translate informal time periods like \"90s\", \"eighties\", \"2010s\", or \"recent\" into precise start_year and end_year constraints:\n"
        "   - \"90s\" or \"1990s\" -> start_year=1990, end_year=1999\n"
        "   - \"80s\" or \"1980s\" -> start_year=1980, end_year=1989\n"
        "   - \"70s\" or \"1970s\" -> start_year=1970, end_year=1979\n"
        "   - \"2000s\" -> start_year=2000, end_year=2009\n"
        "   - \"2010s\" -> start_year=2010, end_year=2019\n"
        "   - \"2020s\" or \"recent\" -> start_year=2020, end_year=2026\n"
        "2. Extract the genre constraint. Map names like \"scifi\" or \"sci-fi\" to \"Science Fiction\".\n"
        "3. Extract age rating certifications (e.g., \"R\", \"PG-13\", \"PG\", \"G\").\n"
        "4. Extract streaming platforms/watch providers (e.g., \"Netflix\", \"Prime Video\", \"Hulu\", \"Disney Plus\", \"Max\").\n"
        "5. ALWAYS search the database using the discover_movies tool before giving a recommendation. Do not recommend movies from memory.\n"
        "6. Provide a rich, engaging, and detailed final answer. List the matching movies and explain why they fit the user's constraints.\n\n"
        "You have access to the following tools:\n\n"
        "{tools}\n\n"
        "Use the following format:\n\n"
        "Question: the input question you must answer\n"
        "Thought: you should always think about what to do and how to convert the user constraints (decade, genre, rating, platforms) into parameters for the tool.\n"
        "Action: the action to take, should be one of [{tool_names}]\n"
        "Action Input: the input to the action (MUST be a valid JSON string containing the filters, e.g. {{\"genre\": \"Horror\", \"start_year\": 1990, \"end_year\": 1999, \"certification\": \"R\"}})\n"
        "Observation: the result of the action\n"
        "... (this Thought/Action/Action Input/Observation can repeat)\n"
        "Thought: I now have the database results and know the final answer.\n"
        "Final Answer: the final answer to the original input question, detailing the recommended movies (title, year, rating, streaming, overview) and explaining why they match the request.\n\n"
        "Begin!\n\n"
        "Question: {input}\n"
        "Thought: {agent_scratchpad}"
    )
    
    prompt = PromptTemplate.from_template(template)
    
    # 4. Create the agent
    agent = create_react_agent(llm, tools, prompt)
    
    # 5. Return the executor
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5
    )


def run_movie_agent(user_query: str) -> Dict[str, Any]:
    """Execute the agent executor on the user query and collect steps."""
    logger.info(f"Running agent for query: {user_query}")
    
    # Create callback handler to capture intermediate thoughts
    cb_handler = AgentExecutionCallbackHandler()
    executor = get_movie_agent_executor()
    
    try:
        # Run agent
        response = executor.invoke(
            {"input": user_query},
            config={"callbacks": [cb_handler]}
        )
        
        final_answer = response.get("output", "")
        
        # Assemble structured result
        result = {
            "query": user_query,
            "final_answer": final_answer,
            "steps": cb_handler.steps,
            "status": "success",
            "error": None
        }
        
        # Let's try to extract any JSON-formatted movie info returned in the final answer
        # or we can parse the observation to build a beautiful visual grid of movies!
        # This is a key trick: we can look at the "observation" step in cb_handler.steps
        # and parse out the movies to return them as a clean structured list in the JSON response,
        # so the frontend can render them as gorgeous cards with images, in addition to showing the text response!
        result["movies"] = _extract_movies_from_steps(cb_handler.steps)
        return result
        
    except Exception as e:
        logger.error(f"Error during agent execution: {e}", exc_info=True)
        return {
            "query": user_query,
            "final_answer": "I encountered an error while processing your request. Please check your API keys or try again.",
            "steps": cb_handler.steps,
            "status": "error",
            "error": str(e),
            "movies": []
        }


def _extract_movies_from_steps(steps: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Helper to parse raw movie information out of the tool's observation text."""
    movies = []
    for step in steps:
        if step.get("type") == "observation":
            content = step.get("content", "")
            # Split by "Movie "
            blocks = content.split("Movie ")
            for block in blocks:
                if not block.strip() or ":" not in block:
                    continue
                try:
                    lines = block.strip().split("\n")
                    movie_info = {}
                    for line in lines:
                        if ":" in line:
                            k, v = line.split(":", 1)
                            key = k.strip().lower()
                            val = v.strip()
                            if key == "title":
                                movie_info["title"] = val
                            elif key == "year":
                                movie_info["year"] = val
                            elif key == "genres":
                                movie_info["genres"] = [g.strip() for g in val.split(",")]
                            elif key == "certification":
                                movie_info["certification"] = val
                            elif key == "rating":
                                movie_info["rating"] = val
                            elif key == "streaming on":
                                movie_info["watch_providers"] = [wp.strip() for wp in val.split(",")]
                            elif key == "poster url":
                                movie_info["poster_path"] = val if val != "None" else None
                            elif key == "overview":
                                movie_info["overview"] = val
                    if "title" in movie_info:
                        movies.append(movie_info)
                except Exception as ex:
                    logger.warning(f"Error parsing movie block: {ex}")
    return movies
