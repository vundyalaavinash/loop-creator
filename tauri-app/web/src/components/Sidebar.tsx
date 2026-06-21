import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/loops", label: "Loops", icon: "⟳" },
  { to: "/new", label: "New Loop", icon: "+" },
  { to: "/files", label: "Files", icon: "◫" },
];

export function Sidebar() {
  return (
    <aside className="w-52 bg-surface border-r border-border-color flex flex-col h-screen flex-shrink-0">
      <div className="px-5 py-4 border-b border-border-color">
        <span className="text-accent-teal font-mono text-sm font-semibold tracking-widest uppercase">
          Loop Creator
        </span>
      </div>
      <nav className="flex-1 py-3">
        {NAV.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-2 text-sm font-mono transition-colors ${
                isActive
                  ? "text-accent-teal bg-elevated border-l-2 border-accent-teal"
                  : "text-muted hover:text-primary hover:bg-elevated"
              }`
            }
          >
            <span className="text-base">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-3 border-t border-border-color">
        <span className="text-xs text-muted font-mono">SP2 v0.1.0</span>
      </div>
    </aside>
  );
}
