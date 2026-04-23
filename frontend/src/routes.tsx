import { createBrowserRouter } from "react-router"
import App from "./App"
import { SourcesPage } from "./pages/sources-page"
import { ExplorerPage } from "./pages/explorer-page"
import { ThemesPage } from "./pages/themes-page"
import { ReportsPage } from "./pages/reports-page"
import { ReportDetailPage } from "./pages/report-detail-page"
import { DashboardPage } from "./pages/dashboard-page"
import { EvalPage } from "./pages/eval-page"
import { RecommendationDetailPage } from "./pages/recommendation-detail-page"
import { ErrorBoundary, NotFound } from "./components/error-boundary"
import { SmartRedirect } from "./components/smart-redirect"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    errorElement: <ErrorBoundary />,
    children: [
      { index: true, element: <SmartRedirect /> },
      { path: "explorer", element: <ExplorerPage /> },
      { path: "sources", element: <SourcesPage /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "eval", element: <EvalPage /> },
      { path: "themes", element: <ThemesPage /> },
      { path: "reports", element: <ReportsPage /> },
      { path: "reports/:reportId", element: <ReportDetailPage /> },
      { path: "recommendations/:recommendationId", element: <RecommendationDetailPage /> },
      { path: "*", element: <NotFound /> },
    ],
  },
])