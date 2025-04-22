import React from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './Card';
import Button from './Button';

interface SandboxProps {
  id: string;
  name: string;
  createdAt: string;
  onSelect: (id: string) => void;
  onDelete?: (id: string) => void;
  status?: 'running' | 'stopped' | 'error';
}

const SandboxCard: React.FC<SandboxProps> = ({ id, name, createdAt, onSelect, onDelete, status = 'running' }) => {
  const formattedDate = new Date(createdAt).toLocaleDateString();
  const formattedTime = new Date(createdAt).toLocaleTimeString();
  
  // Handle delete with confirmation
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering card selection
    if (onDelete && window.confirm(`Are you sure you want to delete sandbox "${name}"? This action cannot be undone.`)) {
      onDelete(id);
    }
  };
  
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-start justify-between">
          <span className="truncate">{name}</span>
          {status === 'running' && (
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-100 text-xs text-green-600" title="Running">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
            </span>
          )}
          {status === 'stopped' && (
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 text-xs text-gray-600" title="Stopped">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="6" y="6" width="12" height="12"></rect>
              </svg>
            </span>
          )}
          {status === 'error' && (
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 text-xs text-red-600" title="Error">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-gray-500">
          <div className="mt-2 flex items-center">
            <svg className="mr-1 h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"></path>
            </svg>
            <span className="text-xs font-medium text-gray-400">ID:</span>
            <span className="text-xs ml-1 text-gray-300">{id}</span>
          </div>
          
          <div className="mt-3 flex items-center">
            <svg className="mr-1 h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <span className="text-xs font-medium text-gray-400">Created:</span>
            <span className="text-xs ml-1 text-gray-300">{formattedDate} at {formattedTime}</span>
          </div>
          
          <div className="mt-3 flex items-center">
            <svg className="mr-1 h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 12m-10 0a10 10 0 1 0 20 0a10 10 0 1 0-20 0"></path>
              <path d="M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0-6 0"></path>
            </svg>
            <span className="text-xs font-medium text-gray-400">Status:</span>
            <span className={`text-xs ml-1 ${status === 'running' ? 'text-green-400' : status === 'error' ? 'text-red-400' : 'text-gray-400'}`}>
              {status === 'running' ? 'Running' : status === 'stopped' ? 'Stopped' : 'Error'}
            </span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="pt-0 flex flex-col gap-2">
        <Button 
          variant="primary" 
          className="w-full" 
          onClick={() => onSelect(id)}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 11 12 14 22 4"></polyline>
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
          </svg>
          Select Sandbox
        </Button>
        
        {onDelete && (
          <Button 
            variant="danger" 
            className="w-full" 
            onClick={handleDelete}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18"></path>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
              <line x1="10" y1="11" x2="10" y2="17"></line>
              <line x1="14" y1="11" x2="14" y2="17"></line>
            </svg>
            Delete Sandbox
          </Button>
        )}
      </CardFooter>
    </Card>
  );
};

export default SandboxCard;
