import React, { useState } from 'react';
import Button from './Button';

interface NavbarProps {
  username?: string;
  onLogout: () => void;
  onTabChange?: (tab: 'profile' | 'sandboxes' | 'apikey') => void;
  activeTab?: 'profile' | 'sandboxes' | 'apikey';
}

const Navbar: React.FC<NavbarProps> = ({ username, onLogout, onTabChange, activeTab = 'profile' }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="bg-gray-900 shadow-md border-b border-gray-800">
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <img src="/assets/mcp_logo.svg" alt="MCP Logo" className="h-8 w-8 mr-2" />
              <span className="text-blue-400 font-bold text-xl">MCP Sandbox</span>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <button
                onClick={() => onTabChange?.('profile')}
                className={`${activeTab === 'profile' ? 'border-blue-500 text-white' : 'border-transparent text-gray-400 hover:border-gray-600 hover:text-gray-300'} inline-flex items-center px-4 py-2 text-sm font-medium border-b-2`}
              >
                Dashboard
              </button>
              <button
                onClick={() => onTabChange?.('sandboxes')}
                className={`${activeTab === 'sandboxes' ? 'border-blue-500 text-white' : 'border-transparent text-gray-400 hover:border-gray-600 hover:text-gray-300'} inline-flex items-center px-4 py-2 text-sm font-medium border-b-2`}
              >
                Sandboxes
              </button>
              <button
                onClick={() => onTabChange?.('apikey')}
                className={`${activeTab === 'apikey' ? 'border-blue-500 text-white' : 'border-transparent text-gray-400 hover:border-gray-600 hover:text-gray-300'} inline-flex items-center px-4 py-2 text-sm font-medium border-b-2`}
              >
                API Keys
              </button>
            </div>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            {username && (
              <div className="ml-3 relative">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-medium text-gray-300">
                    Welcome, {username}
                  </span>
                  <Button variant="outline" size="sm" onClick={onLogout}>
                    Logout
                  </Button>
                </div>
              </div>
            )}
          </div>
          <div className="-mr-2 flex items-center sm:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              type="button"
              className="bg-white inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              aria-expanded="false"
            >
              <span className="sr-only">Open main menu</span>
              <svg
                className={`${isMenuOpen ? 'hidden' : 'block'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              <svg
                className={`${isMenuOpen ? 'block' : 'hidden'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className={`${isMenuOpen ? 'block' : 'hidden'} sm:hidden`}>
        <div className="pt-2 pb-3 space-y-1">
          <a
            href="#"
            className="bg-blue-50 border-blue-500 text-blue-700 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
          >
            Dashboard
          </a>
          <a
            href="#"
            className="border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
          >
            Sandboxes
          </a>
          <a
            href="#"
            className="border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800 block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
          >
            API Keys
          </a>
        </div>
        {username && (
          <div className="pt-4 pb-3 border-t border-gray-200">
            <div className="flex items-center px-4">
              <div className="flex-shrink-0">
                <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold">
                  {username.charAt(0).toUpperCase()}
                </div>
              </div>
              <div className="ml-3">
                <div className="text-base font-medium text-gray-800">
                  {username}
                </div>
              </div>
            </div>
            <div className="mt-3 space-y-1">
              <button
                onClick={onLogout}
                className="block w-full text-left px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
              >
                Sign out
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
