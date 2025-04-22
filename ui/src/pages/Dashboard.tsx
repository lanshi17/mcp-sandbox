import React, { useState, useEffect } from 'react';
import { User, Sandbox, authApi, sandboxApi } from '../services/api';
import Navbar from '../components/Navbar';
import Button from '../components/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/Card';
import SandboxCard from '../components/SandboxCard';

interface DashboardProps {
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [user, setUser] = useState<User | null>(null);
  const [apiKey, setApiKey] = useState<string>('');
  const [sseUrl, setSseUrl] = useState<string>('');
  const [sandboxes, setSandboxes] = useState<Sandbox[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegeneratingKey, setIsRegeneratingKey] = useState(false);
  const [isDeletingSandbox, setIsDeletingSandbox] = useState(false);
  const [deletingId, setDeletingId] = useState<string>('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [activeTab, setActiveTab] = useState<'profile' | 'sandboxes' | 'apikey'>('profile');

  // Function to fetch only sandboxes - useful for refreshing after operations
  const fetchSandboxes = async () => {
    try {
      setError('');
      // Fetch user's sandboxes
      const userSandboxes = await sandboxApi.getUserSandboxes();
      setSandboxes(userSandboxes || []);
      return true;
    } catch (err) {
      console.error('Error fetching sandboxes:', err);
      setError('Failed to load sandbox data. Please try again later.');
      return false;
    }
  };

  // Setup periodic sandbox refreshing to detect changes made by MCP tools
  useEffect(() => {
    let interval: number;
    
    // Only set up the refresh interval when the sandboxes tab is active
    if (activeTab === 'sandboxes') {
      // Refresh every 5 seconds when the sandboxes tab is active
      interval = window.setInterval(() => {
        fetchSandboxes();
      }, 5000); // 5 seconds polling interval
    }
    
    // Cleanup the interval when the component unmounts or tab changes
    return () => {
      if (interval) {
        window.clearInterval(interval);
      }
    };
  }, [activeTab]); // Re-run when activeTab changes

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setIsLoading(true);
        setError('');
        
        // Fetch user profile
        const userData = await authApi.getCurrentUser();
        setUser(userData);
        
        // Fetch API key
        const apiKeyData = await authApi.getApiKey();
        setApiKey(apiKeyData.api_key);
        setSseUrl(sandboxApi.getSseUrl(apiKeyData.api_key));
        
        // Fetch user's sandboxes
        await fetchSandboxes();
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError('Failed to load user data. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const handleRegenerateApiKey = async () => {
    try {
      setIsRegeneratingKey(true);
      const result = await authApi.regenerateApiKey();
      setApiKey(result.api_key);
      setSseUrl(sandboxApi.getSseUrl(result.api_key));
    } catch (err) {
      console.error('Error regenerating API key:', err);
      setError('Failed to regenerate API key. Please try again.');
    } finally {
      setIsRegeneratingKey(false);
    }
  };

  const handleSelectSandbox = (sandboxId: string) => {
    // In a real application, this would navigate to the sandbox page
    console.log(`Selected sandbox: ${sandboxId}`);
  };

  const handleDeleteSandbox = async (sandboxId: string) => {
    try {
      setIsDeletingSandbox(true);
      setDeletingId(sandboxId);
      setError('');
      
      // Call the API to delete the sandbox
      await sandboxApi.deleteSandbox(sandboxId);
      
      // Update the local state by removing the deleted sandbox
      setSandboxes(prevSandboxes => prevSandboxes.filter(sandbox => sandbox.id !== sandboxId));
      
      // Show success message
      setSuccessMessage('Sandbox deleted successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccessMessage('');
      }, 3000);
    } catch (err) {
      console.error('Error deleting sandbox:', err);
      setError('Failed to delete sandbox. Please try again.');
    } finally {
      setIsDeletingSandbox(false);
      setDeletingId('');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Navbar 
          username={user?.username} 
          onLogout={onLogout} 
        />
        <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-400"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen h-screen w-full bg-gray-900 flex flex-col overflow-hidden">
      <Navbar 
        username={user?.username} 
        onLogout={onLogout} 
        onTabChange={setActiveTab}
        activeTab={activeTab}
      />

      <main className="flex-1 w-full py-6 px-4 sm:px-6 lg:px-8 text-gray-200 flex flex-col h-[calc(100vh-4rem)] overflow-y-auto">
        {error && (
          <div className="mb-4 bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded relative">
            {error}
          </div>
        )}
        
        {successMessage && (
          <div className="mb-4 bg-green-900/50 border border-green-700 text-green-200 px-4 py-3 rounded relative">
            {successMessage}
          </div>
        )}

        {/* Mobile-only tabs selector */}
        <div className="sm:hidden mb-6">
          <select
            id="tabs"
            name="tabs"
            className="block w-full rounded-md bg-gray-800 text-white border-gray-700 focus:border-blue-500 focus:ring-blue-500"
            value={activeTab}
            onChange={(e) => setActiveTab(e.target.value as any)}
          >
            <option value="profile">Profile</option>
            <option value="sandboxes">Sandboxes</option>
            <option value="apikey">API Key</option>
          </select>
        </div>

        <div className="flex-1 flex h-full w-full">
        {activeTab === 'profile' && user && (
          <Card className="w-full flex-1">
            <CardHeader>
              <CardTitle>User Profile</CardTitle>
              <CardDescription>Your account information</CardDescription>
            </CardHeader>
            <CardContent className="h-full overflow-auto">
              <div className="space-y-4">
                <div className="flex items-center">
                  <div className="h-12 w-12 rounded-full bg-blue-900 flex items-center justify-center">
                    <span className="text-blue-300 font-bold text-lg">
                      {user.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-white">{user.username}</h3>
                    <p className="text-sm text-gray-400">{user.email}</p>
                  </div>
                </div>

                <div className="border-t border-gray-700 pt-4">
                  <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                    <div className="sm:col-span-1">
                      <dt className="text-sm font-medium text-gray-400">User ID</dt>
                      <dd className="mt-1 text-sm text-gray-200">{user.id}</dd>
                    </div>
                    <div className="sm:col-span-1">
                      <dt className="text-sm font-medium text-gray-400">Account Created</dt>
                      <dd className="mt-1 text-sm text-gray-200">
                        {new Date(user.created_at).toLocaleDateString()}
                      </dd>
                    </div>
                    <div className="sm:col-span-1">
                      <dt className="text-sm font-medium text-gray-400">Status</dt>
                      <dd className="mt-1 text-sm text-gray-200">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-900 text-green-300">
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </dd>
                    </div>
                    <div className="sm:col-span-1">
                      <dt className="text-sm font-medium text-gray-400">Sandboxes</dt>
                      <dd className="mt-1 text-sm text-gray-200">{sandboxes.length}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === 'sandboxes' && (
          <div className="flex flex-col flex-1 w-full h-[32rem] max-h-[80vh] min-h-[24rem] overflow-y-auto">
            <div className="mb-6 flex justify-between items-center">
              <h2 className="text-lg font-medium text-white">Your Sandboxes</h2>
              <Button onClick={fetchSandboxes} variant="outline" size="sm">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                </svg>
                Refresh
              </Button>
            </div>

            <div className="flex-1 w-full">
              {sandboxes.length === 0 ? (
                <Card className="bg-gray-800 border border-gray-700 shadow-md rounded-lg overflow-hidden w-full">
                  <CardContent className="p-6 h-full flex items-center justify-center">
                    <div className="text-center py-10">
                      <svg
                        className="mx-auto h-12 w-12 text-gray-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                        ></path>
                      </svg>
                      <h3 className="mt-2 text-sm font-medium text-gray-200">No sandboxes available</h3>
                      <p className="mt-1 text-sm text-gray-400">
                        You don't have any sandboxes yet.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 pb-4">
                  {sandboxes.map((sandbox) => (
                    <SandboxCard
                      key={sandbox.id}
                      id={sandbox.id}
                      name={sandbox.name}
                      createdAt={sandbox.created_at}
                      status={isDeletingSandbox && sandbox.id === deletingId ? 'stopped' : 'running'}
                      onSelect={handleSelectSandbox}
                      onDelete={!isDeletingSandbox ? handleDeleteSandbox : undefined}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'apikey' && (
          <Card className="w-full flex-1">
            <CardHeader>
              <CardTitle>API Key Management</CardTitle>
              <CardDescription>
                Your API key is used to authenticate API requests and SSE connections
              </CardDescription>
            </CardHeader>
            <CardContent className="h-full overflow-auto">
              <div className="space-y-4">
                <div className="flex flex-col items-center justify-center">
                  <label className="block text-sm font-medium text-gray-300">Your API Key</label>
                  <div className="mt-1 flex rounded-md shadow-sm w-full max-w-xl justify-center">
                    <div className="relative flex items-stretch flex-grow">
                      <input
                        type="text"
                        value={apiKey}
                        readOnly
                        className="focus:ring-blue-500 focus:border-blue-500 block w-full rounded-md border-gray-700 bg-gray-800 text-gray-200 pr-10 sm:text-sm text-center"
                      />
                    </div>
                  </div>
                </div>
                <div className="flex flex-col items-center justify-center">
                  <label className="block text-sm font-medium text-gray-300">SSE URL</label>
                  <div className="mt-1 flex rounded-md shadow-sm w-full max-w-xl justify-center">
                    <div className="relative flex items-stretch flex-grow">
                      <input
                        type="text"
                        value={sseUrl}
                        readOnly
                        className="focus:ring-blue-500 focus:border-blue-500 block w-full rounded-md border-gray-700 bg-gray-800 text-gray-200 pr-10 sm:text-sm text-center"
                      />
                    </div>
                  </div>
                  <p className="mt-2 text-sm text-gray-400 text-center">
                    Use this URL to connect to the SSE endpoint.
                  </p>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button
                variant="outline"
                onClick={handleRegenerateApiKey}
                isLoading={isRegeneratingKey}
              >
                <svg
                  className="-ml-1 mr-2 h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z"
                    clipRule="evenodd"
                  />
                </svg>
                Regenerate API Key
              </Button>
              <div className="ml-4 text-sm text-gray-500">
                <strong>Warning:</strong> Regenerating your API key will invalidate your existing key.
              </div>
            </CardFooter>
          </Card>
        )}
        </div>
      </main>

    </div>
  );
};

export default Dashboard;
