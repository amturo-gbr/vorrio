import DefaultTheme from "vitepress/theme";
import ApiReference from "./components/ApiReference.vue";
import LocaleRedirect from "./components/LocaleRedirect.vue";
import Layout from "./Layout.vue";
import "./custom.css";

export default {
  extends: DefaultTheme,
  Layout,
  enhanceApp({ app }) {
    app.component("ApiReference", ApiReference);
    app.component("LocaleRedirect", LocaleRedirect);
  },
};
