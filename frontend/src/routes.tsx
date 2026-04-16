import { createBrowserRouter, Navigate } from "react-router"
import App from "./App"
import { SourcesPage } from "./pages/sources-page"
import { ExplorerPage } from "./pages/explorer-page"
import { ThemesPage } from "./pages/themes-page"
import { ErrorBoundary, NotFound } from "./components/error-boundary"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    errorElement: <ErrorBoundary />,
    children: [
      { index: true, element: <Navigate to="/explorer" replace /> },
      { path: "explorer", element: <ExplorerPage /> },
      { path: "sources", element: <SourcesPage /> },
      { path: "themes", element: <ThemesPage /> },
      { path: "*", element: <NotFound /> },
    ],
  },
])
