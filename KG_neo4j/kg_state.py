import operator
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    question: str
    intent: str
    cypher: str
    cypher_result: str
    error: Optional[str]