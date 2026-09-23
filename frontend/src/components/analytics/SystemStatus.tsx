import { CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Service {
  name: string
  status: string
}

interface SystemStatusProps {
  services: Record<string, string>
}

function getStatusConfig(status: string) {
  const s = status.toLowerCase()
  if (s === 'healthy' || s === 'ok' || s === 'connected') {
    return { icon: CheckCircle2, color: 'text-green-500', label: 'Healthy' }
  }
  if (s === 'degraded' || s === 'slow') {
    return { icon: AlertCircle, color: 'text-amber-500', label: 'Degraded' }
  }
  if (s === 'loading' || s === 'starting') {
    return { icon: Loader2, color: 'text-blue-500 animate-spin', label: 'Starting' }
  }
  return { icon: XCircle, color: 'text-red-500', label: 'Unhealthy' }
}

export default function SystemStatus({ services }: SystemStatusProps) {
  const serviceList: Service[] = Object.entries(services).map(([name, status]) => ({
    name: name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    status,
  }))

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {serviceList.map((svc) => {
        const config = getStatusConfig(svc.status)
        const Icon = config.icon
        return (
          <div
            key={svc.name}
            className={cn(
              'flex items-center gap-2.5 rounded-lg p-3',
              'border border-border bg-muted/20',
            )}
          >
            <Icon className={cn('h-4 w-4 flex-shrink-0', config.color)} />
            <div className="min-w-0">
              <p className="text-xs font-medium text-foreground truncate">{svc.name}</p>
              <p className={cn('text-xs', config.color)}>{config.label}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
