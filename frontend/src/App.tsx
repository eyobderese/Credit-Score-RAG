import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom';
import { useAppStore } from './store/appStore';
import { Brain, MessageSquare, FileText, BarChart3, FlaskConical, Settings, Moon, Sun, Menu } from 'lucide-react';
import HomePage from './pages/HomePage';
import QueryPage from './pages/QueryPage';
import DocumentsPage from './pages/DocumentsPage';
import EvaluationPage from './pages/EvaluationPage';
import ExperimentsPage from './pages/ExperimentsPage';
import './App.css';

const navItems = [
  { path: '/', icon: Brain, label: 'Home' },
  { path: '/query', icon: MessageSquare, label: 'Query' },
  { path: '/documents', icon: FileText, label: 'Documents' },
  { path: '/evaluation', icon: BarChart3, label: 'Evaluation' },
  { path: '/experiments', icon: FlaskConical, label: 'Experiments' },
];

function App() {
  const darkMode = useAppStore((state) => state.darkMode);
  const toggleDarkMode = useAppStore((state) => state.toggleDarkMode);
  const sidebarOpen = useAppStore((state) => state.sidebarOpen);
  const toggleSidebar = useAppStore((state) => state.toggleSidebar);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [darkMode]);

  return (
    <BrowserRouter>
      <div className="app">
        <aside className={`sidebar ${!sidebarOpen ? 'collapsed' : ''}`}>
          <div className="sidebar-header">
            <Brain className="logo-icon" size={28} />
            {sidebarOpen && <span className="logo-text gradient-text">Credit RAG</span>}
          </div>
          <nav className="sidebar-nav">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              >
                <item.icon size={20} />
                {sidebarOpen && <span>{item.label}</span>}
              </NavLink>
            ))}
          </nav>
          {sidebarOpen && (
            <div className="sidebar-footer">
              <p>v2.0.0 • AI Course Project</p>
            </div>
          )}
        </aside>

        <div className={`main-content ${!sidebarOpen ? 'sidebar-closed' : ''}`}>
          <header className="header">
            <button className="icon-btn" onClick={toggleSidebar}>
              <Menu size={20} />
            </button>
            <button className="icon-btn" onClick={toggleDarkMode}>
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </header>
          <main className="content">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/query" element={<QueryPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/evaluation" element={<EvaluationPage />} />
              <Route path="/experiments" element={<ExperimentsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
