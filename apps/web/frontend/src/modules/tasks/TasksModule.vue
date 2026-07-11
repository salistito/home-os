<script setup lang="ts">
import PointsChart from "./PointsChart.vue";
import RankingWidget from "./RankingWidget.vue";
import TasksTable from "./TasksTable.vue";
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4">
    <div class="grid grid-cols-1 items-start gap-4 lg:grid-cols-3">
      <div class="lg:col-span-2">
        <TasksTable />
      </div>
      <RankingWidget />
    </div>
    <PointsChart />
  </div>
</template>
