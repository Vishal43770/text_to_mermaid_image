print("INSTALL ALL DEPENDES WITH THIS COMMAND ")
print("run this command->     pip install -r requirements.txt      ")

import json
import re
import zlib
import base64
import os
import requests
from typing import Annotated, TypedDict, List
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()
class State(TypedDict):
    messages: Annotated[list, add_messages]
print("INSTALL ALL DEPENDES WITH THIS COMMAND ")
print("run this command->     pip install -r requirements.txt      ")
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("⚠️ GOOGLE_API_KEY not found in environment or .env file.")
    api_key = input("Please enter your Google API Key: ").strip()
    if not api_key:
        raise ValueError("API Key is required to proceed.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=api_key,
    temperature=0
)

# Shape mapping based on standard flowchart symbols (Figma style)
SHAPE_MAPPING = {
    "process": ("[", "]"),    # Standard rectangle
    "decision": ("{", "}"),   # Diamond
    "terminal": ("([", "])"), # Rounded (Start/End)
    "database": ("[(", ")]"), # Cylinder
    "io": ("[/", "/]"),       # Parallelogram
}

def get_graph_structure(user_text: str):
    """Ask AI to generate nodes and edges with types from text and a title."""
    prompt = f"""
    You are a system that converts natural language descriptions into a structured JSON for a flowchart.
    Extract the logic from the text and return ONLY a JSON object with 'title', 'nodes', and 'edges'.

    JSON SCHEMA:
    {{
      "title": "A descriptive title for the flowchart",
      "nodes": [
        {{ "id": "unique_id", "label": "Human Readable Label", "type": "process|decision|terminal|database|io" }}
      ],
      "edges": [
        {{ "from": "source_id", "to": "target_id", "label": "optional_label" }}
      ]
    }}

    RULES:
    1. Identify 'terminal' nodes (start/end), 'decision' nodes (if/then), 'database' nodes (storage), and 'process' nodes (actions).
    2. Slugify the 'id' (lowercase, underscores).
    3. Ensure logical flow.
    4. Provide labels for decision branches (e.g., "Yes", "No", "Success", "Failure").
    5. 'title' should be short, descriptive, and suitable for a filename (alphanumeric and underscores).

    Input: {user_text}
    Output: JSON ONLY.
    """
    response = llm.invoke(prompt)
    content = response.content.strip()
    
    # Extract JSON if wrapped in markdown
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return json.loads(content)

def slugify(text: str) -> str:
    """Helper to ensure IDs are valid Mermaid identifiers and avoid reserved words."""
    slug = re.sub(r'[^a-zA-Z0-9_]', '_', text).lower().strip('_')
    # Avoid reserved words
    if slug in ['end', 'graph', 'subgraph', 'flowchart']:
        slug = f"{slug}_node"
    return slug

def generate_perfect_mermaid(structure):
    mermaid_lines = ["graph TD;"]

    # Nodes
    for node in structure.get("nodes", []):
        n_id = slugify(node["id"])
        label = node["label"]
        n_type = node.get("type", "process")

        start_shape, end_shape = SHAPE_MAPPING.get(n_type, ("[", "]"))
        mermaid_lines.append(f'    {n_id}{start_shape}"{label}"{end_shape};')

    # Start / End helpers
    mermaid_lines.append('    __start__([" "]):::first')
    mermaid_lines.append('    __end__([" "]):::last')

    if structure.get("nodes"):
        mermaid_lines.append(
            f"    __start__ --> {slugify(structure['nodes'][0]['id'])};"
        )

    # Edges (NOW WITH LABELS)
    for edge in structure.get("edges", []):
        src = slugify(edge["from"])
        tgt = slugify(edge["to"])
        label = edge.get("label", "").strip()

        if label:
            mermaid_lines.append(f'    {src} -->|{label}| {tgt};')
        else:
            mermaid_lines.append(f'    {src} --> {tgt};')

    # Styles
    mermaid_lines.append("    classDef first fill:#e1daff,stroke:#9b86ff,stroke-width:2px;")
    mermaid_lines.append("    classDef last fill:#9b86ff,stroke:#e1daff,stroke-width:2px,color:#fff;")
    mermaid_lines.append("    classDef decision fill:#fff9db,stroke:#fab005,stroke-width:2px;")
    mermaid_lines.append("    classDef database fill:#e3fafc,stroke:#1098ad,stroke-width:2px;")

    for node in structure.get("nodes", []):
        node_id = slugify(node["id"])
        if node["type"] == "decision":
            mermaid_lines.append(f"    class {node_id} decision;")
        elif node["type"] == "database":
            mermaid_lines.append(f"    class {node_id} database;")

    return "\n".join(mermaid_lines)


def encode_mermaid(mermaid_code: str) -> str:
    """Encodes Mermaid code using pako (zlib) + base64 for mermaid.ink."""
    data = {
        "code": mermaid_code,
        "mermaid": {"theme": "default"}
    }
    json_str = json.dumps(data)
    compressed = zlib.compress(json_str.encode('utf-8'))
    encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return f"pako:{encoded}"

def download_image(mermaid_code: str, output_path: str):
    """Downloads the diagram from mermaid.ink."""
    # Try Pako first
    encoded = encode_mermaid(mermaid_code)
    url = f"https://mermaid.ink/img/{encoded}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
        
        # Fallback to simple base64 if Pako fails
        print("🔄 Pako failed, trying simple base64...")
        b64_encoded = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
        url = f"https://mermaid.ink/img/{b64_encoded}"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
            
        print(f"❌ Failed to render image. Status code: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ Error downloading image: {e}")
        return False

def main():
    print("Welcome to THE PERFECT Mermaid Flowchart Generator (Gemini Version)!")
    user_input = input("\nDescribe your logical flow:\n> ")
    
    if not user_input:
        print("Empty input. Exiting.")
        return

    print("\n⏳ AI is designing your professional flowchart...")
    try:
        structure = get_graph_structure(user_input)
        
        title = structure.get("title", "flowchart").replace(" ", "_")
        # Ensure 'images' directory exists
        if not os.path.exists("images"):
            os.makedirs("images")
        
        output_filename = os.path.join("images", f"{title}.png")
        
        print("🏗️ Generating Mermaid shapes and styles...")
        mermaid_code = generate_perfect_mermaid(structure)
        
        print("\n" + "="*50)
        print(f"TITLE: {structure.get('title', 'Unknown')}")
        print("="*50)
        print("PROFESSIONAL MERMAID CODE:")
        print("="*50)
        print(mermaid_code)
        print("="*50 + "\n")
        
        print(f"🏗️ Rendering high-quality image as '{output_filename}'...")
        if download_image(mermaid_code, output_filename):
            print(f"✓ Success! Professional diagram saved as '{output_filename}'")
        else:
            print("⚠️ Could not save PNG, but you can use the code above in https://mermaid.live")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()