# MiroFish Railway Deployment Guide (No Zep Cloud)

This guide explains how to deploy MiroFish on Railway without using Zep Cloud, replacing it with a self-hosted Neo4j graph database.

---

## Overview: Replacing Zep Cloud

**What Zep Cloud does:**
- Stores knowledge graphs (entities as nodes, relationships as edges)
- Provides semantic search (BM25 + vector hybrid) on graph content
- Handles temporal facts (valid/invalid/expired edges)
- Manages graph memory with automatic entity extraction

**Our replacement:** Neo4j (graph database) + pgvector-style search or in-memory vector search

---

## Architecture Changes

```
Before (Zep Cloud):
User → Frontend → Backend → Zep Cloud API (hosted)

After (Self-hosted):
User → Frontend → Backend → Neo4j (Railway-hosted)
               ↓
         LLM for entity extraction
```

---

## Step 1: Set Up Neo4j on Railway

### Option A: Deploy Neo4j via Railway Template

1. **Go to Railway Dashboard** → "New Project" → "Deploy Neo4j"
   - Use the official Neo4j template or Docker image: `neo4j:5-community`

2. **Add Environment Variables**:
```env
NEO4J_AUTH=neo4j/your-strong-password-here
NEO4J_PLUGINS=["apoc", "gds"]  # APOC for utilities, GDS for graph data science
```

3. **Expose Ports**:
   - `7474` (HTTP browser interface)
   - `7687` (Bolt protocol for backend connection)

4. **Get Connection Details**:
   - URI: `neo4j+s://your-instance.railway.app:7687`
   - Username: `neo4j`
   - Password: (from NEO4J_AUTH)

### Neo4j `Neo.ClientError.Security.Unauthorized` (auth works in the dashboard)

If MiroFish shows **Unauthorized** but you believe the password is correct:

1. **URI spelling** — Use **`bolt://`** (with a **b**), not `olt://`. Correct examples:  
   `bolt://noderamfneo4j.railway.internal:7687` or `bolt://noderamfneo4j:7687` (short internal hostname from Railway).

2. **Neo4j service must use `NEO4J_AUTH`**, not separate `NEO4J_USER` / `NEO4J_PASSWORD`. The official image only applies credentials from  
   `NEO4J_AUTH=neo4j/<password>` (everything after the first `/` is the password).

3. **MiroFish: same secret as Neo4j** — Either set **`NEO4J_PASSWORD`** to the password only (after the slash), **or** set **`NEO4J_AUTH=neo4j/<password>`** (recommended: use **Variable reference** from the Neo4j service so MiroFish gets the exact same `NEO4J_AUTH` value). If both are set, **`NEO4J_PASSWORD` wins** — remove a stale `NEO4J_PASSWORD` if you switch to referencing `NEO4J_AUTH`.

4. **Password is stored on the Neo4j volume** — Changing `NEO4J_AUTH` in Railway **does not** change an already-initialized database. The DB keeps the old password until you change it inside Neo4j or **delete the volume** (data loss) and redeploy so Neo4j picks up the new env.

5. **Hidden whitespace** — Re-paste the password, or use a short alphanumeric test password.

6. **App config precedence** — The backend loads `.env` with **`override=False`** so Railway’s env wins. Redeploy MiroFish after config changes.

---

## Step 2: Backend Code Modifications

### 2.1 Install Neo4j Driver

Add to `backend/pyproject.toml`:
```toml
dependencies = [
    # ... existing deps ...
    "neo4j>=5.14.0",
    "sentence-transformers>=2.2.2",  # For local embeddings
    "scikit-learn>=1.3.0",  # For vector similarity
]
```

### 2.2 Create Neo4j Service

Create `backend/app/services/neo4j_graph.py`:

```python
"""
Neo4j-based graph service to replace Zep Cloud
Handles: entity storage, relationship edges, semantic search, temporal facts
"""

import os
import uuid
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from neo4j import GraphDatabase
import numpy as np
from sentence_transformers import SentenceTransformer

# Load embedding model (small, fast, multilingual)
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')


@dataclass
class NodeInfo:
    """Entity node in the graph"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class EdgeInfo:
    """Relationship edge between nodes"""
    uuid: str
    name: str
    fact: str
    source_node_uuid: str
    target_node_uuid: str
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    created_at: Optional[str] = None
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    expired_at: Optional[str] = None


class Neo4jGraphService:
    """
    Neo4j-based graph service - Zep Cloud replacement
    
    Features:
    - Store entities as nodes with embeddings
    - Store relationships as edges with temporal info
    - Semantic search via vector similarity
    - Full CRUD operations on graph
    """
    
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.embedding_model = EMBEDDING_MODEL
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create indexes and constraints"""
        with self.driver.session() as session:
            # Constraint for unique node UUIDs
            session.run("""
                CREATE CONSTRAINT node_uuid IF NOT EXISTS
                FOR (n:Entity) REQUIRE n.uuid IS UNIQUE
            """)
            # Index on node names for fast lookup
            session.run("""
                CREATE INDEX node_name_idx IF NOT EXISTS
                FOR (n:Entity) ON (n.name)
            """)
    
    def close(self):
        self.driver.close()
    
    # ========== Graph Building ==========
    
    def create_graph(self, graph_name: str) -> str:
        """Create a new graph (returns graph_id)"""
        graph_id = str(uuid.uuid4())
        with self.driver.session() as session:
            session.run("""
                CREATE (g:Graph {
                    id: $graph_id,
                    name: $name,
                    created_at: datetime(),
                    node_count: 0,
                    edge_count: 0
                })
            """, graph_id=graph_id, name=graph_name)
        return graph_id
    
    def add_episode(self, graph_id: str, text_chunk: str, 
                    extracted_entities: List[Dict], 
                    extracted_edges: List[Dict]):
        """
        Add an episode (text chunk) with extracted entities/edges
        This replaces Zep's automatic entity extraction from episodes
        """
        # Generate embedding for the chunk
        chunk_embedding = self.embedding_model.encode(text_chunk).tolist()
        
        with self.driver.session() as session:
            # Create episode node
            episode_id = str(uuid.uuid4())
            session.run("""
                MATCH (g:Graph {id: $graph_id})
                CREATE (e:Episode {
                    id: $episode_id,
                    text: $text,
                    embedding: $embedding,
                    created_at: datetime()
                })
                CREATE (g)-[:CONTAINS]->(e)
            """, graph_id=graph_id, episode_id=episode_id, 
                 text=text_chunk, embedding=chunk_embedding)
            
            # Create entity nodes
            entity_map = {}  # name -> uuid
            for entity in extracted_entities:
                entity_uuid = str(uuid.uuid4())
                entity_map[entity['name']] = entity_uuid
                
                # Generate embedding for entity summary
                entity_text = f"{entity['name']}: {entity.get('summary', '')}"
                entity_embedding = self.embedding_model.encode(entity_text).tolist()
                
                session.run("""
                    MATCH (ep:Episode {id: $episode_id})
                    MERGE (n:Entity {name: $name})
                    ON CREATE SET 
                        n.uuid = $uuid,
                        n.summary = $summary,
                        n.embedding = $embedding,
                        n.labels = $labels,
                        n.created_at = datetime()
                    ON MATCH SET
                        n.summary = COALESCE(n.summary, $summary),
                        n.embedding = $embedding
                    CREATE (ep)-[:MENTIONS {fact: $summary}]->(n)
                """, episode_id=episode_id, 
                     uuid=entity_uuid,
                     name=entity['name'],
                     summary=entity.get('summary', ''),
                     labels=entity.get('labels', ['Entity']),
                     embedding=entity_embedding)
            
            # Create edges between entities
            for edge in extracted_edges:
                source = entity_map.get(edge['source'])
                target = entity_map.get(edge['target'])
                if source and target:
                    edge_uuid = str(uuid.uuid4())
                    session.run("""
                        MATCH (s:Entity {uuid: $source_uuid})
                        MATCH (t:Entity {uuid: $target_uuid})
                        CREATE (s)-[r:RELATES {
                            uuid: $edge_uuid,
                            name: $relation_name,
                            fact: $fact,
                            created_at: datetime(),
                            valid_at: datetime()
                        }]->(t)
                    """, source_uuid=source, target_uuid=target,
                         edge_uuid=edge_uuid,
                         relation_name=edge.get('name', 'relates_to'),
                         fact=edge.get('fact', ''))
            
            # Update graph counts
            session.run("""
                MATCH (g:Graph {id: $graph_id})
                SET g.node_count = g.node_count + $node_count,
                    g.edge_count = g.edge_count + $edge_count
            """, graph_id=graph_id, 
                 node_count=len(extracted_entities),
                 edge_count=len(extracted_edges))
    
    # ========== Semantic Search ==========
    
    def search_graph(self, graph_id: str, query: str, 
                     limit: int = 10) -> List[Dict]:
        """
        Semantic search on graph - replaces Zep's search API
        Uses vector similarity on entity embeddings + keyword matching on edges
        """
        query_embedding = self.embedding_model.encode(query).tolist()
        
        with self.driver.session() as session:
            # Search entities by vector similarity
            entity_results = session.run("""
                MATCH (g:Graph {id: $graph_id})-[:CONTAINS]->(ep:Episode)-[:MENTIONS]->(n:Entity)
                WHERE n.embedding IS NOT NULL
                WITH n, gds.similarity.cosine(n.embedding, $query_embedding) AS score
                WHERE score > 0.5
                RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary, 
                       n.labels AS labels, score
                ORDER BY score DESC
                LIMIT $limit
            """, graph_id=graph_id, query_embedding=query_embedding, limit=limit)
            
            # Search edges by keyword matching (fallback)
            edge_results = session.run("""
                MATCH (g:Graph {id: $graph_id})-[:CONTAINS]->(:Episode)-[:MENTIONS]->
                      (s:Entity)-[r:RELATES]->(t:Entity)
                WHERE r.fact CONTAINS $query OR r.name CONTAINS $query
                RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
                       s.uuid AS source_uuid, t.uuid AS target_uuid,
                       s.name AS source_name, t.name AS target_name
                LIMIT $limit
            """, graph_id=graph_id, query=query, limit=limit)
            
            # Combine results
            facts = []
            for record in entity_results:
                facts.append(f"[{record['name']}]: {record['summary']}")
            for record in edge_results:
                facts.append(record['fact'])
            
            return {
                'facts': list(set(facts))[:limit],  # Deduplicate
                'query': query,
                'total_count': len(facts)
            }
    
    # ========== Graph Navigation ==========
    
    def get_all_nodes(self, graph_id: str) -> List[NodeInfo]:
        """Get all entity nodes in a graph"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Graph {id: $graph_id})-[:CONTAINS]->(:Episode)-[:MENTIONS]->(n:Entity)
                RETURN DISTINCT n.uuid AS uuid, n.name AS name, 
                       n.summary AS summary, n.labels AS labels,
                       n.attributes AS attributes, n.embedding AS embedding
            """, graph_id=graph_id)
            
            nodes = []
            for record in result:
                nodes.append(NodeInfo(
                    uuid=record['uuid'],
                    name=record['name'],
                    labels=record['labels'] or ['Entity'],
                    summary=record['summary'] or '',
                    attributes=json.loads(record['attributes']) if record['attributes'] else {},
                    embedding=record['embedding']
                ))
            return nodes
    
    def get_all_edges(self, graph_id: str) -> List[EdgeInfo]:
        """Get all relationship edges in a graph"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Graph {id: $graph_id})-[:CONTAINS]->(:Episode)-[:MENTIONS]->
                      (s:Entity)-[r:RELATES]->(t:Entity)
                RETURN DISTINCT r.uuid AS uuid, r.name AS name, r.fact AS fact,
                       s.uuid AS source_uuid, t.uuid AS target_uuid,
                       s.name AS source_name, t.name AS target_name,
                       r.created_at AS created_at, r.valid_at AS valid_at,
                       r.invalid_at AS invalid_at, r.expired_at AS expired_at
            """, graph_id=graph_id)
            
            edges = []
            for record in result:
                edges.append(EdgeInfo(
                    uuid=record['uuid'],
                    name=record['name'],
                    fact=record['fact'],
                    source_node_uuid=record['source_uuid'],
                    target_node_uuid=record['target_uuid'],
                    source_node_name=record['source_name'],
                    target_node_name=record['target_name'],
                    created_at=str(record['created_at']) if record['created_at'] else None,
                    valid_at=str(record['valid_at']) if record['valid_at'] else None,
                    invalid_at=str(record['invalid_at']) if record['invalid_at'] else None,
                    expired_at=str(record['expired_at']) if record['expired_at'] else None
                ))
            return edges
    
    def get_node_detail(self, node_uuid: str) -> Optional[NodeInfo]:
        """Get detailed info about a specific node"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Entity {uuid: $uuid})
                RETURN n.uuid AS uuid, n.name AS name, n.summary AS summary,
                       n.labels AS labels, n.attributes AS attributes
            """, uuid=node_uuid)
            
            record = result.single()
            if record:
                return NodeInfo(
                    uuid=record['uuid'],
                    name=record['name'],
                    labels=record['labels'] or ['Entity'],
                    summary=record['summary'] or '',
                    attributes=json.loads(record['attributes']) if record['attributes'] else {}
                )
            return None
    
    def get_node_edges(self, node_uuid: str) -> List[EdgeInfo]:
        """Get all edges connected to a specific node"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Entity {uuid: $uuid})
                MATCH (n)-[r:RELATES]-(other:Entity)
                RETURN r.uuid AS uuid, r.name AS name, r.fact AS fact,
                       CASE WHEN startNode(r) = n THEN other.uuid ELSE n.uuid END AS other_uuid,
                       CASE WHEN startNode(r) = n THEN other.name ELSE n.name END AS other_name,
                       CASE WHEN startNode(r) = n THEN 'outgoing' ELSE 'incoming' END AS direction
            """, uuid=node_uuid)
            
            edges = []
            for record in result:
                edges.append(EdgeInfo(
                    uuid=record['uuid'],
                    name=record['name'],
                    fact=record['fact'],
                    source_node_uuid=node_uuid if record['direction'] == 'outgoing' else record['other_uuid'],
                    target_node_uuid=record['other_uuid'] if record['direction'] == 'outgoing' else node_uuid,
                    source_node_name=record.get('source_name'),
                    target_node_name=record.get('target_name')
                ))
            return edges
    
    def get_entities_by_type(self, graph_id: str, entity_type: str) -> List[NodeInfo]:
        """Get all entities of a specific type"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Graph {id: $graph_id})-[:CONTAINS]->(:Episode)-[:MENTIONS]->(n:Entity)
                WHERE $type IN n.labels
                RETURN DISTINCT n.uuid AS uuid, n.name AS name, 
                       n.summary AS summary, n.labels AS labels
            """, graph_id=graph_id, type=entity_type)
            
            nodes = []
            for record in result:
                nodes.append(NodeInfo(
                    uuid=record['uuid'],
                    name=record['name'],
                    labels=record['labels'],
                    summary=record['summary'] or ''
                ))
            return nodes
    
    def get_graph_statistics(self, graph_id: str) -> Dict[str, Any]:
        """Get statistics about a graph"""
        with self.driver.session() as session:
            # Node and edge counts
            counts = session.run("""
                MATCH (g:Graph {id: $graph_id})
                RETURN g.node_count AS nodes, g.edge_count AS edges
            """, graph_id=graph_id).single()
            
            # Entity type distribution
            type_dist = session.run("""
                MATCH (g:Graph {id: $graph_id})-[:CONTAINS]->(:Episode)-[:MENTIONS]->(n:Entity)
                UNWIND n.labels AS label
                WITH label, COUNT(*) AS count
                WHERE label <> 'Entity'
                RETURN label, count
            """, graph_id=graph_id)
            
            entity_types = {record['label']: record['count'] for record in type_dist}
            
            return {
                'graph_id': graph_id,
                'total_nodes': counts['nodes'] if counts else 0,
                'total_edges': counts['edges'] if counts else 0,
                'entity_types': entity_types
            }
```

### 2.3 Create Entity Extraction Service

Since we no longer have Zep's automatic entity extraction, we need to extract entities using LLM:

Create `backend/app/services/entity_extractor.py`:

```python
"""
LLM-based entity and relationship extraction
Replaces Zep Cloud's automatic extraction from text chunks
"""

import json
from typing import List, Dict, Any
from ..utils.llm_client import LLMClient


class EntityExtractor:
    """Extract entities and relationships from text using LLM"""
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()
    
    def extract_from_chunk(self, text: str, ontology: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract entities and relationships from a text chunk
        
        Args:
            text: The text chunk to process
            ontology: The ontology definition (entity types and relations)
            
        Returns:
            Dict with 'entities' and 'edges' lists
        """
        system_prompt = """You are an expert information extraction system. 
Your task is to extract entities and their relationships from the provided text.

Output must be valid JSON with this structure:
{
    "entities": [
        {"name": "Entity Name", "type": "EntityType", "summary": "Brief description"}
    ],
    "relationships": [
        {"source": "Entity Name", "target": "Other Entity", "name": "relation_type", "fact": "Description of relationship"}
    ]
}

Rules:
- Use only entity types from the provided ontology
- Each relationship must connect two entities that appear in the entities list
- Facts should be concise but informative
- Ensure valid JSON output only, no markdown formatting"""

        user_prompt = f"""Text to analyze:
{text[:4000]}  # Limit to avoid token overflow

Ontology:
Entity Types: {', '.join(ontology.get('entity_types', ['Person', 'Organization', 'Event', 'Concept']))}
Relation Types: {', '.join(ontology.get('relation_types', ['relates_to', 'part_of', 'causes', 'influences']))}

Extract all relevant entities and relationships."""

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            return {
                'entities': response.get('entities', []),
                'edges': response.get('relationships', [])
            }
        except Exception as e:
            # Fallback: return empty extraction
            return {'entities': [], 'edges': []}
    
    def extract_from_chunks(self, chunks: List[str], 
                           ontology: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process multiple chunks and return extraction results"""
        results = []
        for chunk in chunks:
            result = self.extract_from_chunk(chunk, ontology)
            results.append(result)
        return results
```

### 2.4 Update Graph Builder Service

Modify `backend/app/services/graph_builder.py` to use Neo4j:

```python
# Replace the Zep import with Neo4j
# from zep_cloud.client import Zep
# from zep_cloud import EpisodeData, EntityEdgeSourceTarget

from .neo4j_graph import Neo4jGraphService
from .entity_extractor import EntityExtractor
from ..config import Config

# In GraphBuilderService.__init__:
def __init__(self):
    # Connect to Neo4j instead of Zep
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_pass = os.environ.get('NEO4J_PASSWORD', 'password')
    
    self.client = Neo4jGraphService(neo4j_uri, neo4j_user, neo4j_pass)
    self.extractor = EntityExtractor()
    self.task_manager = TaskManager()

# In build_graph_async, replace Zep episode creation with:
# 1. Chunk the text
# 2. For each chunk, extract entities/edges using LLM
# 3. Store in Neo4j via self.client.add_episode()
```

### 2.5 Update Zep Tools Service

Modify `backend/app/services/zep_tools.py` to use Neo4j:

```python
# Replace Zep client with Neo4j
# from zep_cloud.client import Zep

from .neo4j_graph import Neo4jGraphService, NodeInfo, EdgeInfo, SearchResult

class Neo4jToolsService:
    """Neo4j-based tools service - replaces ZepToolsService"""
    
    def __init__(self, llm_client=None):
        neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        neo4j_pass = os.environ.get('NEO4J_PASSWORD', 'password')
        
        self.client = Neo4jGraphService(neo4j_uri, neo4j_user, neo4j_pass)
        self._llm_client = llm_client
    
    # All methods from ZepToolsService map directly:
    # - search_graph() → self.client.search_graph()
    # - get_all_nodes() → self.client.get_all_nodes()
    # - get_all_edges() → self.client.get_all_edges()
    # - etc.
```

### 2.6 Update Configuration

Modify `backend/app/config.py`:

```python
class Config:
    # ... existing configs ...
    
    # Remove Zep config
    # ZEP_API_KEY = os.environ.get('ZEP_API_KEY')
    
    # Add Neo4j config
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
    
    @classmethod
    def validate(cls):
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY not configured")
        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD not configured")
        return errors
```

---

## Step 3: Update Environment Variables

New `.env` file:

```env
# LLM API (OpenRouter recommended - see model suggestions below)
LLM_API_KEY=your_openrouter_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=anthropic/claude-3.5-sonnet

# Neo4j (Railway-hosted)
NEO4J_URI=neo4j+s://your-instance.railway.app:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Optional: Boost LLM for faster extraction
LLM_BOOST_API_KEY=optional
LLM_BOOST_BASE_URL=optional
LLM_BOOST_MODEL_NAME=optional
```

---

## Step 4: Railway Deployment

### Backend Service on Railway

1. **Create `railway.json`** in project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "startCommand": "cd backend && uv run python run.py",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

2. **Create `backend/Dockerfile`**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependencies
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync

# Copy application
COPY . .

# Expose port
EXPOSE 5001

# Run
CMD ["uv", "run", "python", "run.py"]
```

3. **Add Neo4j as a database service** in Railway dashboard

4. **Connect services** - Railway handles internal networking

### Frontend Service on Railway

1. **Create `frontend/Dockerfile`**:

```dockerfile
FROM node:20-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

2. **Create `frontend/nginx.conf`**:

```nginx
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    location /api {
        proxy_pass ${BACKEND_URL};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Recommended OpenRouter Models

OpenRouter provides unified access to multiple LLM providers. Here are recommended models for MiroFish:

### Primary Models (Best Quality)

| Model | Provider | Use Case | Cost Estimate |
|-------|----------|----------|---------------|
| `anthropic/claude-3.5-sonnet` | Anthropic | Entity extraction, report generation | $3-5 per simulation |
| `anthropic/claude-3.5-haiku` | Anthropic | Faster extraction, good quality | $1-2 per simulation |
| `google/gemini-1.5-pro` | Google | Long context, good for large documents | $2-4 per simulation |

### Budget-Friendly Options

| Model | Provider | Use Case | Cost Estimate |
|-------|----------|----------|---------------|
| `meta-llama/llama-3.1-70b-instruct` | Meta | Good balance of quality/cost | $0.50-1 per simulation |
| `mistralai/mistral-large` | Mistral | Strong reasoning for reports | $1-2 per simulation |
| `nousresearch/hermes-3-llama-3.1-405b` | Nous | Open source, very capable | $1-2 per simulation |

### Embedding Models (Local - No API Cost)

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| `all-MiniLM-L6-v2` | ~80MB | Very fast | Good |
| `BAAI/bge-small-en-v1.5` | ~130MB | Fast | Better |
| `sentence-transformers/all-mpnet-base-v2` | ~420MB | Medium | Best |

**Recommended config for OpenRouter:**
```env
LLM_API_KEY=sk-or-v1-your-openrouter-key
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=anthropic/claude-3.5-sonnet

# For faster/cheaper entity extraction
LLM_BOOST_API_KEY=sk-or-v1-your-openrouter-key
LLM_BOOST_BASE_URL=https://openrouter.ai/api/v1
LLM_BOOST_MODEL_NAME=meta-llama/llama-3.1-70b-instruct
```

---

## Cost Comparison: Zep vs Self-Hosted

| Component | Zep Cloud | Self-Hosted (Neo4j on Railway) |
|-----------|-----------|-------------------------------|
| Graph Storage | Free tier: limited | ~$5-15/month (small instance) |
| API Calls | Included | None (direct DB connection) |
| Embeddings | Included | Local (free) |
| Entity Extraction | Automatic (Zep) | LLM calls (~$0.01-0.05/chunk) |
| **Total/Month** | Free tier limited | ~$10-30 + LLM costs |

**LLM Costs per Simulation:**
- 40 rounds with Zep + Qwen: ~$5
- 40 rounds with Neo4j + Claude 3.5 Sonnet: ~$8-12
- 40 rounds with Neo4j + Llama 3.1 70B: ~$3-5

---

## Migration Checklist

- [ ] Deploy Neo4j on Railway
- [ ] Create Neo4j service code (`neo4j_graph.py`)
- [ ] Create entity extractor service
- [ ] Update graph builder to use Neo4j
- [ ] Update zep_tools to use Neo4j
- [ ] Update config.py (remove Zep, add Neo4j)
- [ ] Update .env.example
- [ ] Test graph creation locally
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Railway
- [ ] Update docker-compose.yml for local development
- [ ] Test end-to-end simulation

---

## Troubleshooting

### Neo4j Connection Issues
- Check Railway logs for Neo4j service
- Verify NEO4J_URI uses correct protocol (`neo4j://` for local, `neo4j+s://` for Railway)
- Ensure password meets Neo4j requirements (8+ chars)

### Embedding Model Issues
- First run downloads model (~80-400MB)
- If memory issues, use `all-MiniLM-L6-v2` (smallest)
- Models cached in `~/.cache/torch/sentence_transformers/`

### LLM Extraction Quality
- If extraction is poor, try Claude 3.5 Sonnet instead of cheaper models
- Increase `max_tokens` for complex documents
- Add few-shot examples in the system prompt

---

## Summary

This migration replaces Zep Cloud (SaaS) with:
1. **Neo4j** on Railway for graph storage
2. **Local embeddings** (Sentence Transformers) for semantic search
3. **LLM-based extraction** instead of Zep's automatic extraction

**Trade-offs:**
- ✅ Full data ownership
- ✅ No external API dependency for graph
- ✅ Potentially lower cost at scale
- ❌ Requires managing Neo4j instance
- ❌ LLM extraction costs vs Zep's included extraction
