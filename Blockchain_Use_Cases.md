# MiroFish — Blockchain Use Cases: Command Prompts

This document provides detailed command prompts for executing blockchain-focused simulations from a Validator and Infrastructure perspective.

---

## Validator Behavior & Operations

### 1. Validator Behavior Modeling

```
Simulate validator responses to a 20% commission rate increase proposal. 
Model 50 validators with varying stake sizes, operational costs, and risk 
tolerance levels. Track which validators accept, reject, or exit the active 
set, and measure delegator reallocation patterns over a 30-day period.
```

### 2. Slashing Event Contagion

```
Model the aftermath of a double-sign slashing incident affecting 3 top-10 
validators. Simulate 10,000 delegators with loyalty scores, risk awareness, 
and social network influence. Track reputation recovery curves and measure 
how long until affected validators regain 90% of pre-slash stake.
```

### 3. Delegator Behavior Analysis

```
Simulate delegator switching behavior when a mid-tier validator announces 
4-hour planned maintenance. Model 5,000 delegators with varying time 
horizons, yield sensitivity, and validator relationship strength. Track 
unstaking volumes, validator selection criteria, and social sentiment spread.
```

### 4. Staking Reward Dynamics

```
Predict delegator behavior following a protocol change that reduces staking 
APR from 15% to 10%. Model token holders with varying opportunity cost 
thresholds, DeFi yield awareness, and liquidity needs. Track re-staking 
rates, unstaking queues, and alternative yield-seeking patterns.
```

---

## Network Upgrades & Governance

### 5. Network Upgrade Impact Simulation

```
Simulate validator adoption for a contentious hard fork proposal requiring 
client software updates. Model 100 validators with different technical 
capabilities, upgrade cost sensitivities, and ideological positions. Track 
upgrade timeline, chain split probability, and exchange readiness coordination.
```

### 6. Governance Proposal Testing

```
Model voting patterns for a treasury spending proposal allocating 2M tokens 
to ecosystem development. Simulate 200 voting stakeholders weighted by stake, 
delegation preferences, and proposal affinity. Track lobbying efforts, whale 
influence, quorum achievement, and vote flipping dynamics.
```

### 7. Consensus Mechanism Stress Testing

```
Test Byzantine fault tolerance under a coordinated validator collusion attack 
scenario. Simulate 150 validators where 40% are compromised and attempt 
double-spending. Model honest validator detection, slashing execution, and 
chain finality preservation under varying attack intensities.
```

---

## Infrastructure & Operations

### 8. Infrastructure Provider Strategy

```
Model node operator infrastructure decisions between bare metal (high capex, 
low opex), cloud providers (AWS vs. smaller providers), and decentralized 
infrastructure (Akash, Flux). Simulate 75 operators with capital constraints, 
uptime requirements, and geographic distribution goals. Track provider market 
share and centralization risks.
```

### 9. Validator Set Decentralization

```
Simulate the impact of a 10% stake cap per validator and geographic diversity 
incentives. Model existing whale validators forced to split operations versus 
new entrants. Track Nakamoto coefficient improvement, operational overhead 
increases, and network latency effects.
```

### 10. Rollup Sequencer Decentralization

```
Model competition for decentralized sequencer roles in an optimistic rollup 
transitioning from centralized operation. Simulate 50 infrastructure providers 
bidding for slots based on MEV extraction capabilities, hardware requirements, 
and reputation scores. Track stake requirements, leader rotation fairness, 
and user fee impacts.
```

---

## Security & Attack Scenarios

### 11. MEV Strategy Simulation

```
Simulate validator MEV extraction strategies in a high-volume DeFi environment. 
Model 40 validators with varying ethics profiles, extraction capabilities, and 
user relationship concerns. Track sandwich attack frequency, OFAC compliance 
decisions, and user trust erosion metrics.
```

### 12. Bridge Security Incident Response

```
Model cross-chain asset flow disruptions during a bridge exploit affecting 
$100M in locked value. Simulate validators on both chains, bridge operators, 
and 50,000 affected users. Track message passing delays, emergency pause 
coordination, social panic spread, and recovery fund voting patterns.
```

### 13. Light Client Attack Scenarios

```
Simulate detection and response to a header withholding attack targeting light 
clients. Model 10,000 light client users with varying technical sophistication, 
full node availability, and social information sources. Track attack detection 
latency, user fund protection rates, and mitigation deployment speed.
```

### 14. Cross-Chain Message Propagation

```
Model IBC packet propagation patterns between 5 interconnected chains. Simulate 
relayer competition, validator censoring motivations, and packet prioritization 
based on value at risk. Track message latency distributions, censorship resistance 
metrics, and fee market dynamics.
```

---

## Economic Policy

### 15. Inflation Policy Impact

```
Simulate network participant reactions to a proposal changing token emission 
from 10% to 7% annually with 2% directed to a burn mechanism. Model validators, 
delegators, speculators, and developers with varying time horizons and token 
holdings. Track staking participation rates, price speculation cycles, and 
development funding sustainability.
```

---

## Prompt Structure Guidelines

Each prompt follows a consistent structure optimized for MiroFish simulations:

| Element | Purpose |
|---------|---------|
| **Specific parameters** | Validator counts, token amounts, timeframes for reproducibility |
| **Diverse agent populations** | Realistic attribute distributions across stakeholder types |
| **Clear success metrics** | Quantifiable outcomes for analyzing simulation results |
| **Controllable variables** | Parameters for A/B testing different scenarios |

---

*Use Case Reference Table*

| # | Title | Category |
|---|-------|----------|
| 1 | Validator Behavior Modeling | Validator Behavior & Operations |
| 2 | Slashing Event Contagion | Validator Behavior & Operations |
| 3 | Delegator Behavior Analysis | Validator Behavior & Operations |
| 4 | Staking Reward Dynamics | Validator Behavior & Operations |
| 5 | Network Upgrade Impact Simulation | Network Upgrades & Governance |
| 6 | Governance Proposal Testing | Network Upgrades & Governance |
| 7 | Consensus Mechanism Stress Testing | Network Upgrades & Governance |
| 8 | Infrastructure Provider Strategy | Infrastructure & Operations |
| 9 | Validator Set Decentralization | Infrastructure & Operations |
| 10 | Rollup Sequencer Decentralization | Infrastructure & Operations |
| 11 | MEV Strategy Simulation | Security & Attack Scenarios |
| 12 | Bridge Security Incident Response | Security & Attack Scenarios |
| 13 | Light Client Attack Scenarios | Security & Attack Scenarios |
| 14 | Cross-Chain Message Propagation | Security & Attack Scenarios |
| 15 | Inflation Policy Impact | Economic Policy |
