import { createBrowserRouter, Navigate } from "react-router"
import App from "./App"
import { SourcesPage } from "./pages/sources-page"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/sources" replace /> },
      { path: "sources", element: <SourcesPage /> },
    ],
  },
])
