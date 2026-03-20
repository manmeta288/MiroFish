# Blockchain Simulation — Open Source & Public API Resources

Companion to the “simulate for existing blockchains” requirements. Each **aspect** lists **concrete tools/APIs** you can use today, plus **gaps** (what’s hard to get for free or uniformly).

Legend: **OSS** = open source | **API** = hosted public or freemium API | **Paid** = commercial (listed when it’s the de facto option)

---

## 1. RPC / WebSocket (read chain state, blocks, txs)

| Resource | Type | Chains / notes |
|----------|------|----------------|
| **Alchemy** | API | Ethereum, L2s, Solana, etc.; free tier |
| **Infura** | API | Ethereum, IPFS; free tier |
| **QuickNode** | API | Multi-chain; free tier |
| **Ankr** | API | Multi-chain public RPC + paid |
| **PublicNode / Allnodes-style public RPCs** | API | Often rate-limited, no SLA |
| **Chainlist** | Index | Curated public RPC URLs (not a provider) |
| **Cosmos ecosystem** | API | Public RPCs per chain ([Cosmos Chain Registry](https://github.com/cosmos/chain-registry)) |
| **Solana** | API | `api.mainnet-beta.solana.com` + Helius/Triton for production |
| **Bitcoin Core RPC** | OSS + self-host | `bitcoind` JSON-RPC |
| **Erigon** / **Geth** / **Nethermind** | OSS | Self-hosted archive/full node RPC |

**Gap:** Archive depth, rate limits, and historical `debug_trace*` differ by provider; no single free API gives every chain + full archive + traces at scale.

---

## 2. Aggregated “multi-chain” query APIs (balances, txs, portfolios)

| Resource | Type | Notes |
|----------|------|--------|
| **Covalent** | API | Unified REST across many EVM + some non-EVM; class balances, txs, logs |
| **Moralis** | API | EVM chains, NFTs, streams; free tier |
| **Bitquery** | API | GraphQL; many chains; paid for heavy use |
| **Zerion API** | API | Portfolio-oriented (check current product/API availability) |
| **Blockscout** | OSS | Self-host EVM explorer + API if you run your own instance |

**Gap:** Validator sets, internal staking module layout, and IBC are often **not** in generic “wallet” APIs—you need chain-specific indexers or raw module queries.

---

## 3. Indexers & subgraphs (events, custom queries)

| Resource | Type | Notes |
|----------|------|--------|
| **The Graph** | OSS + hosted | Subgraphs; many DeFi protocols; hosted network has free tier limits |
| **Subsquid** | OSS | Multi-chain indexing framework |
| **Envio (Hyperindex)** | OSS | Indexing for EVM |
| **Goldsky** | API | Subgraph hosting / pipelines |
| **Dune** | API | SQL over decoded datasets; `dune.com/api` (API key) |
| **Flipside Crypto** | API / SQL | Snowflake-based; many chain datasets |
| **BigQuery public crypto datasets** | Data | e.g. Ethereum public datasets (Google); schema varies |

**Gap:** You still need to **author** subgraphs/SQL for staking/governance if not already published for your target chain.

---

## 4. Validator / staking / consensus (L1 specifics)

### Ethereum (Beacon / PoS)

| Resource | Type | Notes |
|----------|------|--------|
| **Beaconcha.in** | API + UI | Validators, epochs, slashings, charts |
| **Beacon API (standard)** | Spec + OSS clients | Any consensus client exposes REST: `/eth/v1/...` |
| **Lighthouse / Prysm / Nimbus / Teku** | OSS | Run your own beacon + REST |
| **Rated Network** | API | Validator ratings, MEV-related analytics (check ToS/tier) |
| **EthStaker / community dashboards** | UI | Not always machine-friendly APIs |

### Cosmos SDK chains

| Resource | Type | Notes |
|----------|------|--------|
| **REST: `/cosmos/staking/v1beta1/validators`** | API | Standard module queries via LCD |
| **Mintscan (Cosmostation)** | API + UI | Many Cosmos chains; txs, validators, gov |
| **Map of Zones** | API | IBC topology/stats (not full packet-level history everywhere) |
| **Cosmos Chain Registry** | Data | Endpoints, denoms, metadata ([GitHub](https://github.com/cosmos/chain-registry)) |

### Other ecosystems

| Resource | Type | Notes |
|----------|------|--------|
| **Solana validators** | RPC + explorers | Solana Beach, Validators.app (check APIs) |
| **Polkadot Subscan** | API | Staking, validators for substrate chains |
| **Near** | Explorer APIs | Near blocks/explorer (varies) |

**Gap:** **Historical delegation time series** (per delegator, per block) often requires **your own indexer** or **archive node + custom extraction**—explorers rarely expose full history via one free endpoint.

---

## 5. Governance (on-chain proposals & votes)

| Resource | Type | Notes |
|----------|------|--------|
| **Cosmos SDK gov REST** | API | `/cosmos/gov/v1/proposals`, votes, deposits |
| **Mintscan** | API | Proposal/vote views for supported chains |
| **Snapshot** | API | Off-chain voting; widely used in EVM DAOs |
| **Tally** | API | EVM governor contracts; API access varies |
| **Boardroom** | API | Aggregated governance (check access) |
| **OpenZeppelin Governor subgraphs** | The Graph | If deployed for a DAO |

**Gap:** **Unified** governance across Cosmos + EVM + Snapshot doesn’t exist—plan per-ecosystem connectors.

---

## 6. Slashing, downtime, evidence (operational incidents)

| Resource | Type | Notes |
|----------|------|--------|
| **Beaconcha.in** | API | Slashings, exits, sync committee (ETH) |
| **Mintscan** | API | Slashing txs, validator events (Cosmos chains) |
| **Chain-specific explorers** | API | Often the only place with “nice” incident views |

**Gap:** **Standardized “incident timeline” API** across chains is rare; you often parse **blocks + txs + module events** yourself.

---

## 7. MEV / block builder / PBS (Ethereum-focused)

| Resource | Type | Notes |
|----------|------|--------|
| **Flashbots** | OSS + APIs | MEV-Boost, relay specs, `mev-boost-relay` |
| **MEV-Boost Relay APIs** | API | Block bids, payloads (relay-specific) |
| **libmev / mev-inspect-py** | OSS | Historical analysis tooling (maintenance varies) |
| **EigenPhi / MEV analytics tools** | Mixed | Often proprietary or partial OSS |
| **Ethernow / ultra sound money** | UI | Mostly visualization |

**Gap:** **Complete historical MEV attribution** for all validators is incomplete and chain-dependent; Solana/MEV on other L1s uses different tooling.

---

## 8. Bridges & cross-chain messaging (incl. IBC)

| Resource | Type | Notes |
|----------|------|--------|
| **Map of Zones** | API | IBC channels, transfers, volume aggregates |
| **Mintscan IBC** | UI/API areas | Packet search varies by integration |
| **Wormhole / LayerZero / official bridge APIs** | API | Project-specific; not universal |
| **DefiLlama bridges** | API | TVL and bridge metadata |

**Gap:** **Per-packet latency and censorship** across all routes rarely available from one API; deep IBC analysis may need **node + indexer**.

---

## 9. Oracles & token prices (for economic calibration)

| Resource | Type | Notes |
|----------|------|--------|
| **CoinGecko API** | API | Free tier with rate limits |
| **CoinCap** | API | Simple, public-friendly |
| **DefiLlama** | API | Prices, yields, stablecoins, fees |
| **Pyth** | OSS + API | Oracle feeds (Solana and cross-chain) |
| **Chainlink** | Docs + feeds | On-chain feeds; read via RPC |

**Gap:** Historical intraday for **every** small cap may be spotty on free tiers.

---

## 10. Explorers (human + sometimes machine)

| Resource | Type | Notes |
|----------|------|--------|
| **Etherscan / V2 APIs** | API | EVM; free tier; not all chains |
| **Blockscout** | OSS | Run your own explorer + API |
| **Mintscan** | API | Cosmos-heavy |
| **Subscan** | API | Substrate |
| **Solscan / SolanaFM** | API | Check plans |

**Gap:** Explorer APIs are **not standardized**; field names and coverage differ.

---

## 11. Simulation, tracing, and “what-if” execution

| Resource | Type | Notes |
|----------|------|--------|
| **Tenderly** | API | Transaction simulation, forks; dev-focused |
| **Foundry `cast` / Anvil** | OSS | Local fork testing |
| **Hardhat** | OSS | Forking mainnet for tests |
| **revm** | OSS | Rust EVM execution |

**Gap:** These help **contract-level** simulation; **network-wide agent** simulation is your product layer, not supplied as a generic public API.

---

## 12. Data warehouses & research-grade datasets

| Resource | Type | Notes |
|----------|------|--------|
| **Google BigQuery public datasets** | Data | Ethereum and others (check coverage) |
| **Crypto Ecosystem datasets** | Various | Messari, Kaiko, etc. — often **paid** |

**Gap:** **Validator psychology** and **social graphs** are not in warehouses—you need **social APIs** or **surveys** (separate stack).

---

## 13. Identity, reputation, social (optional for agent realism)

| Resource | Type | Notes |
|----------|------|--------|
| **GitHub API** | API | Validator infra repos, disclosure |
| **Twitter/X API** | API | Expensive / restricted |
| **Farcaster** | OSS + API | Open social graph (niche) |
| **ENS** | API + on-chain | Name resolution |

**Gap:** **Mapping validators to social accounts** is often manual or heuristic.

---

## Summary: What we likely **don’t** have (collective gaps)

| Gap | Why |
|-----|-----|
| **One API for all chains** (staking + gov + IBC + MEV) | Fragmentation by design |
| **Full historical delegator ↔ validator time series** | Heavy indexing; rarely free |
| **Standard cross-chain “slashing contagion” dataset** | Must build from events |
| **Real-time global mempool for all chains** | Access and cost |
| **Ground-truth “why validators behaved X”** | Off-chain; needs surveys or labels |
| **Licensing** | Some “public” dashboards forbid bulk scraping—read ToS |

---

## Suggested minimal stacks (examples)

| Target | Pull data via | Notes |
|--------|----------------|--------|
| **EVM + DeFi** | Alchemy/Infura + Covalent or Moralis + DefiLlama + Dune/Flipside | Good for markets; add **staking** only if chain uses contract you index |
| **Cosmos Hub / Cosmos app-chains** | Public LCD from chain registry + Mintscan + Map of Zones | Strong fit for validators/IBC/gov |
| **Ethereum consensus** | Beacon REST (self or provider) + Beaconcha.in | Validators/slashings/exits |

---

*This list is intentionally practical: replace or add vendors as APIs change; verify keys, rate limits, and ToS before production use.*
