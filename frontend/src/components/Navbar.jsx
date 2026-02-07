import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const { dark, toggle } = useTheme();
  const location = useLocation();

  const navLink = (to, label) => {
    const active = location.pathname === to;
    return (
      <Link
        to={to}
        className={`text-sm px-3 py-1 rounded-lg transition ${
          active
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
            : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
        }`}
      >
        {label}
      </Link>
    );
  };

  return (
    <nav className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-5xl mx-auto px-4 py-3 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-xl font-bold text-blue-600 dark:text-blue-400">
            Smart Study Assistant
          </Link>
          {navLink('/', 'Dashboard')}
          {navLink('/stats', 'Statistics')}
          {navLink('/shared', 'Shared')}
          {navLink('/groups', 'Groups')}
          {user?.is_admin && navLink('/admin', 'Admin')}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={toggle}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 transition"
            title={dark ? 'Light mode' : 'Dark mode'}
          >
            {dark ? '\u2600\uFE0F' : '\uD83C\uDF19'}
          </button>
          <button onClick={logout} className="text-gray-500 hover:text-gray-700 dark:text-gray-400 text-sm">
            Sign Out
          </button>
        </div>
      </div>
    </nav>
  );
}
