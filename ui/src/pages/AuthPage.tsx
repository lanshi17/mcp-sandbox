import React, { useState } from 'react';
import { authApi, LoginCredentials, RegisterCredentials } from '../services/api';
import Button from '../components/Button';
import { Card, CardContent } from '../components/Card';

interface AuthPageProps {
  onLoginSuccess: (token: string) => void;
}

const AuthPage: React.FC<AuthPageProps> = ({ onLoginSuccess }) => {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Frontend validation errors
  const [usernameError, setUsernameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const credentials: LoginCredentials = { username, password };
      const response = await authApi.login(credentials);
      localStorage.setItem('token', response.access_token);
      onLoginSuccess(response.access_token);
    } catch (error) {
      console.error('Login error:', error);
      setError('Invalid username or password');
    } finally {
      setIsLoading(false);
    }
  };

  // Validate form fields
  const validateForm = () => {
    let isValid = true;
    
    // Reset all errors
    setUsernameError('');
    setEmailError('');
    setPasswordError('');
    setConfirmPasswordError('');
    setError('');
    
    // Username validation
    if (!username.trim()) {
      setUsernameError('Username is required');
      isValid = false;
    } else if (username.length < 3) {
      setUsernameError('Username must be at least 3 characters');
      isValid = false;
    }
    
    // Email validation
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!email.trim()) {
      setEmailError('Email is required');
      isValid = false;
    } else if (!emailRegex.test(email)) {
      setEmailError('Please enter a valid email address');
      isValid = false;
    }
    
    // Password validation
    if (!password) {
      setPasswordError('Password is required');
      isValid = false;
    } else if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      isValid = false;
    }
    
    // Confirm password validation
    if (!confirmPassword) {
      setConfirmPasswordError('Please confirm your password');
      isValid = false;
    } else if (password !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match');
      isValid = false;
    }
    
    return isValid;
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form before submission
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);

    try {
      const credentials: RegisterCredentials = { username, email, password };
      await authApi.register(credentials);
      
      // Auto-login after successful registration
      const loginCredentials: LoginCredentials = { username, password };
      const response = await authApi.login(loginCredentials);
      localStorage.setItem('token', response.access_token);
      onLoginSuccess(response.access_token);
    } catch (error: any) {
      console.error('Registration error:', error);
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else if (error.response?.status === 422) {
        setError('Validation error. Please check all fields are correctly formatted.');
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <img src="/assets/mcp_logo.svg" alt="MCP Logo" className="h-20 w-20" />
          </div>
          <h1 className="text-3xl font-extrabold text-white">MCP Sandbox</h1>
          <p className="mt-2 text-sm text-gray-400">
            {isRegistering ? 'Create a new account' : 'Sign in to your account'}
          </p>
        </div>

        <Card className="bg-gray-800 border border-black shadow-xl">

          <CardContent className="text-gray-300">
            {error && (
              <div className="mb-4 bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded">
                {error}
              </div>
            )}

            {isRegistering ? (
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <label htmlFor="register-username" className="block text-sm font-medium text-gray-300">
                    Username
                  </label>
                  <input
                    id="register-username"
                    name="username"
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className={`mt-1 block w-full px-3 py-2 bg-gray-700 border ${usernameError ? 'border-red-500' : 'border-gray-600'} text-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
                  />
                  {usernameError && (
                    <p className="mt-1 text-sm text-red-500">{usernameError}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="register-email" className="block text-sm font-medium text-gray-300">
                    Email
                  </label>
                  <input
                    id="register-email"
                    name="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`mt-1 block w-full px-3 py-2 bg-gray-700 border ${emailError ? 'border-red-500' : 'border-gray-600'} text-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
                  />
                  {emailError && (
                    <p className="mt-1 text-sm text-red-500">{emailError}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="register-password" className="block text-sm font-medium text-gray-300">
                    Password
                  </label>
                  <input
                    id="register-password"
                    name="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={`mt-1 block w-full px-3 py-2 bg-gray-700 border ${passwordError ? 'border-red-500' : 'border-gray-600'} text-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
                  />
                  {passwordError && (
                    <p className="mt-1 text-sm text-red-500">{passwordError}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="register-confirm-password" className="block text-sm font-medium text-gray-300">
                    Confirm Password
                  </label>
                  <input
                    id="register-confirm-password"
                    name="confirmPassword"
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`mt-1 block w-full px-3 py-2 bg-gray-700 border ${confirmPasswordError ? 'border-red-500' : 'border-gray-600'} text-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm`}
                  />
                  {confirmPasswordError && (
                    <p className="mt-1 text-sm text-red-500">{confirmPasswordError}</p>
                  )}
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  className="w-full"
                  isLoading={isLoading}
                >
                  Register
                </Button>
                
                <div className="text-center mt-4">
                  <button
                    type="button"
                    className="text-blue-400 hover:text-blue-300 text-sm"
                    onClick={() => setIsRegistering(false)}
                  >
                    Already have an account? Sign in
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label htmlFor="login-username" className="block text-sm font-medium text-gray-300">
                    Username
                  </label>
                  <input
                    id="login-username"
                    name="username"
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label htmlFor="login-password" className="block text-sm font-medium text-gray-300">
                    Password
                  </label>
                  <input
                    id="login-password"
                    name="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  className="w-full"
                  isLoading={isLoading}
                >
                  Sign in
                </Button>
                
                <div className="text-center mt-4">
                  <button
                    type="button"
                    className="text-blue-400 hover:text-blue-300 text-sm"
                    onClick={() => setIsRegistering(true)}
                  >
                    Don't have an account? Register
                  </button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AuthPage;
