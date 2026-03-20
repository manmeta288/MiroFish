# Solana Stress Simulation — Reduced Scope & Open-Source Sufficiency

**Scenario (summary):** ~1,900 validators; top **19** control **≥33%** stake (Nakamoto coefficient ~19); historical **outages** tied to **client bugs** and **cluster** failures; **~$40B** staked SOL; stress test: **19 high-stake validators** concentrated in **3–4 DC providers** coordinate **block skipping**, **vote withholding**, and **governance capture**; observe **throughput/TPS**, **MEV/Jito**, **Marinade / Jupiter / Kamino** cascade; **monoculture** (same **Agave** version).

**Prediction asks:** Block height at **non-finality**? What **diverges first** — uptime, vote latency, delegation exits? **Time window** for a resilience layer?

---

## 1. What open / public sources can supply (enough to **seed** a sim)

| Need | Open / public sources | Sufficiency |
|------|------------------------|-------------|
| **Validator set + stake weights** | Solana JSON-RPC (`getVoteAccounts`, `getStakeActivation`, cluster nodes), **Validators.app**, **Solana Beach**, **StakeView**-style dashboards | **Strong** — enough to build the **top-19** cohort and full stake distribution for **t₀**. |
| **Nakamoto coefficient (≈19)** | Computed **locally** from stake snapshot (not usually one API field) | **Strong** — you derive it; matches your narrative if snapshot matches methodology. |
| **Client version “monoculture” (Agave)** | RPC / gossip-derived **version strings** where exposed; some explorers aggregate | **Partial** — coverage is good for **reporting** but not always **100%** of validators or **historical** version time series without your own scrapes/snapshots. |
| **Data center / ASN concentration** | **Partial public**: some validators self-report; **RPKI/BGP/ASN** inference is **incomplete**; **no** authoritative open map “validator pubkey → DC” for all 1,900 | **Weak for exact topology** — for **3–4 provider** concentration among top 19 you often need **assumptions**, **manual labels**, or **paid** infra intel unless you only model **hypothetical** concentration. |
| **Historical outages (27+)** | Solana **incident write-ups**, **status** posts, **community** timelines | **Narrative + timing** — good for **calibrating** “how bad” and **precedent**; **not** one standardized machine API with block ranges for every event. |
| **TPS / throughput under load** | **Public metrics** (validators, explorers), **Solana docs** on limits | **Partial** — good for **ranges** and **qualitative** collapse; **exact** chain-wide TPS at each slot under arbitrary adversary needs **simulation**, not a historical oracle. |
| **MEV / Jito / bundle behavior** | **Jito** docs, **block engine** / bundle APIs where public; **Solscan** / explorers for high-level patterns | **Partial** — enough to **parameterize** “MEV spikes under congestion” **if** you define rules; **not** a full historical counterfactual for **this** attack (never happened). |
| **Marinade / Jupiter / Kamino** | **DefiLlama** (TVL, protocols), **on-chain** program accounts (with indexing), protocol docs | **Partial for TVL and mechanics** — **cascading liquidations** need **oracle prices**, **position-level** stress; **public** APIs give **aggregate** or **sample** data, rarely **full** live book for stress unless you **index** yourself. |
| **Governance “capture” (stake-weighted)** | Solana **governance** is **not** one simple Cosmos-style on-chain tally for all decisions; much is **SPL / DAO / multisig** | **Weak as a single API** — you must **scope** which **governance surface** you mean and pull **per-program** state. |

**Bottom line for “do we have enough from open sources?”**

- **Yes, enough to calibrate the *topology* (stake), *initial* cohort (top 19), *rough* client mix, *DeFi* size, and *historical outage* narrative.**
- **No, not enough to answer the prediction questions *from APIs alone* without a *model* + *assumptions*.** Open data **does not** emit “block height of non-finality” for a novel coordinated attack.

---

## 2. Reduced scope: what to **fix** vs **assume**

| Layer | Reduce to | Rationale |
|-------|-----------|-----------|
| **Validators** | Top **K** (e.g. 19) + **sample** of long tail | Matches Nakamoto story; full 1,900 only if you need statistical tail risk. |
| **Infra** | **3–4 DC providers** as **labels** on the cohort (synthetic or partially sourced) | Open DC mapping for all keys is incomplete — **explicit assumptions** are honest. |
| **Attack** | **Parameterized** fractions: skip rate, withhold votes, duration, coordination delay | Not inferrable from chain history for this scenario. |
| **Consensus / finality** | **Internal model** (Tower BFT, timeouts, fork choice) with **published** params | Must be **implemented or linked** to a research/simulator — not in Covalent-style APIs. |
| **DeFi cascade** | **Representative** pools / LTVs from **DefiLlama + docs** + **simplified** liquidation rules | Full **position-level** live state needs **your indexer** or **fork + dry-run**. |
| **Monoculture** | **Version distribution** from snapshots + **scenario** “all top-19 on same Agave build” | Observable **in part**; **counterfactual** monoculture is **scenario**, not history. |

---

## 3. Direct answer to your prediction questions

| Question | Open sources alone? | What’s actually required |
|----------|---------------------|---------------------------|
| **Block height of non-finality** | **No** | **Simulator** of consensus + network (slot schedule, leader schedule skew, skip patterns). Output is **model-dependent**. |
| **What diverges first (uptime vs vote latency vs delegations)** | **No** (no single public timeline for this attack) | **Instrumented sim** with explicit metrics + **sensitivity analysis**; optionally **historical** proxies (latency/uptime from **your** or **third-party** metrics — often **not** open at per-validator history). |
| **Time for resilience layer to intervene** | **No** | **Policy layer** in the model (detection delay, multisig latency, client patch time). |

---

## 4. Concrete public / OSS stack (Solana-only, minimal)

| Purpose | Examples |
|---------|----------|
| **Stake + validators** | Solana RPC (`getVoteAccounts`, `getClusterNodes`), Validators.app / Solana Beach APIs where exposed |
| **Chain analytics** | Solscan / SolanaFM (check ToS for bulk), Dune Solana datasets |
| **DeFi aggregates** | DefiLlama API |
| **Run / fork** | **Solana testnet** / **localnet**, **Agave** (formerly solana-labs client) OSS |
| **Liquidations / lending** | Program IDs + **self-hosted** indexer (e.g. **Helius**, **Triton**, or **your** RPC + account subscription) |

---

## 5. Gaps you should plan for (explicitly “we don’t have this”)

1. **Per-validator historical vote latency** at scale — rarely complete in one open feed.  
2. **Validator → datacenter** ground truth — **incomplete** publicly.  
3. **Counterfactual coordinated attack** — **zero** historical traces; all **scenario**.  
4. **Single API** for Marinade/Jupiter/Kamino **cross-liquidation** under arbitrary stress — **build** simplified models or **index**.  
5. **Finality boundary** as a number — **emergent** from **your** consensus + network model, not from **Covalent**-class APIs.

---

## 6. Verdict

| Question | Answer |
|----------|--------|
| **Do we have enough from open sources to simulate this scenario meaningfully?** | **Yes** for **inputs** (stake layout, rough ecosystem sizing, client/version signals, outage precedent, DeFi protocol **parameters**). |
| **Do we have enough from open sources to *predict* finality block height and ordering of divergences without building a model?** | **No** — that requires a **simulation engine** + **assumptions**; APIs **cannot** return those answers for a novel stress test. |

**Recommended next step:** Lock a **t₀ stake snapshot** (open), document **DC labels** as **assumed** or **partially sourced**, then implement **minimal** consensus + leader-schedule + skip/withhold logic to produce distributions (not single magic block height) unless you fix all randomness.
