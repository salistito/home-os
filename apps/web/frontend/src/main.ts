import { createApp } from "vue";
import App from "./App.vue";
import "./tailwind.css";

createApp(App).mount("#app");

const splash = document.getElementById("splash");

if (splash) {
  requestAnimationFrame(() => {
    splash.classList.add("is-hidden");
    splash.addEventListener("transitionend", () => splash.remove(), { once: true });
  });
}
