import { Link, useLocation } from "react-router"
import { HugeiconsIcon } from "@hugeicons/react"
import { AnimatePresence, motion } from "motion/react"
import { useSidebar } from "@/components/ui/sidebar"
import {
  DashboardCircleIcon,
  Compass01Icon,
  Tag01Icon,
  File01Icon,
  TestTube01Icon,
  DatabaseIcon,
} from "@hugeicons/core-free-icons"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar"

const primaryNav = [
  { label: "Dashboard", href: "/dashboard", icon: DashboardCircleIcon },
  { label: "Explorer", href: "/explorer", icon: Compass01Icon },
  { label: "Themes", href: "/themes", icon: Tag01Icon },
  { label: "Reports", href: "/reports", icon: File01Icon },
] as const

const manageNav = [
  { label: "Eval", href: "/eval", icon: TestTube01Icon },
  { label: "Sources", href: "/sources", icon: DatabaseIcon },
] as const

function SidebarLogo() {
  const { state } = useSidebar()
  const collapsed = state === "collapsed"

  return (
    <Link to="/" className="flex items-center gap-2 h-7" aria-label="Home">
      <AnimatePresence mode="wait" initial={false}>
        {collapsed ? (
          <motion.img
            key="icon"
            src="/spectra-icon.png"
            alt="Spectra"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.15, ease: [0.23, 1, 0.32, 1] }}
            className="size-7 shrink-0 object-contain"
          />
        ) : (
          <motion.img
            key="full"
            src="/spectra-full.png"
            alt="Spectra"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15, ease: [0.23, 1, 0.32, 1] }}
            className="h-6 shrink-0 object-contain"
          />
        )}
      </AnimatePresence>
    </Link>
  )
}

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation()

  const isActive = (href: string) =>
    location.pathname === href ||
    (href !== "/" && location.pathname.startsWith(href + "/"))

  return (
    <Sidebar variant="sidebar" collapsible="icon" {...props}>
      <SidebarHeader className="px-4 pt-6 pb-0">
        <SidebarLogo />
      </SidebarHeader>

      <SidebarContent className="px-2 pt-4">
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {primaryNav.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    render={<Link to={item.href} />}
                    isActive={isActive(item.href)}
                    tooltip={item.label}
                  >
                    <HugeiconsIcon icon={item.icon} strokeWidth={2} className="size-4" />
                    <span>{item.label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator />

        <SidebarGroup>
          <SidebarGroupLabel>Manage</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {manageNav.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton
                    render={<Link to={item.href} />}
                    isActive={isActive(item.href)}
                    tooltip={item.label}
                  >
                    <HugeiconsIcon icon={item.icon} strokeWidth={2} className="size-4" />
                    <span>{item.label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarRail />
    </Sidebar>
  )
}