import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Navbar from '../components/Navbar';

// Mock AuthContext
const mockLogout = vi.fn();
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { token: 'fake-token', is_admin: false },
    logout: mockLogout,
  }),
}));

// Mock ThemeContext
const mockToggle = vi.fn();
vi.mock('../contexts/ThemeContext', () => ({
  useTheme: () => ({
    dark: false,
    toggle: mockToggle,
  }),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => 'fake-token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

function renderNavbar() {
  return render(
    <BrowserRouter>
      <Navbar />
    </BrowserRouter>
  );
}

describe('Navbar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders app title/brand', () => {
    renderNavbar();

    expect(screen.getByText('Smart Study Assistant')).toBeInTheDocument();
  });

  it('renders navigation links (Dashboard, Statistics, Shared, Groups)', () => {
    renderNavbar();

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Statistics')).toBeInTheDocument();
    expect(screen.getByText('Shared')).toBeInTheDocument();
    expect(screen.getByText('Groups')).toBeInTheDocument();
  });

  it('renders dark mode toggle', () => {
    renderNavbar();

    const toggleButton = screen.getByTitle(/dark mode/i);
    expect(toggleButton).toBeInTheDocument();
  });

  it('renders logout button when logged in', () => {
    renderNavbar();

    const signOutButton = screen.getByText('Sign Out');
    expect(signOutButton).toBeInTheDocument();
  });
});
