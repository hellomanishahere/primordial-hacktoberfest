import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  GitPullRequest,
  ListChecks,
  FileText,
  Radar,
  FlaskConical,
  Settings,
} from 'lucide-react';

const links = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/analyze', label: 'Analyze', icon: FlaskConical },
  { to: '/decisions', label: 'Decisions', icon: ListChecks },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/adrs', label: 'ADR Library', icon: FileText },
  { to: '/radar', label: 'PR Radar', icon: Radar },
  { to: '/settings', label: 'Settings', icon: Settings },
] as const;

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-60 flex-col border-r border-charcoal-700 bg-charcoal-900">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-5 py-5">
        <GitPullRequest className="h-7 w-7 text-accent" />
        <span className="text-lg font-bold tracking-tight text-white">
          Primordial
        </span>
      </div>

      {/* Navigation */}
      <nav className="mt-2 flex flex-1 flex-col gap-0.5 px-3">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-accent/10 text-accent'
                  : 'text-gray-400 hover:bg-charcoal-800 hover:text-gray-200'
              }`
            }
          >
            <Icon className="h-4.5 w-4.5 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-charcoal-700 px-5 py-4">
        <p className="text-xs text-gray-500">
          Decision Intelligence Platform
        </p>
      </div>
    </aside>
  );
}

