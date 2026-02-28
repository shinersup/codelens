import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import { Terminal, History, LogOut, Scan } from 'lucide-react';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 border-b border-surface-5 bg-surface-0/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="relative">
              <Terminal
                size={20}
                className="text-accent-cyan group-hover:drop-shadow-[0_0_8px_rgba(0,229,255,0.5)] transition-all"
              />
            </div>
            <span className="font-display font-bold text-base tracking-tight text-txt-primary">
              code<span className="text-accent-cyan">lens</span>
            </span>
            <span className="hidden sm:inline text-[10px] font-mono text-txt-muted tracking-widest uppercase ml-1">
              v1.0
            </span>
          </Link>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            {isAuthenticated ? (
              <>
                <Link
                  to="/analyze"
                  className={`btn-ghost ${isActive('/analyze') ? 'text-accent-cyan bg-surface-3' : ''}`}
                >
                  <Scan size={15} />
                  <span className="hidden sm:inline">Analyze</span>
                </Link>
                <Link
                  to="/history"
                  className={`btn-ghost ${isActive('/history') ? 'text-accent-cyan bg-surface-3' : ''}`}
                >
                  <History size={15} />
                  <span className="hidden sm:inline">History</span>
                </Link>
                <div className="w-px h-5 bg-surface-5 mx-2" />
                <span className="text-xs font-mono text-txt-muted hidden sm:inline mr-2">
                  {user?.email}
                </span>
                <button onClick={logout} className="btn-ghost text-txt-muted hover:text-accent-red">
                  <LogOut size={15} />
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className={`btn-ghost ${isActive('/login') ? 'text-accent-cyan' : ''}`}
                >
                  Login
                </Link>
                <Link to="/register" className="btn-primary text-xs py-2 px-4">
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
