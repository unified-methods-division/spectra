import { Link, useLocation } from "react-router"
import { HugeiconsIcon } from "@hugeicons/react"
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

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation()

  const isActive = (href: string) =>
    location.pathname === href ||
    (href !== "/" && location.pathname.startsWith(href + "/"))

  return (
    <Sidebar variant="sidebar" collapsible="icon" {...props}>
      <SidebarHeader className="px-4 pt-6 pb-0">
        <Link
          to="/"
          className="flex items-center gap-2"
          aria-label="Home"
        >
          <span className="text-lg leading-none group-data-[collapsible=icon]:text-xl">&#x1f4ca;</span>
          <span className="text-[15px] font-semibold tracking-tight text-sidebar-foreground group-data-[collapsible=icon]:hidden">
            Intelligence
          </span>
        </Link>
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