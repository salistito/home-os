<script setup lang="ts">
import { icons } from "../lib/icons";
import { moneyHiddenValue, toggleMoneyHidden } from "../lib/money";
import IconButton from "./IconButton.vue";
</script>

<template>
  <IconButton
    :icon="moneyHiddenValue ? icons.eyeOff : icons.eye"
    :label="moneyHiddenValue ? 'Mostrar montos' : 'Ocultar montos'"
    @click="toggleMoneyHidden"
  />
</template>
