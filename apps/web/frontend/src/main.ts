import { createApp } from "vue";
import "./tailwind.css";
import App from "./App.vue";

createApp(App).mount("#app");

const splash = document.getElementById("splash");
if (splash) {
  requestAnimationFrame(() => {
    splash.classList.add("is-hidden");
    splash.addEventListener("transitionend", () => splash.remove(), { once: true });
  });
}
