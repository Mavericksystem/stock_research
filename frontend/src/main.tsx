import React from "react";
import ReactDOM from "react-dom/client";
import App from "./app/App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import PrivacyPage from "./pages/Privacy/PrivacyPage";
import { PRIVACY_PATH } from "./layouts/Footer";
import "./index.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Root element #root was not found");
}

// No client-side router: the privacy policy is a standalone page, so a simple
// pathname check is enough. Trailing slash tolerated.
const isPrivacyRoute =
  window.location.pathname.replace(/\/+$/, "") === PRIVACY_PATH;

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <ErrorBoundary>
      {isPrivacyRoute ? <PrivacyPage /> : <App />}
    </ErrorBoundary>
  </React.StrictMode>,
);
