import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LogOut, Layers, DollarSign, ShieldCheck } from 'lucide-react';
import { getAuthToken, removeAuthToken } from '../api/client';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const token = getAuthToken();

  const handleLogout = () => {
    removeAuthToken();
    navigate('/login');
  };

  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800 bg-slate-900/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link to="/roles" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-6 h-6 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-heading font-bold text-xl tracking-tight text-white">Candidate<span className="text-emerald-400">Lens</span></span>
              <span className="text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">POC</span>
            </div>
            <p className="text-xs text-slate-400 -mt-0.5 hidden sm:block">Assess for readiness</p>
          </div>
        </Link>

        {token && (
          <nav className="flex items-center space-x-1 sm:space-x-4">
            <Link
              to="/roles"
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive('/roles')
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Roles</span>
            </Link>

            <Link
              to="/costs"
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive('/costs')
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <DollarSign className="w-4 h-4" />
              <span>Admin Costs</span>
            </Link>

            <div className="h-5 w-px bg-slate-800 mx-2" />

            <button
              onClick={handleLogout}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </nav>
        )}
      </div>
    </header>
  );
};
