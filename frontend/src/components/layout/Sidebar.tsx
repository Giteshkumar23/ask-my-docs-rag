import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  FolderOpen,
  BarChart3,
  FlaskConical,
  Settings,
  ChevronLeft,
  BookOpen,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

interface NavItem {
  label: string
  to: string
  icon: React.ComponentType<{ className?: string }>
}

const navItems: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Documents', to: '/dashboard/documents', icon: FileText },
  { label: 'Ask', to: '/dashboard/ask', icon: MessageSquare },
  { label: 'Collections', to: '/dashboard/collections', icon: FolderOpen },
  { label: 'Analytics', to: '/dashboard/analytics', icon: BarChart3 },
  { label: 'Evaluation', to: '/dashboard/evaluation', icon: FlaskConical },
  { label: 'Settings', to: '/dashboard/settings', icon: Settings },
]

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <TooltipProvider delayDuration={0}>
      <aside
        className={cn(
          'flex flex-col h-full bg-card border-r border-border transition-all duration-200 ease-in-out',
          collapsed ? 'w-[60px]' : 'w-[220px]',
        )}
      >
        {/* Logo */}
        <div className={cn(
          'flex items-center h-14 border-b border-border px-3 gap-2 overflow-hidden',
        )}>
          <div className="flex-shrink-0 w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <BookOpen className="h-4 w-4 text-primary-foreground" />
          </div>
          {!collapsed && (
            <span className="font-semibold text-sm text-foreground truncate">Ask My Docs</span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 px-2 space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon
            const link = (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/dashboard'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-md px-2.5 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                    collapsed && 'justify-center px-0',
                  )
                }
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            )

            if (collapsed) {
              return (
                <Tooltip key={item.to}>
                  <TooltipTrigger asChild>{link}</TooltipTrigger>
                  <TooltipContent side="right">{item.label}</TooltipContent>
                </Tooltip>
              )
            }

            return link
          })}
        </nav>

        {/* Collapse toggle */}
        <div className="p-2 border-t border-border">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className={cn(
              'w-full h-8 transition-all duration-200',
              collapsed ? 'justify-center' : 'justify-end px-2',
            )}
          >
            <ChevronLeft
              className={cn(
                'h-4 w-4 transition-transform duration-200',
                collapsed && 'rotate-180',
              )}
            />
          </Button>
        </div>
      </aside>
    </TooltipProvider>
  )
}
