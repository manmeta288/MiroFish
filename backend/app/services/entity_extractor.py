"""
LLM-based entity and relationship extractor.
Replaces Zep Cloud's automatic entity extraction from text chunks.
"""

import logging
from typing import Dict, Any, List, Optional

from ..utils.llm_client import LLMClient

logger = logging.getLogger('nodera.entity_extractor')


class EntityExtractor:
    """
    Extracts entities and relationships from a text chunk using the configured LLM.
    Returns the same dict shape expected by Neo4jGraphService.add_entities_and_edges().
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._llm = llm_client

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    def extract(self, text: str, ontology: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities and relationships from one text chunk.

        Args:
            text:     The text to analyse (will be truncated to 3000 chars).
            ontology: Ontology dict with 'entity_types' and 'edge_types' lists.

        Returns:
            {'entities': [...], 'edges': [...]}
        """
        entity_type_names = [
            et.get('name', '') for et in ontology.get('entity_types', []) if et.get('name')
        ]
        edge_type_names = [
            et.get('name', '') for et in ontology.get('edge_types', []) if et.get('name')
        ]

        if not entity_type_names:
            entity_type_names = ['Person', 'Organization', 'Event', 'Concept']
        if not edge_type_names:
            edge_type_names = ['relates_to', 'part_of', 'causes', 'influences']

        system_prompt = (
            "You are an expert information extraction system.\n"
            "Extract entities and their relationships from the provided text.\n"
            "Output ONLY valid JSON — no markdown, no explanation.\n\n"
            "Format:\n"
            "{\n"
            '  "entities": [\n'
            '    {"name": "EntityName", "type": "EntityType", "summary": "Brief description"}\n'
            "  ],\n"
            '  "relationships": [\n'
            '    {"source": "EntityName", "target": "OtherEntity", "name": "relation_type", '
            '"fact": "One-sentence description of the relationship"}\n'
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Use only the entity types listed in the ontology.\n"
            "- Each relationship must reference entities that appear in the entities list.\n"
            "- Keep summaries concise (1–2 sentences).\n"
            "- Output valid JSON only — never wrap in markdown code fences."
        )

        user_prompt = (
            f"Text:\n{text[:3000]}\n\n"
            f"Ontology:\n"
            f"Entity types: {', '.join(entity_type_names)}\n"
            f"Relation types: {', '.join(edge_type_names)}\n\n"
            "Extract all entities and relationships."
        )

        try:
            response = self.llm.chat_json(
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                temperature=0.1,
            )

            entities = response.get('entities', [])
            relationships = response.get('relationships', [])

            # Normalise — add labels field if missing
            for e in entities:
                if 'labels' not in e:
                    t = e.get('type', 'Entity')
                    e['labels'] = ['Entity', t] if t != 'Entity' else ['Entity']
                if 'attributes' not in e:
                    e['attributes'] = {}

            logger.debug(
                f"Extracted {len(entities)} entities and {len(relationships)} relationships"
            )
            return {'entities': entities, 'edges': relationships}

        except Exception as exc:
            logger.warning(f"Entity extraction failed: {exc}")
            return {'entities': [], 'edges': []}

    def extract_batch(
        self, chunks: List[str], ontology: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract from multiple chunks sequentially."""
        return [self.extract(chunk, ontology) for chunk in chunks]
