# graphrag_enterprise_extractor.py
import json
from typing import List, Dict, Any
from openai import AzureOpenAI
import networkx as nx

class EnterpriseGraphRAGBuilder:
    def __init__(self, client: AzureOpenAI, model: str = "gpt-4o"):
        self.client = client
        self.model = model
        self.graph = nx.Graph()

    async def extract_entities_and_relations(self, text_chunk: str) -> Dict[str, Any]:
        system_prompt = (
            "You are an enterprise knowledge graph builder. Read the input text and extract all entities "
            "(organizations, products, technologies, risks, leaders) and the relationships between them. "
            "For each relationship, provide a concise description explaining how the entities are connected. "
            "Output strictly formatted JSON matching the graph schema."
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_chunk}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        data = json.loads(response.choices[0].message.content)
        
        # Populate NetworkX graph
        for entity in data.get("entities", []):
            self.graph.add_node(entity["name"], type=entity["type"], description=entity.get("description", ""))
            
        for rel in data.get("relationships", []):
            self.graph.add_edge(rel["source"], rel["target"], relationship=rel["type"], description=rel.get("description", ""))
            
        return data

    def summarize_hierarchical_communities(self, level: int = 1) -> List[str]:
        # Hierarchical community summaries enable corpus-level reasoning
        communities = nx.community.louvain_communities(self.graph)
        summaries = []
        for idx, comm in enumerate(communities):
            subgraph = self.graph.subgraph(comm)
            nodes_info = [f"{n} ({self.graph.nodes[n].get('type')})" for n in subgraph.nodes()]
            summaries.append(f"Community {idx}: {', '.join(nodes_info)}")
        return summaries
