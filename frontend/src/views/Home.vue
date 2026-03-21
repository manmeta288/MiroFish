<template>
  <div class="simulate-root">
    <!-- Google Fonts: Poppins -->
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />

    <!-- ─── Geometric background shapes ─────────────────────────────────── -->
    <div class="shape shape-circle-red" aria-hidden="true"></div>
    <div class="shape shape-square-yellow" aria-hidden="true"></div>
    <div class="shape shape-circle-blue" aria-hidden="true"></div>
    <div class="shape shape-square-black" aria-hidden="true"></div>
    <div class="shape shape-circle-outline" aria-hidden="true"></div>

    <!-- ─── Header ──────────────────────────────────────────────────────── -->
    <header class="site-header">
      <div class="header-inner">
        <div class="logo-group">
          <a href="https://www.nodera.app" class="logo-link" target="_blank" rel="noopener">
            <span class="logo-dot"></span>
            <span class="logo-text">NODERA</span>
          </a>
          <span class="logo-divider"></span>
          <span class="logo-tag">SIMULATE</span>
        </div>
        <nav class="header-nav">
          <a href="https://learn.nodera.app" class="nav-link" target="_blank" rel="noopener">Learn</a>
          <a href="https://www.nodera.app" class="nav-link" target="_blank" rel="noopener">Nodera</a>
        </nav>
      </div>
    </header>

    <!-- ─── Hero ─────────────────────────────────────────────────────────── -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-kicker">
          <span class="kicker-dot"></span>
          VALIDATOR RISK SIMULATION
        </div>
        <h1 class="hero-title">
          Stress-Test Your Network<br />
          <span class="hero-title-accent">Before It Breaks</span>
        </h1>
        <p class="hero-sub">
          Select a blockchain network. Fetch live intelligence. Run a targeted
          simulation. Know your exposure before the market does.
        </p>
      </div>
    </section>

    <!-- ─── Main interaction area ─────────────────────────────────────────── -->
    <main class="main-panel">

      <!-- Step 1: Network selector -->
      <div class="step-block">
        <div class="step-label">
          <span class="step-number">01</span>
          <span class="step-title-text">Choose a Network</span>
        </div>

        <div class="select-wrapper">
          <select
            v-model="selectedNetwork"
            class="network-select"
            :disabled="loadingData"
            @change="onNetworkChange"
          >
            <option value="" disabled>Choose a blockchain network…</option>
            <option v-for="net in networkList" :key="net.slug" :value="net.slug">
              {{ net.display_name }} ({{ net.token }})
            </option>
          </select>
          <span class="select-arrow">▾</span>
        </div>
      </div>

      <!-- Live data strip (visible after selection) -->
      <transition name="fade-slide">
        <div v-if="networkData && !loadingData" class="data-strip">
          <div class="data-pill">
            <span class="pill-label">Price</span>
            <span class="pill-value">${{ formatPrice(networkData.price_usd) }}</span>
            <span
              class="pill-change"
              :class="networkData.price_change_24h >= 0 ? 'positive' : 'negative'"
            >
              {{ networkData.price_change_24h >= 0 ? '+' : '' }}{{ networkData.price_change_24h?.toFixed(1) }}%
            </span>
          </div>
          <div class="data-pill">
            <span class="pill-label">Validators</span>
            <span class="pill-value">{{ networkData.validator_count || '—' }}</span>
          </div>
          <div class="data-pill nakamoto">
            <span class="pill-label">Nakamoto Coefficient</span>
            <span class="pill-value pill-red">{{ networkData.nakamoto_coefficient || '—' }}</span>
          </div>
          <div class="data-pill">
            <span class="pill-label">Staking Ratio</span>
            <span class="pill-value">{{ networkData.staking_ratio ? (networkData.staking_ratio * 100).toFixed(1) + '%' : '—' }}</span>
          </div>
          <div class="data-pill">
            <span class="pill-label">APY</span>
            <span class="pill-value">{{ networkData.staking_apy ? (networkData.staking_apy * 100).toFixed(1) + '%' : '—' }}</span>
          </div>
          <div class="data-pill">
            <span class="pill-label">Sources</span>
            <span class="pill-value pill-small">{{ networkData.data_sources_used?.join(', ') || 'public apis' }}</span>
          </div>
        </div>
      </transition>

      <!-- Loading shimmer -->
      <div v-if="loadingData" class="loading-state">
        <div class="spinner"></div>
        <span class="loading-label">Fetching live network intelligence…</span>
      </div>

      <!-- API error notice -->
      <div v-if="dataError" class="error-notice">
        <span class="error-icon">⚠</span>
        {{ dataError }}
      </div>

      <!-- Step 2: Scenario cards -->
      <transition name="fade-slide">
        <div v-if="networkData && !loadingData && !dataError" class="step-block cards-block">
          <div class="step-label">
            <span class="step-number">02</span>
            <span class="step-title-text">Choose a Scenario</span>
          </div>

          <div class="cards-grid">
            <div
              v-for="(card, idx) in scenarios"
              :key="idx"
              class="scenario-card"
              :class="[`card-${card.color}`, { selected: selectedScenario === idx }]"
              @click="selectScenario(idx)"
              role="button"
              :aria-selected="selectedScenario === idx"
            >
              <div class="card-category">{{ card.category }}</div>
              <div class="card-title">{{ card.title }}</div>
              <div class="card-subtitle">{{ card.subtitle }}</div>
              <p class="card-desc">{{ card.description }}</p>
              <div class="card-cta">
                <span>{{ selectedScenario === idx ? 'Selected ✓' : 'Select scenario →' }}</span>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <!-- Step 3: Prompt editor + launch -->
      <transition name="fade-slide">
        <div v-if="selectedScenario !== null" class="step-block prompt-block">
          <div class="step-label">
            <span class="step-number">03</span>
            <span class="step-title-text">Review &amp; Customise Prompt</span>
          </div>
          <div class="prompt-wrapper">
            <textarea
              v-model="simulationPrompt"
              class="prompt-textarea"
              rows="7"
              placeholder="Your simulation prompt will appear here…"
            ></textarea>
            <div class="prompt-hint">
              You can edit this prompt freely. The simulation will also use live
              {{ networkData?.display_name }} data fetched above as its knowledge seed.
            </div>
          </div>

          <button
            class="run-btn"
            :disabled="!simulationPrompt.trim() || launching"
            @click="launchSimulation"
          >
            <span v-if="!launching">Run Simulation →</span>
            <span v-else class="launching-dots">
              <span>Initialising</span>
              <span class="dot-1">.</span><span class="dot-2">.</span><span class="dot-3">.</span>
            </span>
          </button>
        </div>
      </transition>

    </main>

    <!-- ─── Footer ───────────────────────────────────────────────────────── -->
    <footer class="site-footer">
      <span>Infrastructure intelligence for serious operators.</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { setPendingUpload } from '../store/pendingUpload'
import service from '../api/index'

const router = useRouter()

// ─── State ────────────────────────────────────────────────────────────────────
const networkList = ref([])
const selectedNetwork = ref('')
const networkData = ref(null)
const loadingData = ref(false)
const dataError = ref('')
const selectedScenario = ref(null)
const simulationPrompt = ref('')
const launching = ref(false)

// ─── Fallback network list (in case API fails) ────────────────────────────────
const FALLBACK_NETWORKS = [
  { slug: 'ethereum', display_name: 'Ethereum', token: 'ETH' },
  { slug: 'cosmos', display_name: 'Cosmos Hub', token: 'ATOM' },
  { slug: 'celestia', display_name: 'Celestia', token: 'TIA' },
  { slug: 'osmosis', display_name: 'Osmosis', token: 'OSMO' },
  { slug: 'injective', display_name: 'Injective', token: 'INJ' },
  { slug: 'sei', display_name: 'Sei', token: 'SEI' },
  { slug: 'neutron', display_name: 'Neutron', token: 'NTRN' },
  { slug: 'dymension', display_name: 'Dymension', token: 'DYM' },
  { slug: 'polkadot', display_name: 'Polkadot', token: 'DOT' },
  { slug: 'solana', display_name: 'Solana', token: 'SOL' },
  { slug: 'near', display_name: 'NEAR Protocol', token: 'NEAR' },
]

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const res = await service.get('/network/list')
    if (res.success && res.data && res.data.length > 0) {
      networkList.value = res.data
    } else {
      networkList.value = FALLBACK_NETWORKS
    }
  } catch (e) {
    console.warn('Could not load network list from API, using fallback:', e)
    networkList.value = FALLBACK_NETWORKS
  }
})

// ─── Computed: 3 scenarios built from live data ───────────────────────────────
const scenarios = computed(() => {
  const d = networkData.value
  if (!d) return []

  const net = d.display_name
  const token = d.token
  const nc = d.nakamoto_coefficient || '?'
  const topV = d.top_validators?.[0]?.name || 'a leading validator'
  const topVPct = d.top_validators?.[0]?.voting_power_pct?.toFixed(1) || '?'
  const top3 = d.top_validators?.slice(0, 3).map(v => v.name).join(', ') || 'top validators'
  const smallCount = Math.max((d.validator_count || 50) - 20, 5)
  const apy = d.staking_apy ? (d.staking_apy * 100).toFixed(1) : '?'
  const propId = d.governance_proposals?.[0]?.id || '001'
  const propTitle = d.governance_proposals?.[0]?.title || 'a governance upgrade proposal'
  const stakingPct = d.staking_ratio ? (d.staking_ratio * 100).toFixed(0) : '?'

  return [
    {
      category: 'NETWORK RISK',
      color: 'red',
      title: 'Nakamoto Crisis',
      subtitle: 'Validator Concentration & Collusion Risk',
      description: `On ${net}, only ${nc} validators need to coordinate to exceed the 33% Byzantine fault threshold. Model what happens when they collude.`,
      prompt:
        `Simulate a critical scenario on ${net} (${token}). ` +
        `The network's Nakamoto Coefficient is ${nc}, meaning only ${nc} validators control enough stake ` +
        `to disrupt consensus. The top validators—${top3}—discover a shared financial interest in ` +
        `front-running governance proposal #${propId} ("${propTitle}"). ` +
        `They form a private coordination channel and begin voting as a bloc, selectively censoring ` +
        `competing validator messages. Model the chain reaction: how do delegators respond, ` +
        `what happens to token price, and can the remaining validators mount a defence? ` +
        `Show the sequence of events across 72 hours.`,
    },
    {
      category: 'VALIDATOR DYNAMICS',
      color: 'blue',
      title: 'The Commission War',
      subtitle: 'Race to Zero & Validator Sustainability',
      description: `${net} staking yields ~${apy}% APY. When ${topV} (${topVPct}% of stake) slashes commission to 0%, delegators flood in. Model the cascading sustainability crisis across the validator set.`,
      prompt:
        `Simulate a commission war on ${net} (${token}). ` +
        `${topV}, currently controlling ${topVPct}% of stake, announces a permanent 0% commission rate. ` +
        `Within 48 hours, delegators begin migrating en masse from mid-tier validators. ` +
        `Mid-tier validators retaliate by also cutting commission to 0%. ` +
        `Smaller validators, running on thin margins with staking APY at ${apy}%, ` +
        `cannot sustain operations at 0% commission and begin signalling exit. ` +
        `Model the domino effect: which validator archetypes survive, how does voting power redistribute, ` +
        `does the Nakamoto Coefficient improve or worsen, and what is the community's response?`,
    },
    {
      category: 'COMMUNITY ACTION',
      color: 'yellow',
      title: 'Community Defense',
      subtitle: 'Stake With Small Validators Campaign',
      description: `${nc} validators control the safety threshold on ${net}. Model how a coordinated community campaign to redistribute stake to small validators improves network resilience.`,
      prompt:
        `Simulate a "stake with small validators" grassroots campaign on ${net} (${token}). ` +
        `A community forum post goes viral, revealing that only ${nc} validators control over 33% of stake. ` +
        `An organised movement — driven by retail stakers who collectively hold ${100 - parseInt(stakingPct || 50)}% of ` +
        `unstaked supply — begins a coordinated migration to the bottom ${smallCount} validators. ` +
        `Track the campaign's spread: how much stake migrates per day, how the Nakamoto Coefficient changes, ` +
        `whether large validators respond (e.g. cutting commission, PR campaigns), ` +
        `and how token price and staking ratio shift as more community members lock their ${token} ` +
        `to support smaller, independent node operators. ` +
        `Show both the optimistic and adversarial outcomes over 30 days.`,
    },
  ]
})

// ─── Methods ──────────────────────────────────────────────────────────────────

const onNetworkChange = async () => {
  if (!selectedNetwork.value) return
  selectedScenario.value = null
  simulationPrompt.value = ''
  networkData.value = null
  dataError.value = ''
  loadingData.value = true

  try {
    const res = await service.get('/network/fetch', { params: { network: selectedNetwork.value } })
    if (res.success) {
      networkData.value = res.data
    } else {
      dataError.value = res.error || 'Failed to fetch network data. Please try again.'
    }
  } catch (e) {
    dataError.value = 'Network API unavailable. Please check your connection or try again later.'
    console.error('Network fetch error:', e)
  } finally {
    loadingData.value = false
  }
}

const selectScenario = (idx) => {
  selectedScenario.value = idx
  simulationPrompt.value = scenarios.value[idx].prompt
  // Scroll to prompt block after selection
  setTimeout(() => {
    const el = document.querySelector('.prompt-block')
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, 120)
}

const launchSimulation = () => {
  if (!simulationPrompt.value.trim() || launching.value) return
  launching.value = true

  const reportText = networkData.value?.synthetic_report || `Network: ${networkData.value?.display_name}\n${simulationPrompt.value}`
  const reportFile = new File([reportText], 'network-intelligence-report.txt', { type: 'text/plain' })

  setPendingUpload([reportFile], simulationPrompt.value)
  router.push({ name: 'Process', params: { projectId: 'new' } })
}

const formatPrice = (p) => {
  if (!p) return '—'
  if (p >= 1000) return p.toLocaleString('en-US', { maximumFractionDigits: 0 })
  if (p >= 1) return p.toFixed(2)
  return p.toFixed(4)
}
</script>

<style scoped>
/* ─── Variables ──────────────────────────────────────────────────────────── */
:root {
  --red: #ff3b30;
  --blue: #017bfe;
  --yellow: #ffcd00;
  --black: #000000;
  --white: #ffffff;
}

/* ─── Root & font ────────────────────────────────────────────────────────── */
.simulate-root {
  font-family: 'Poppins', sans-serif;
  background: #ffffff;
  color: #000000;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

/* ─── Geometric background shapes ───────────────────────────────────────── */
.shape {
  position: fixed;
  z-index: 0;
  pointer-events: none;
}
.shape-circle-red {
  width: 480px;
  height: 480px;
  border-radius: 50%;
  background: #ff3b30;
  opacity: 0.06;
  top: -120px;
  right: -140px;
}
.shape-square-yellow {
  width: 260px;
  height: 260px;
  background: #ffcd00;
  opacity: 0.12;
  bottom: 180px;
  left: -80px;
  transform: rotate(18deg);
}
.shape-circle-blue {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: #017bfe;
  opacity: 0.07;
  top: 45%;
  right: 5%;
}
.shape-square-black {
  width: 100px;
  height: 100px;
  background: #000000;
  opacity: 0.03;
  top: 30%;
  left: 6%;
  transform: rotate(30deg);
}
.shape-circle-outline {
  width: 320px;
  height: 320px;
  border-radius: 50%;
  border: 3px solid #ff3b30;
  opacity: 0.05;
  bottom: -80px;
  right: 10%;
}

/* ─── Header ─────────────────────────────────────────────────────────────── */
.site-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  border-bottom: 3px solid #000;
  background: #fff;
}
.simulate-root {
  padding-top: 70px; /* Account for fixed header height */
}
.header-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 18px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.logo-group {
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo-link {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #000;
}
.logo-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #ff3b30;
  flex-shrink: 0;
}
.logo-text {
  font-size: 22px;
  font-weight: 900;
  letter-spacing: 0.06em;
  color: #000;
}
.logo-divider {
  width: 1px;
  height: 24px;
  background: #ddd;
}
.logo-tag {
  font-size: 11px;
  font-weight: 700;
  background: #000;
  color: #fff;
  padding: 3px 8px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  pointer-events: none;
  user-select: none;
  cursor: default;
}
.header-nav {
  display: flex;
  gap: 28px;
}
.nav-link {
  font-size: 13px;
  font-weight: 600;
  color: #000;
  text-decoration: none;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  transition: color 0.15s;
}
.nav-link:hover { color: #ff3b30; }

/* ─── Hero ───────────────────────────────────────────────────────────────── */
.hero {
  position: relative;
  z-index: 5;
  padding: 80px 32px 56px;
  border-bottom: 3px solid #000;
  background: #fff;
}
.hero-inner {
  max-width: 1100px;
  margin: 0 auto;
}
.hero-kicker {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #666;
  margin-bottom: 24px;
}
.kicker-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ff3b30;
}
.hero-title {
  font-size: clamp(42px, 7vw, 80px);
  font-weight: 900;
  line-height: 1.05;
  letter-spacing: -0.03em;
  color: #000;
  margin-bottom: 24px;
}
.hero-title-accent {
  color: #ff3b30;
}
.hero-sub {
  font-size: 18px;
  font-weight: 400;
  line-height: 1.65;
  color: #444;
  max-width: 560px;
}

/* ─── Main panel ─────────────────────────────────────────────────────────── */
.main-panel {
  position: relative;
  z-index: 5;
  max-width: 1100px;
  margin: 0 auto;
  padding: 56px 32px 80px;
  display: flex;
  flex-direction: column;
  gap: 56px;
}

/* ─── Step blocks ────────────────────────────────────────────────────────── */
.step-block {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.step-label {
  display: flex;
  align-items: baseline;
  gap: 14px;
}
.step-number {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  color: #bbb;
  font-feature-settings: 'tnum';
}
.step-title-text {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: #000;
}

/* ─── Network selector ───────────────────────────────────────────────────── */
.select-wrapper {
  position: relative;
  display: inline-block;
  width: 100%;
  max-width: 440px;
}
.network-select {
  width: 100%;
  appearance: none;
  -webkit-appearance: none;
  background: #fff;
  border: 3px solid #000;
  box-shadow: 6px 6px 0 #000;
  padding: 14px 48px 14px 18px;
  font-family: 'Poppins', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: #000;
  cursor: pointer;
  outline: none;
  transition: box-shadow 0.15s;
}
.network-select:focus {
  box-shadow: 8px 8px 0 #ff3b30;
  border-color: #ff3b30;
}
.network-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.select-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  pointer-events: none;
  color: #000;
}

/* ─── Data strip ─────────────────────────────────────────────────────────── */
.data-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.data-pill {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: #f5f5f5;
  border: 2px solid #000;
  padding: 10px 16px;
  min-width: 110px;
  box-shadow: 4px 4px 0 #000;
}
.data-pill.nakamoto { background: #fff0ef; border-color: #ff3b30; box-shadow: 4px 4px 0 #ff3b30; }
.pill-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #888;
}
.pill-value {
  font-size: 16px;
  font-weight: 800;
  color: #000;
}
.pill-red { color: #ff3b30; }
.pill-small { font-size: 11px; font-weight: 600; }
.pill-change.positive { font-size: 11px; font-weight: 700; color: #15803d; }
.pill-change.negative { font-size: 11px; font-weight: 700; color: #ff3b30; }

/* ─── Loading ─────────────────────────────────────────────────────────────── */
.loading-state {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 0;
}
.spinner {
  width: 22px;
  height: 22px;
  border: 3px solid #e0e0e0;
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-label { font-size: 14px; font-weight: 600; color: #555; }

/* ─── Error ───────────────────────────────────────────────────────────────── */
.error-notice {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border: 2px solid #ff3b30;
  background: #fff5f5;
  font-size: 13px;
  font-weight: 600;
  color: #cc0000;
}
.error-icon { font-size: 16px; }

/* ─── Scenario cards ─────────────────────────────────────────────────────── */
.cards-block { gap: 28px; }
.cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
@media (max-width: 840px) {
  .cards-grid { grid-template-columns: 1fr; }
}

.scenario-card {
  border: 3px solid #000;
  box-shadow: 6px 6px 0 #000;
  padding: 28px 24px;
  background: #fff;
  cursor: pointer;
  transition: transform 0.12s, box-shadow 0.12s;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.scenario-card:hover {
  transform: translate(-3px, -3px);
  box-shadow: 9px 9px 0 #000;
}
.scenario-card.selected {
  transform: translate(-3px, -3px);
}

/* Color accents */
.card-red { border-left: 8px solid #ff3b30; }
.card-red.selected { background: #fff5f4; box-shadow: 9px 9px 0 #ff3b30; }
.card-blue { border-left: 8px solid #017bfe; }
.card-blue.selected { background: #f0f7ff; box-shadow: 9px 9px 0 #017bfe; }
.card-yellow { border-left: 8px solid #ffcd00; }
.card-yellow.selected { background: #fffdf0; box-shadow: 9px 9px 0 #000; border-color: #000; }

.card-category {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #999;
}
.card-red .card-category { color: #ff3b30; }
.card-blue .card-category { color: #017bfe; }
.card-yellow .card-category { color: #a08000; }

.card-title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #000;
  line-height: 1.2;
}
.card-subtitle {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  line-height: 1.4;
}
.card-desc {
  font-size: 13px;
  color: #444;
  line-height: 1.6;
  flex: 1;
}
.card-cta {
  margin-top: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #000;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

/* ─── Prompt block ───────────────────────────────────────────────────────── */
.prompt-block { gap: 20px; }
.prompt-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.prompt-textarea {
  font-family: 'Poppins', sans-serif;
  font-size: 14px;
  line-height: 1.7;
  color: #000;
  background: #fff;
  border: 3px solid #000;
  box-shadow: 6px 6px 0 #000;
  padding: 18px 20px;
  resize: vertical;
  outline: none;
  transition: box-shadow 0.15s;
}
.prompt-textarea:focus {
  box-shadow: 8px 8px 0 #017bfe;
  border-color: #017bfe;
}
.prompt-hint {
  font-size: 12px;
  color: #888;
  font-weight: 500;
}

/* ─── Run button ─────────────────────────────────────────────────────────── */
.run-btn {
  font-family: 'Poppins', sans-serif;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  background: #000;
  color: #fff;
  border: 3px solid #000;
  box-shadow: 6px 6px 0 #ff3b30;
  padding: 18px 48px;
  cursor: pointer;
  align-self: flex-start;
  transition: transform 0.12s, box-shadow 0.12s;
}
.run-btn:hover:not(:disabled) {
  transform: translate(-3px, -3px);
  box-shadow: 9px 9px 0 #ff3b30;
}
.run-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: 3px 3px 0 #ccc;
  border-color: #ccc;
}
.launching-dots span:not(.dot-1):not(.dot-2):not(.dot-3) { vertical-align: baseline; }
.dot-1 { animation: blink 1s infinite 0s; }
.dot-2 { animation: blink 1s infinite 0.2s; }
.dot-3 { animation: blink 1s infinite 0.4s; }
@keyframes blink { 0%, 100% { opacity: 0.2; } 50% { opacity: 1; } }

/* ─── Footer ─────────────────────────────────────────────────────────────── */
.site-footer {
  position: relative;
  z-index: 5;
  border-top: 3px solid #000;
  padding: 32px;
  font-size: 15px;
  font-weight: 600;
  color: #333;
  background: #f5f5f5;
  text-align: center;
  letter-spacing: 0.02em;
}

/* ─── Transitions ────────────────────────────────────────────────────────── */
.fade-slide-enter-active { transition: opacity 0.35s, transform 0.35s; }
.fade-slide-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-slide-enter-from { opacity: 0; transform: translateY(16px); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
