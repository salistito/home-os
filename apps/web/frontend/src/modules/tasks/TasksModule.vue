<script setup lang="ts">
import PointsChart from "./PointsChart.vue";
import RankingWidget from "./RankingWidget.vue";
import TasksTable from "./TasksTable.vue";
import TodayBoard from "./TodayBoard.vue";
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-4">
    <div class="grid grid-cols-1 items-stretch gap-4 lg:grid-cols-3">
      <div class="grid lg:col-span-2">
        <PointsChart />
      </div>
      <div class="space-y-4">
        <RankingWidget />
        <TodayBoard />
      </div>
    </div>
    <TasksTable />
  </div>
</template>
