<template>
  <div class="main-view">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')"><span class="brand-dot"></span><span class="brand-name">NODERA</span><span class="brand-tag">SIMULATE</span></div>
      </div>
      
      <div class="header-center">
        <div class="view-switcher">
          <button 
            v-for="mode in ['graph', 'split', 'workbench']" 
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { graph: 'Graph', split: 'Split', workbench: 'Workbench' }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <div class="workflow-step">
          <span class="step-num">Step 3/5</span>
          <span class="step-name">Run Simulation</span>
        </div>
        <div class="step-divider"></div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
        <button
          class="restart-btn"
          type="button"
          :disabled="restartBusy"
          @click="handleRestartStep"
          title="Stop and restart the simulation run on this page"
        >
          ↺ Restart step
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="content-area">
      <!-- Left Panel: Graph -->
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <GraphPanel 
          :graphData="graphData"
          :loading="graphLoading"
          :currentPhase="3"
          :isSimulating="isSimulating"
          @refresh="refreshGraph"
          @toggle-maximize="toggleMaximize('graph')"
        />
      </div>

      <!-- Right Panel: Step3 Run Simulation (mount only after simulation exists on server) -->
      <div class="panel-wrapper right" :style="rightPanelStyle">
        <div v-if="loadingSimulation" class="step-bootstrap">
          <div class="bootstrap-spinner"></div>
          <p>Loading simulation…</p>
        </div>
        <div v-else-if="simulationNotFound" class="step-blocked-panel">
          <div class="blocked-card">
            <h2 class="blocked-title">Simulation not found</h2>
            <p class="blocked-lead">
              <code class="blocked-id">{{ currentSimulationId }}</code> is not on this server anymore.
            </p>
            <p class="blocked-copy">
              That usually means the app was redeployed, storage was reset, or you’re using an old bookmark.
              Step 3 cannot run without that server-side simulation.
            </p>
            <div class="blocked-actions">
              <button type="button" class="blocked-btn primary" @click="goHome">Start from home</button>
            </div>
            <p class="blocked-hint">
              You’ll need to run the flow again: choose a network → build the knowledge graph → environment setup → run simulation.
            </p>
          </div>
        </div>
        <div v-else-if="loadErrorMessage" class="step-blocked-panel">
          <div class="blocked-card">
            <h2 class="blocked-title">Could not load simulation</h2>
            <p class="blocked-copy">{{ loadErrorMessage }}</p>
            <div class="blocked-actions">
              <button type="button" class="blocked-btn primary" @click="retryLoad">Retry</button>
              <button type="button" class="blocked-btn ghost" @click="goHome">Home</button>
            </div>
          </div>
        </div>
        <Step3Simulation
          v-else-if="simulationReady"
          :key="step3Key"
          :simulationId="currentSimulationId"
          :maxRounds="maxRounds"
          :minutesPerRound="minutesPerRound"
          :projectData="projectData"
          :graphData="graphData"
          :systemLogs="systemLogs"
          @go-back="handleGoBack"
          @next-step="handleNextStep"
          @add-log="addLog"
          @update-status="updateStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step3Simulation from '../components/Step3Simulation.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, getSimulationConfig, stopSimulation, closeSimulationEnv, getEnvStatus } from '../api/simulation'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  simulationId: String
})

// Layout State
const viewMode = ref('split')

// Data State
const currentSimulationId = ref(route.params.simulationId)
// Read maxRounds from query params at init so child component gets it immediately
const maxRounds = ref(route.query.maxRounds ? parseInt(route.query.maxRounds) : null)
const minutesPerRound = ref(30) // default: 30 minutes per round
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('idle') // idle | processing | completed | error (Step 3 updates this)
const step3Key = ref(0)
const restartBusy = ref(false)
const loadingSimulation = ref(true)
const simulationReady = ref(false)
const simulationNotFound = ref(false)
const loadErrorMessage = ref('')

// --- Computed Layout Styles ---
const leftPanelStyle = computed(() => {
  if (viewMode.value === 'graph') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'workbench') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'workbench') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'graph') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '50%', opacity: 1, transform: 'translateX(0)' }
})

// --- Status Computed ---
const statusClass = computed(() => {
  if (loadingSimulation.value) return 'loading'
  if (simulationNotFound.value || loadErrorMessage.value) return 'error'
  return currentStatus.value
})

const statusText = computed(() => {
  if (loadingSimulation.value) return 'Loading'
  if (simulationNotFound.value) return 'Unavailable'
  if (loadErrorMessage.value) return 'Error'
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Completed'
  if (currentStatus.value === 'processing') return 'Running'
  return 'Ready'
})

const isSimulating = computed(() => simulationReady.value && currentStatus.value === 'processing')

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

const goHome = () => {
  router.push('/')
}

const retryLoad = async () => {
  if (restartBusy.value) return
  restartBusy.value = true
  loadErrorMessage.value = ''
  simulationNotFound.value = false
  loadingSimulation.value = true
  try {
    const ok = await loadSimulationData()
    if (ok) {
      step3Key.value += 1
      simulationReady.value = true
      currentStatus.value = 'idle'
    }
  } finally {
    loadingSimulation.value = false
    restartBusy.value = false
  }
}

// --- Layout Methods ---
const toggleMaximize = (target) => {
  if (viewMode.value === target) {
    viewMode.value = 'split'
  } else {
    viewMode.value = target
  }
}

const handleRestartStep = async () => {
  if (restartBusy.value) return
  restartBusy.value = true
  addLog('↺ Restarting simulation run on this page…')
  stopGraphRefresh()
  simulationReady.value = false
  simulationNotFound.value = false
  loadErrorMessage.value = ''
  try {
    try {
      await stopSimulation({ simulation_id: currentSimulationId.value })
    } catch {
      /* best-effort stop before remount */
    }
    currentStatus.value = 'idle'
    await nextTick()
    loadingSimulation.value = true
    const ok = await loadSimulationData()
    loadingSimulation.value = false
    if (ok) {
      step3Key.value += 1
      simulationReady.value = true
    } else {
      currentStatus.value = 'error'
    }
  } finally {
    restartBusy.value = false
  }
}

const handleGoBack = async () => {
  if (simulationNotFound.value) {
    goHome()
    return
  }
  // Close any running simulation before returning to Step 2
  addLog('Preparing to return to Step 2, closing simulation…')
  
  // Stop polling
  stopGraphRefresh()
  
  try {
    // Try graceful close first
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog('Closing simulation environment…')
      try {
        await closeSimulationEnv({ 
          simulation_id: currentSimulationId.value,
          timeout: 10
        })
        addLog('✓ Simulation environment closed')
      } catch (closeErr) {
        addLog('Close failed, attempting force stop…')
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('✓ Simulation force stopped')
        } catch (stopErr) {
          addLog(`Force stop failed: ${stopErr.message}`)
        }
      }
    } else {
      // Environment not running; check if process needs stopping
      if (isSimulating.value) {
        addLog('Stopping simulation process…')
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog('✓ Simulation stopped')
        } catch (err) {
          addLog(`Stop simulation failed: ${err.message}`)
        }
      }
    }
  } catch (err) {
    addLog(`Check simulation status failed: ${err.message}`)
  }
  
  // Return to Step 2 (Environment Setup)
  router.push({ name: 'Simulation', params: { simulationId: currentSimulationId.value } })
}

const handleNextStep = () => {
  // Step3Simulation component handles report generation and routing directly
  // This method is a fallback only
  addLog('Entering Step 4: Generate Report')
}

// --- Data Logic ---
const loadSimulationData = async () => {
  simulationNotFound.value = false
  loadErrorMessage.value = ''
  try {
    addLog(`Loading simulation data: ${currentSimulationId.value}`)

    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data

      try {
        const configRes = await getSimulationConfig(currentSimulationId.value)
        if (configRes.success && configRes.data?.time_config?.minutes_per_round) {
          minutesPerRound.value = configRes.data.time_config.minutes_per_round
          addLog(`Time config: each round ${minutesPerRound.value} mins`)
        }
      } catch {
        addLog(`Failed to get time config, using default: ${minutesPerRound.value} min/round`)
      }

      if (simData.project_id) {
        const projRes = await getProject(simData.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(`Project loaded: ${projRes.data.project_id}`)

          if (projRes.data.graph_id) {
            await loadGraph(projRes.data.graph_id)
          }
        }
      }
      return true
    }

    const msg = simRes.error || 'Unknown error'
    loadErrorMessage.value = msg
    addLog(`Failed to load simulation data: ${msg}`)
    updateStatus('error')
    return false
  } catch (err) {
    const status = err?.response?.status
    const is404 = status === 404 || /404/.test(String(err.message || ''))
    if (is404) {
      simulationNotFound.value = true
      addLog(
        'Simulation not found on the server (redeploy, storage reset, or stale URL). Start a new workflow from the home page.'
      )
      updateStatus('error')
      return false
    }
    const msg = err.message || 'Unknown error'
    loadErrorMessage.value = msg
    addLog(`Load error: ${msg}`)
    updateStatus('error')
    return false
  }
}

const loadGraph = async (graphId) => {
  // Suppress full-screen loading during auto-refresh to prevent flicker
  // Show loading on manual refresh or initial load
  if (!isSimulating.value) {
    graphLoading.value = true
  }
  
  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      if (!isSimulating.value) {
        addLog('Graph data loaded')
      }
    }
  } catch (err) {
    addLog(`Graph load failed: ${err.message}`)
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

// --- Auto Refresh Logic ---
let graphRefreshTimer = null

const startGraphRefresh = () => {
  if (graphRefreshTimer) return
  addLog('Graph auto-refresh enabled (30s)')
  // Refresh immediately, then every 30 s
  graphRefreshTimer = setInterval(refreshGraph, 30000)
}

const stopGraphRefresh = () => {
  if (graphRefreshTimer) {
    clearInterval(graphRefreshTimer)
    graphRefreshTimer = null
    addLog('Graph auto-refresh stopped')
  }
}

watch(isSimulating, (newValue) => {
  if (!simulationReady.value) {
    stopGraphRefresh()
    return
  }
  if (newValue) {
    startGraphRefresh()
  } else {
    stopGraphRefresh()
  }
}, { immediate: true })

watch(
  () => route.params.simulationId,
  async (id) => {
    if (!id || id === currentSimulationId.value) return
    currentSimulationId.value = id
    simulationReady.value = false
    simulationNotFound.value = false
    loadErrorMessage.value = ''
    stopGraphRefresh()
    loadingSimulation.value = true
    currentStatus.value = 'idle'
    const ok = await loadSimulationData()
    loadingSimulation.value = false
    if (ok) {
      step3Key.value += 1
      simulationReady.value = true
    }
  }
)

onMounted(async () => {
  addLog('SimulationRunView Initializing')

  if (maxRounds.value) {
    addLog(`Custom simulation rounds: ${maxRounds.value}`)
  }

  loadingSimulation.value = true
  const ok = await loadSimulationData()
  loadingSimulation.value = false
  if (ok) {
    simulationReady.value = true
  }
})

onUnmounted(() => {
  stopGraphRefresh()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #FFF;
  overflow: hidden;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

/* Header */
.app-header {
  height: 60px;
  border-bottom: 1px solid #EAEAEA;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #FFF;
  z-index: 100;
  position: relative;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.brand-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ff3b30;
  flex-shrink: 0;
}
.brand-name {
  font-family: 'Poppins', sans-serif;
  font-weight: 900;
  font-size: 16px;
  letter-spacing: 0.06em;
  color: #000;
}
.brand-tag {
  font-family: 'Poppins', sans-serif;
  font-size: 10px;
  font-weight: 700;
  background: #000;
  color: #fff;
  padding: 2px 6px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.view-switcher {
  display: flex;
  background: #F5F5F5;
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: #FFF;
  color: #000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
  color: #000;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #E0E0E0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #CCC;
}

.status-indicator.loading .dot { background: #607D8B; animation: pulse 1s infinite; }
.status-indicator.processing .dot { background: #FF5722; animation: pulse 1s infinite; }
.status-indicator.completed .dot { background: #4CAF50; }
.status-indicator.error .dot { background: #F44336; }

@keyframes pulse { 50% { opacity: 0.5; } }

.step-bootstrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: #666;
  font-size: 14px;
}
.bootstrap-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #EAEAEA;
  border-top-color: #ff3b30;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.step-blocked-panel {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  background: #fafafa;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
.blocked-card {
  max-width: 420px;
  background: #fff;
  border: 1px solid #eaeaea;
  border-radius: 8px;
  padding: 28px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}
.blocked-title {
  font-family: 'Poppins', sans-serif;
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #111;
}
.blocked-lead {
  margin: 0 0 8px;
  font-size: 14px;
  color: #444;
  line-height: 1.5;
}
.blocked-id {
  font-size: 12px;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  word-break: break-all;
}
.blocked-copy {
  margin: 0 0 16px;
  font-size: 13px;
  color: #666;
  line-height: 1.55;
}
.blocked-hint {
  margin: 16px 0 0;
  font-size: 12px;
  color: #888;
  line-height: 1.5;
}
.blocked-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.blocked-btn {
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 600;
  padding: 10px 18px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
}
.blocked-btn.primary {
  background: #000;
  color: #fff;
}
.blocked-btn.primary:hover {
  background: #333;
}
.blocked-btn.ghost {
  background: #fff;
  color: #333;
  border: 1px solid #ddd;
}
.blocked-btn.ghost:hover {
  background: #f5f5f5;
}

/* Content */
.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
  will-change: width, opacity, transform;
}

.panel-wrapper.left {
  border-right: 1px solid #EAEAEA;
}
</style>
<style src="../assets/process-restart-btn.css"></style>

