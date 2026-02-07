import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import DashboardPage from '../pages/DashboardPage';
import api from '../services/api';

// Mock api module
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { token: 'fake-token', is_admin: false },
    logout: vi.fn(),
  }),
}));

// Mock ThemeContext
vi.mock('../contexts/ThemeContext', () => ({
  useTheme: () => ({
    dark: false,
    toggle: vi.fn(),
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

function renderDashboardPage() {
  return render(
    <BrowserRouter>
      <DashboardPage />
    </BrowserRouter>
  );
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    // API calls remain pending (never resolve during this test)
    api.get.mockReturnValue(new Promise(() => {}));

    renderDashboardPage();

    // The page should render the heading and upload section while data loads
    expect(screen.getByText(/upload study material/i)).toBeInTheDocument();
  });

  it('renders uploads after API response', async () => {
    const mockUploads = [
      {
        id: 1,
        filename: 'lecture-notes.pdf',
        file_type: 'pdf',
        file_size: 204800,
        status: 'Completed',
        created_at: '2026-01-15T10:30:00Z',
        course_name: null,
      },
      {
        id: 2,
        filename: 'chapter-summary.docx',
        file_type: 'docx',
        file_size: 51200,
        status: 'Pending',
        created_at: '2026-01-16T14:00:00Z',
        course_name: 'Biology',
      },
    ];

    api.get.mockImplementation((url) => {
      if (url === '/uploads/') {
        return Promise.resolve({ data: mockUploads });
      }
      if (url === '/uploads/courses') {
        return Promise.resolve({ data: [] });
      }
      return Promise.resolve({ data: [] });
    });

    renderDashboardPage();

    await waitFor(() => {
      expect(screen.getByText('lecture-notes.pdf')).toBeInTheDocument();
      expect(screen.getByText('chapter-summary.docx')).toBeInTheDocument();
    });

    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('shows empty state when no uploads', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/uploads/') {
        return Promise.resolve({ data: [] });
      }
      if (url === '/uploads/courses') {
        return Promise.resolve({ data: [] });
      }
      return Promise.resolve({ data: [] });
    });

    renderDashboardPage();

    await waitFor(() => {
      expect(
        screen.getByText(/no uploads yet\. upload a file to get started\./i)
      ).toBeInTheDocument();
    });
  });
});
