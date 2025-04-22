import { useState, useEffect } from 'react';
import './App.css';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import { authApi } from './services/api';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Check if user is already logged in
    const checkLoginStatus = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          // Verify token validity by getting user info
          await authApi.getCurrentUser();
          setIsLoggedIn(true);
        } catch (error) {
          // Token is invalid or expired
          console.error('Invalid token:', error);
          localStorage.removeItem('token');
        }
      }
      setIsLoading(false);
    };

    checkLoginStatus();
  }, []);

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return isLoggedIn ? (
    <Dashboard onLogout={handleLogout} />
  ) : (
    <AuthPage onLoginSuccess={handleLoginSuccess} />
  );
}

export default App;
