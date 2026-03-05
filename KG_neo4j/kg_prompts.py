from kg_state import AgentState


INTENT_PROMPT = ("Classify the intent of user input as one of the following:"
                 "1- Add: Store new fact"
                 "2- Inquire: Search for information"
                 "3- Edit/Update: Modify existing fact"
                 "4- Delete: Remove fact"
                 "ONLY return the label, 'ADD', 'INQUIRE', 'UPDATE', or 'DELETE'.")

CYPHER_PROMPT = ("You are a neo4j knowledge graph expert."
                 "Given a question and intent, generate a Cypher query that can answer the question.")

SYNTHESIZER_PROMPT = ("You're a neo4j knowledge graph expert and you're also good at generating natural human-friendly "
                      "responses summarizing the results of a Cypher query.")

SCHEMA_PROMPT = ("")