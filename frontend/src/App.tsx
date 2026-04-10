import { Link, Outlet, useLocation } from "react-router"
import { cn } from "@/lib/utils"

const navItems = [
  { label: "Sources", href: "/sources" },
  { label: "Explorer", href: "/explorer" },
  { label: "Dashboard", href: "/dashboard" },
  { label: "Themes", href: "/themes" },
]

export function App() {
  const location = useLocation()

  return (
    <div className="flex min-h-svh bg-background">
      <aside className="sticky top-0 flex h-svh w-[220px] shrink-0 flex-col px-8 pt-7 pb-5">
        <Link to="/" className="group mb-12 flex flex-col">
          <span className="text-[10px] font-medium tracking-[0.2em] text-muted-foreground/50 uppercase">
            Feedback
          </span>
          <span className="text-[15px] font-medium tracking-tight text-foreground">
            Intelligence
          </span>
        </Link>

        <nav className="flex flex-col gap-1">
          {navItems.map((item) => {
            const active = location.pathname.startsWith(item.href)
            return (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  "flex items-center gap-2 py-1 text-[13px] transition-colors duration-150",
                  active
                    ? "font-medium text-foreground"
                    : "text-muted-foreground/60 hover:text-muted-foreground",
                )}
              >
                <span className={cn(
                  "text-sm font-mono",
                  active ? "text-primary" : "text-muted-foreground/30",
                )}>
                  +
                </span>
                {item.label}
              </Link>
            )
          })}
        </nav>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}

export default App
