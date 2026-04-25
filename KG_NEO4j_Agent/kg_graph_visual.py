import sys
from pathlib import Path

# Add project root to path (same level as inventory_chatbot_langgraph)
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from inventory_chatbot_langgraph.KG_neo4j.kg_graph import app

png_bytes = app.get_graph().draw_mermaid_png()

with open("kg_graph.png", "wb") as f:
    f.write(png_bytes)

print("Graph saved as kg_graph.png.")
