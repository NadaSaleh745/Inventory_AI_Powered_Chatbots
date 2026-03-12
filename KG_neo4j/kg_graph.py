from langgraph.graph import StateGraph, END
from kg_nodes import intent_node, execute_cypher, synthesize_node, add_node, inquire_node, update_node, delete_node
from kg_state import AgentState
from langgraph.checkpoint.memory import MemorySaver

def intent_router(state: AgentState):
    if state["intent"] == "ADD":
        return "add"
    elif state["intent"] == "INQUIRE":
        return "delete"
    elif state["intent"] == "UPDATE":
        return "update"
    else:
        return "delete"


workflow = StateGraph(AgentState)
workflow.add_node('intent', intent_node)
workflow.add_node('execute', execute_cypher)
workflow.add_node('synthesize', synthesize_node)

workflow.add_node('add', add_node)
workflow.add_node('inquire', inquire_node)
workflow.add_node('update', update_node)
workflow.add_node('delete', delete_node)

workflow.set_entry_point('intent')

workflow.add_conditional_edges('intent', intent_router, {'add': 'add', 'inquire': 'inquire', 'update': 'update', 'delete': 'delete'})

workflow.add_edge('add', 'execute')
workflow.add_edge('inquire', 'execute')
workflow.add_edge('update', 'execute')
workflow.add_edge('delete', 'execute')
workflow.add_edge('execute', 'synthesize')
workflow.add_edge('synthesize', END)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)