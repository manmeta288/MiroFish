# Quick Start: MiroFish Without Zep Cloud

## What You Asked

1. **How do I use it? What commands?**
2. **Do I need to host it somewhere?**
3. **What will be its interface?**

---

## Answers

### 1. Commands to Run (Local Development)

After setting up Neo4j locally or on Railway:

```bash
# 1. Clone/navigate to repo
cd MiroFish

# 2. Set up environment
cp .env.example .env
# Edit .env with your keys (see below)

# 3. Install dependencies
npm run setup:all

# 4. Start both frontend and backend
npm run dev
```

**That's it.** The app runs at `http://localhost:3000`.

---

### 2. Do You Need to Host It?

| Option | When to Use | Cost |
|--------|-------------|------|
| **Local only** | Personal use, testing | Free (just LLM costs) |
| **Railway** | Team access, always-on | ~$10-30/month + LLM |

**Local is fine** if:
- You're the only user
- Your computer runs when you need it
- You don't mind the initial setup

**Host on Railway** if:
- Team needs access
- You want it always available
- You don't want to manage local infrastructure

---

### 3. The Interface

**Web-based UI** at `http://localhost:3000` (or your Railway URL):

```
┌─────────────────────────────────────────────────────────┐
│  MiroFish - Multi-Agent Prediction Engine               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Step 1: Graph Building                                 │
│  ├── Upload your documents (PDF, TXT, MD)               │
│  └── Review extracted entities and relationships        │
│                                                         │
│  Step 2: Environment Setup                              │
│  ├── Configure simulation parameters                  │
│  └── Generate agent personas                            │
│                                                         │
│  Step 3: Simulation                                     │
│  ├── Watch agents interact in real-time                 │
│  └── See Twitter + Reddit parallel simulations          │
│                                                         │
│  Step 4: Report Generation                            │
│  └── AI-generated prediction report with reasoning      │
│                                                         │
│  Step 5: Deep Interaction                               │
│  └── Chat with any agent from the simulation            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Environment Variables (No Zep)

Your `.env` file should look like this:

```env
# ========== LLM (OpenRouter recommended) ==========
# Get key: https://openrouter.ai/settings/keys
LLM_API_KEY=sk-or-v1-your-key-here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=anthropic/claude-3.5-sonnet

# Optional: Faster/cheaper model for entity extraction
LLM_BOOST_API_KEY=sk-or-v1-your-key-here
LLM_BOOST_BASE_URL=https://openrouter.ai/api/v1
LLM_BOOST_MODEL_NAME=meta-llama/llama-3.1-70b-instruct

# ========== Neo4j (Required - replaces Zep) ==========
# Local development:
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-strong-password

# Railway deployment:
# NEO4J_URI=neo4j+s://your-instance.railway.app:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=from-railway-dashboard
```

---

## Local Neo4j Setup (5 minutes)

**Option A: Docker (Recommended)**

```bash
# Run Neo4j locally
docker run -d \
  --name neo4j-mirofish \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password-here \
  neo4j:5-community

# Access browser at http://localhost:7474
```

**Option B: Homebrew (macOS)**

```bash
brew install neo4j
neo4j start
# Edit /opt/homebrew/var/neo4j/conf/neo4j.conf if needed
```

---

## OpenRouter Model Recommendations

| Model | Price | Quality | Speed | Best For |
|-------|-------|---------|-------|----------|
| `anthropic/claude-3.5-sonnet` | $$ | ⭐⭐⭐⭐⭐ | Medium | Reports, complex extraction |
| `anthropic/claude-3.5-haiku` | $ | ⭐⭐⭐⭐ | Fast | Quick extractions |
| `meta-llama/llama-3.1-70b` | $ | ⭐⭐⭐⭐ | Fast | Budget-friendly |
| `google/gemini-1.5-pro` | $$ | ⭐⭐⭐⭐⭐ | Medium | Long documents |
| `mistralai/mistral-large` | $$ | ⭐⭐⭐⭐ | Medium | Reasoning tasks |

**Best value combo:**
- Entity extraction: `meta-llama/llama-3.1-70b`
- Report generation: `anthropic/claude-3.5-sonnet`

---

## Quick Test After Setup

1. Start Neo4j: `docker start neo4j-mirofish`
2. Start app: `npm run dev`
3. Open `http://localhost:3000`
4. Upload a PDF or paste text
5. Click "Build Graph"
6. Watch entities appear in the visualization
7. Start a simulation (try 10 rounds first)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "NEO4J_PASSWORD not configured" | Add NEO4J_PASSWORD to .env |
| Neo4j connection refused | Check docker is running: `docker ps` |
| "No module named 'neo4j'" | Run `cd backend && uv add neo4j` |
| Embeddings slow on first run | Normal - downloading model (~80MB) |
| Graph builds but no entities | Check LLM API key is valid |

---

## Summary

| Question | Answer |
|----------|--------|
| **Command?** | `npm run dev` (after setup) |
| **Host?** | Optional - local works fine |
| **Interface?** | Web UI at localhost:3000 |
| **Zep replacement?** | Neo4j + local embeddings |
| **LLM?** | OpenRouter recommended |
| **Cost?** | ~$3-10 per simulation |
