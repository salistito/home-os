<script setup lang="ts">
import PointsChart from "./PointsChart.vue";
import RankingWidget from "./RankingWidget.vue";
import TasksTable from "./TasksTable.vue";
import TodayBoard from "./TodayBoard.vue";
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4">
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <TodayBoard />
      <RankingWidget />
    </div>
    <PointsChart />
    <TasksTable />
  </div>
</template>
