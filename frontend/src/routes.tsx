import { createBrowserRouter, Navigate } from "react-router"
import App from "./App"
import { SourcesPage } from "./pages/sources-page"
import { ErrorBoundary, NotFound } from "./components/error-boundary"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    errorElement: <ErrorBoundary />,
    children: [
      { index: true, element: <Navigate to="/sources" replace /> },
      { path: "sources", element: <SourcesPage /> },
      { path: "*", element: <NotFound /> },
    ],
  },
])
