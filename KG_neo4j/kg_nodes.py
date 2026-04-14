import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from neo4j import GraphDatabase
from neo4j.time import Date, DateTime, Time, Duration

from inventory_chatbot_langgraph.KG_neo4j.kg_prompts import REPLAN_PROMPT
from kg_state import AgentState
from kg_prompts import INTENT_PROMPT, SYNTHESIZER_PROMPT, ADD_PROMPT, UPDATE_PROMPT, INQUIRE_PROMPT, DELETE_PROMPT, REPLAN_PROMPT
from llama_index.core import Settings, KnowledgeGraphIndex
from llama_index.graph_stores.neo4j import Neo4jGraphStore, Neo4jPropertyGraphStore
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

llm = ChatOpenAI(model='gpt-5-mini', temperature=0)
Settings.llm = LlamaOpenAI(model="gpt-4o-mini", temperature=0)


_neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)

def _convert_neo4j_types(obj):
    """Recursively convert Neo4j native types to Python native types for serialization."""
    if isinstance(obj, DateTime):
        # Convert Neo4j DateTime to Python datetime (ISO format string)
        return obj.isoformat()
    elif isinstance(obj, Date):
        # Convert Neo4j Date to Python date string
        return obj.isoformat()
    elif isinstance(obj, Time):
        # Convert Neo4j Time to Python time string
        return obj.isoformat()
    elif isinstance(obj, Duration):
        # Convert Neo4j Duration to total seconds
        return obj.total_seconds()
    elif isinstance(obj, dict):
        # Recursively convert dictionary values
        return {key: _convert_neo4j_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        # Recursively convert list items
        return [_convert_neo4j_types(item) for item in obj]
    else:
        # Return primitive types as-is
        return obj



class _AuraGraphStore:
    """Minimal Neo4j graph store compatible with Aura Free (no APOC, no routing issues)."""

    def structured_query(self, query: str, param_map: dict = None) -> list:
        """Execute a Cypher query and return results as a list of dicts."""
        param_map = param_map or {}
        # Strip markdown code fences if present
        if query.startswith("```"):
            query = query.split("```")[1]
            if query.startswith("cypher"):
                query = query[6:]
            query = query.strip()
        with _neo4j_driver.session() as session:
            result = session.run(query, param_map)
            return [record.data() for record in result]


neo4j_graph_store = _AuraGraphStore()


def intent_node(state: AgentState):
    """Determines the intent of the user's question."""
    question = state['question']
    system_prompt = SystemMessage(content=INTENT_PROMPT)
    human_prompt = HumanMessage(content=question)
    response = llm.invoke([system_prompt, human_prompt])
    return {
        **state,
        "intent": response.content.strip().upper(),
    }


def replan_node(state: AgentState):
    system_prompt = SystemMessage(content=REPLAN_PROMPT)

    human_prompt = HumanMessage(content=f"""
                                User request:
                                {state['question']}
                                
                                Broken query:
                                {state['cypher']}
                                
                                Error:
                                {state['error']}
                                """)

    response = llm.invoke([system_prompt, human_prompt])

    return {
        **state,
        "cypher": response.content.strip(),
        "error": None
    }


def execute_cypher(state: AgentState):
    """Executes Cypher query using _AuraGraphStore"""
    query = state.get('cypher')

    # If no Cypher query is provided, return error
    if not query:
        return {
            **state,
            "error": "No Cypher query generated",
            "cypher_result": None
        }

    try:
        # Clean up the query (remove markdown code fences if present)
        if query.startswith("```"):
            query = query.split("```")[1]
            if query.startswith("cypher"):
                query = query[6:]
            query = query.strip()

        # Execute query using _AuraGraphStore
        result = neo4j_graph_store.structured_query(query)
        serializable_result = _convert_neo4j_types(result) if result else []
        print(serializable_result)

        return {
            **state,
            "cypher_result": serializable_result,
            "error": None
        }
    except Exception as e:
        return {
            **state,
            "error": str(e),
            "cypher_result": None
        }


def synthesize_node(state: AgentState):
    """Synthesizes the cypher query result into a human-readable response."""
    cypher_result = state['cypher_result']
    intent = state.get('intent')

    # Handle None or error cases
    if cypher_result is None:
        error_msg = state.get('error', 'No results found or an error occurred.')
        error_response = AIMessage(content=f"I encountered an issue while querying the database: {error_msg}")
        return {
            **state,
            "messages": state["messages"] + [error_response],
        }

    # Convert result to string if it's a list (from Cypher query results)
    if isinstance(cypher_result, list):
        if len(cypher_result) == 0:
            # For ADD operations, empty result might mean success without RETURN
            if intent == 'ADD':
                success_response = AIMessage(content="The data has been successfully added to the knowledge graph.")
                return {
                    **state,
                    "messages": state["messages"] + [success_response],
                }
            # For UPDATE operations
            elif intent == 'UPDATE':
                success_response = AIMessage(content="The data has been successfully updated in the knowledge graph.")
                return {
                    **state,
                    "messages": state["messages"] + [success_response],
                }
            # For DELETE operations
            elif intent == 'DELETE':
                success_response = AIMessage(content="The data has been successfully deleted from the knowledge graph.")
                return {
                    **state,
                    "messages": state["messages"] + [success_response],
                }
            # For INQUIRE operations, empty means not found
            else:
                empty_response = AIMessage(content="I couldn't find any information matching your query in the database.")
                return {
                    **state,
                    "messages": state["messages"] + [empty_response],
                }

        # Format the list of dictionaries as a readable string
        cypher_result_str = str(cypher_result)
    else:
        cypher_result_str = str(cypher_result)

    # Check if the result is empty after conversion
    if not cypher_result_str.strip() or cypher_result_str == "[]":
        empty_response = AIMessage(content="I couldn't find any information matching your query in the database.")
        return {
            **state,
            "messages": state["messages"] + [empty_response],
        }

    # Generate synthesized response using LLM
    system_prompt = SystemMessage(content=SYNTHESIZER_PROMPT)
    human_prompt = HumanMessage(content=cypher_result_str)
    response = llm.invoke([system_prompt, human_prompt])

    return {
        **state,
        "messages": state["messages"] + [response],
    }

def add_node(state:AgentState):
    """Adds a new node to the graph"""
    question = state['question']

    system_prompt = SystemMessage(content=ADD_PROMPT)
    human = HumanMessage(content=question)

    response = llm.invoke([system_prompt, human])
    cypher_query = response.content.strip()
    return {
        **state,
        "cypher": cypher_query,
    }

def update_node(state: AgentState):
    """Updates an existing node in the graph"""
    question = state['question']
    system_prompt = SystemMessage(content=UPDATE_PROMPT)
    human = HumanMessage(content=question)
    response = llm.invoke([system_prompt, human])
    cypher_query = response.content.strip()
    return {
        **state,
        "cypher": cypher_query,
    }

def inquire_node(state: AgentState):
    """Inquires about a node in the graph"""
    question = state['question']
    system_prompt = SystemMessage(content=INQUIRE_PROMPT)
    human = HumanMessage(content=question)
    response = llm.invoke([system_prompt, human])
    cypher_query = response.content.strip()
    return {
        **state,
        "cypher": cypher_query,
    }

def delete_node(state: AgentState):
    """Deletes a node from the graph"""
    question = state['question']
    system_prompt = SystemMessage(content=DELETE_PROMPT)
    human = HumanMessage(content=question)
    response = llm.invoke([system_prompt, human])
    cypher_query = response.content.strip()
    return {
        **state,
        "cypher": cypher_query,
    }