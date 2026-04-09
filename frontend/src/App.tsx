import { Link, Outlet, useLocation } from "react-router"
import { cn } from "@/lib/utils"

const navItems = [{ label: "Sources", href: "/sources" }]

export function App() {
  const location = useLocation()

  return (
    <div className="min-h-svh bg-background">
      <header className="border-b border-border">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-8 px-6">
          <Link to="/" className="text-sm font-semibold tracking-tight">
            Feedback Intelligence
          </Link>
          <nav className="flex gap-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-sm transition-colors",
                  location.pathname.startsWith(item.href)
                    ? "bg-secondary text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}

export default App
