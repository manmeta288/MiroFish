<template>
  <nav class="workflow-step-nav" aria-label="Workflow navigation">
    <span class="nav-label">Steps</span>
    <template v-if="projectId">
      <router-link
        class="nav-link"
        :to="{ name: 'Process', params: { projectId } }"
      >Process</router-link>
      <span class="nav-sep">·</span>
    </template>
    <template v-if="simulationId">
      <router-link
        class="nav-link"
        :to="{ name: 'Simulation', params: { simulationId } }"
      >Environment</router-link>
      <span class="nav-sep">·</span>
      <router-link
        class="nav-link"
        :to="{ name: 'SimulationRun', params: { simulationId } }"
      >Run</router-link>
      <span class="nav-sep">·</span>
    </template>
    <template v-if="reportId">
      <router-link
        class="nav-link"
        :to="{ name: 'Report', params: { reportId } }"
      >Report</router-link>
      <span class="nav-sep">·</span>
      <router-link
        class="nav-link"
        :to="{ name: 'Interaction', params: { reportId } }"
      >Interact</router-link>
    </template>
  </nav>
</template>

<script setup>
defineProps({
  projectId: { type: String, default: '' },
  simulationId: { type: String, default: '' },
  reportId: { type: String, default: '' }
})
</script>

<style scoped>
.workflow-step-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 4px;
  font-size: 12px;
  color: #666;
  max-width: 420px;
}
.nav-label {
  font-weight: 600;
  color: #999;
  margin-right: 4px;
}
.nav-link {
  color: #333;
  text-decoration: none;
  border-bottom: 1px solid transparent;
}
.nav-link:hover {
  border-bottom-color: #333;
}
.nav-link.router-link-active {
  font-weight: 600;
  color: #000;
}
.nav-sep {
  color: #ccc;
  user-select: none;
}
</style>
