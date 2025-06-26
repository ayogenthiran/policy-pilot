'use client';

import { useState } from 'react';

interface ChatResponse {
  answer: string;
  sources?: string[];
}

interface UploadResponse {
  fileId: string;
  status: string;
}

interface ErrorResponse {
  error: string;
  message: string;
}

export default function TestPage() {
  const [question, setQuestion] = useState('');
  const [fileId, setFileId] = useState('');
  const [chatResponse, setChatResponse] = useState<ChatResponse | ErrorResponse | null>(null);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | ErrorResponse | null>(null);
  const [loading, setLoading] = useState({ chat: false, upload: false });

  const testChatAPI = async () => {
    setLoading(prev => ({ ...prev, chat: true }));
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
          ...(fileId.trim() && { fileId: fileId.trim() })
        }),
      });

      const data = await response.json();
      setChatResponse(data);
    } catch (error) {
      setChatResponse({
        error: 'NETWORK_ERROR',
        message: 'Failed to connect to API'
      });
    } finally {
      setLoading(prev => ({ ...prev, chat: false }));
    }
  };

  const testUploadAPI = async () => {
    setLoading(prev => ({ ...prev, upload: true }));
    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
      });

      const data = await response.json();
      setUploadResponse(data);
    } catch (error) {
      setUploadResponse({
        error: 'NETWORK_ERROR',
        message: 'Failed to connect to API'
      });
    } finally {
      setLoading(prev => ({ ...prev, upload: false }));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            PolicyPilot API Test Page
          </h1>
          <p className="text-lg text-gray-600">
            Test your API endpoints with this interactive interface
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Chat API Test */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">
              Chat API Test
            </h2>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
                  Question *
                </label>
                <textarea
                  id="question"
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="What is this document about?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
              </div>

              <div>
                <label htmlFor="fileId" className="block text-sm font-medium text-gray-700 mb-2">
                  File ID (optional)
                </label>
                <input
                  id="fileId"
                  type="text"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="doc123"
                  value={fileId}
                  onChange={(e) => setFileId(e.target.value)}
                />
              </div>

              <button
                onClick={testChatAPI}
                disabled={loading.chat || !question.trim()}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading.chat ? 'Testing...' : 'Test Chat API'}
              </button>

              {chatResponse && (
                <div className="mt-4 p-4 bg-gray-100 rounded-md">
                  <h3 className="font-medium text-gray-800 mb-2">Response:</h3>
                  <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                    {JSON.stringify(chatResponse, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>

          {/* Upload API Test */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">
              Upload API Test
            </h2>
            
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                This endpoint simulates file upload scenarios including both success and various failure cases.
                It has a 20% chance of simulating different upload failures for testing purposes.
              </p>

              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                <h4 className="text-sm font-medium text-yellow-800 mb-1">Simulated Failure Types:</h4>
                <ul className="text-xs text-yellow-700 space-y-1">
                                     <li>• File too large (&gt;10MB)</li>
                  <li>• Unsupported file type</li>
                  <li>• Network upload failure</li>
                  <li>• Security threat detected</li>
                </ul>
              </div>

              <button
                onClick={testUploadAPI}
                disabled={loading.upload}
                className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading.upload ? 'Testing Upload...' : 'Test Upload API (Random Success/Failure)'}
              </button>

              {uploadResponse && (
                <div className={`mt-4 p-4 rounded-md ${
                  'error' in uploadResponse 
                    ? 'bg-red-50 border border-red-200' 
                    : 'bg-green-50 border border-green-200'
                }`}>
                  <h3 className={`font-medium mb-2 ${
                    'error' in uploadResponse ? 'text-red-800' : 'text-green-800'
                  }`}>
                    {'error' in uploadResponse ? '❌ Upload Failed' : '✅ Upload Successful'}
                  </h3>
                  <pre className={`text-sm whitespace-pre-wrap ${
                    'error' in uploadResponse ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {JSON.stringify(uploadResponse, null, 2)}
                  </pre>
                  
                  {'error' in uploadResponse && (
                    <div className="mt-2 text-xs text-red-600">
                      <strong>Tip:</strong> In a real app, you would handle this error and show a user-friendly message.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Quick Test Examples */}
        <div className="mt-12 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6">
            Quick Test Examples
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-700 mb-2">Sample Questions:</h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• "What is this document about?"</li>
                <li>• "How do I implement authentication?"</li>
                <li>• "What are the main requirements?"</li>
                <li>• "Explain the security policies"</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-700 mb-2">cURL Commands:</h3>
              <div className="text-sm text-gray-600 space-y-2">
                <div>
                  <strong>Chat API:</strong>
                  <code className="block bg-gray-100 p-2 rounded mt-1 text-xs">
                    curl -X POST http://localhost:3000/api/chat \<br/>
                    -H "Content-Type: application/json" \<br/>
                    -d '{"{"}"question": "Test question"{"}"}'
                  </code>
                </div>
                <div>
                  <strong>Upload API:</strong>
                  <code className="block bg-gray-100 p-2 rounded mt-1 text-xs">
                    curl -X POST http://localhost:3000/api/upload
                  </code>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 