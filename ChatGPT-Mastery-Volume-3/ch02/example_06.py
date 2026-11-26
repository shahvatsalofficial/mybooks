# graphrag_entity_extractor.py — Knowledge Graph Extraction Pipeline
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class EntityNode(BaseModel):
    name: str = Field(description="Canonical entity name")
    entity_type: str = Field(description="ORGANIZATION, PERSON, LOCATION, CONTRACT, or CONCEPT")
    description: str = Field(description="Brief functional description of the entity")

class RelationshipEdge(BaseModel):
    source_entity: str
    target_entity: str
    relationship_type: str
    strength: float = Field(description="Confidence weight between 0.0 and 1.0")

class GraphExtractionPayload(BaseModel):
    entities: List[EntityNode]
    relationships: List[RelationshipEdge]

GRAPH_EXTRACTION_SYSTEM_PROMPT = """
You are an expert enterprise knowledge graph architect.
Extract all salient entities and directed relationships from the provided technical or legal text.
Produce strict JSON adhering to the GraphExtractionPayload schema.
"""
