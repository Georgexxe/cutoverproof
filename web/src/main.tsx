import "@fontsource/newsreader/latin-600.css";
import "@fontsource/newsreader/latin-700.css";
import "@fontsource/alegreya-sans/latin-400.css";
import "@fontsource/alegreya-sans/latin-500.css";
import "@fontsource/alegreya-sans/latin-700.css";
import React from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "./app.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("CutoverProof root element is missing");
}

createRoot(root).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
