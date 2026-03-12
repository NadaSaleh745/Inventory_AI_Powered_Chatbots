import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from kg_state import AgentState
from kg_prompts import INTENT_PROMPT, SYNTHESIZER_PROMPT, ADD_PROMPT, UPDATE_PROMPT, INQUIRE_PROMPT, DELETE_PROMPT
from llama_index.core import Settings, KnowledgeGraphIndex
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

llm = ChatOpenAI(model='gpt-5-mini', temperature=0)
Settings.llm = LlamaOpenAI(model="gpt-4o-mini", temperature=0)

neo4j_graph_store = Neo4jGraphStore(
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    url=os.getenv("NEO4J_URI"),
)

kg_index = KnowledgeGraphIndex.from_existing(
    storage_context=None,
    graph_store=neo4j_graph_store,
)

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


def execute_cypher(state: AgentState):
    """Executes Cypher query using LlamaIndex Neo4j Graph Store"""
    query = state.get('cypher')
    if not query:
        question = state['question']
        try:
            # Use LlamaIndex query engine for natural language queries
            query_engine = kg_index.as_query_engine(
                include_text=True,
                response_mode="tree_summarize",
                embedding_mode="hybrid"
            )
            response = query_engine.query(question)

            return {
                **state,
                "cypher_result": str(response),
                "error": None
            }
        except Exception as e:
            return {
                **state,
                "error": str(e),
                "cypher_result": None
            }

    try:
        if query.startswith("```"):
            query = query.split("```")[1]
            if query.startswith("cypher"):
                query = query[6:]
            query = query.strip()

        result = neo4j_graph_store.structured_query(query)

        return {
            **state,
            "cypher_result": result,
            "error": None
        }
    except Exception as e:
        return {
            **state,
            "error": str(e),
            "cypher_result": None
        }


def synthesize_node(state: AgentState):
    """Synthesizes the cypher query based on the user's question."""
    cypher_result = state['cypher_result']
    system_prompt = SystemMessage(content=SYNTHESIZER_PROMPT)
    human_prompt = HumanMessage(content=cypher_result)
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