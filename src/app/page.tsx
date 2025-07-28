"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Upload, MessageCircle, X, CheckCircle, AlertCircle, Send } from "lucide-react"
import { useAuth } from '@/components/auth/AuthProvider'
import { useRouter } from 'next/navigation'

interface ChatMessage {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
  sources?: string[]
}

export default function HomePage() {
  const { user, loading, signOut } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth/login')
    }
    // If user is authenticated, stay on the main page with upload/chat functionality
  }, [user, loading, router])

  const [activeTab, setActiveTab] = useState("upload")
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [messageType, setMessageType] = useState<"success" | "error">("success")
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      content: "Hello! How can I help you today?",
      role: "assistant",
      timestamp: new Date(),
    },
  ])
  const [chatInput, setChatInput] = useState("")
  const [isSendingMessage, setIsSendingMessage] = useState(false)
  const [chatError, setChatError] = useState<string | null>(null)

  const navigationItems = [
    {
      key: "upload",
      label: "Upload",
      icon: Upload,
    },
    {
      key: "chat",
      label: "Chat",
      icon: MessageCircle,
    },
  ]

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type on frontend as well
    if (file.type !== "application/pdf") {
      setUploadMessage("Only PDF files are supported")
      setMessageType("error")
      return
    }

    setIsUploading(true)
    setUploadMessage(null)

    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      })

      const result = await response.json()

      if (response.ok) {
        setUploadMessage(result.message)
        setMessageType("success")
      } else {
        setUploadMessage(result.message || "Upload failed")
        setMessageType("error")
      }
    } catch (error) {
      setUploadMessage("Network error occurred while uploading")
      setMessageType("error")
    } finally {
      setIsUploading(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  const closeMessage = () => {
    setUploadMessage(null)
  }

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!chatInput.trim() || isSendingMessage) return

    const userMessage = chatInput.trim()
    setChatInput("")
    setChatError(null)

    // Add user message to chat
    const newUserMessage: ChatMessage = {
      id: Date.now().toString(),
      content: userMessage,
      role: "user",
      timestamp: new Date(),
    }

    setChatMessages((prev) => [...prev, newUserMessage])
    setIsSendingMessage(true)

    try {
      console.log('Sending chat request:', { message: userMessage })
      
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage }),
      })

      console.log('Chat response status:', response.status)
      const result = await response.json()
      console.log('Chat response result:', result)

      if (response.ok) {
        // Add assistant response to chat
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          content: result.answer || result.message, // Support both new and old format
          role: "assistant",
          timestamp: new Date(),
          sources: result.sources, // Include sources if available
        }
        setChatMessages((prev) => [...prev, assistantMessage])
      } else {
        console.error('Chat API error:', result)
        setChatError(result.message || "Failed to send message")
      }
    } catch (error) {
      console.error('Network error:', error)
      setChatError("Network error occurred while sending message")
    } finally {
      setIsSendingMessage(false)
    }
  }

  const closeChatError = () => {
    setChatError(null)
  }

  const renderContent = () => {
    switch (activeTab) {
      case "upload":
        return (
          <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-lg shadow-md">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Upload Files</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center hover:border-gray-400 dark:hover:border-gray-500 transition-colors">
                  <Upload className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
                  <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Drop PDF files here or click to upload
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                    Only PDF files are supported • Maximum 10MB
                  </p>
                  <button
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={handleFileSelect}
                    disabled={isUploading}
                  >
                    {isUploading ? "Uploading..." : "Choose PDF File"}
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>

                {/* Message Display */}
                {uploadMessage && (
                  <div
                    className={`p-4 rounded-lg border ${
                      messageType === "success"
                        ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
                        : "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        {messageType === "success" ? (
                          <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
                        ) : (
                          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                        )}
                        <p
                          className={`text-sm ${
                            messageType === "success"
                              ? "text-green-800 dark:text-green-200"
                              : "text-red-800 dark:text-red-200"
                          }`}
                        >
                          {uploadMessage}
                        </p>
                      </div>
                      <button
                        onClick={closeMessage}
                        className={`p-1 rounded-md hover:bg-opacity-20 ${
                          messageType === "success"
                            ? "text-green-600 dark:text-green-400 hover:bg-green-600"
                            : "text-red-600 dark:text-red-400 hover:bg-red-600"
                        }`}
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      case "chat":
        return (
          <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-lg shadow-md">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Chat Interface</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {/* Chat Messages */}
                <div className="h-96 border rounded-lg p-4 bg-gray-50 dark:bg-gray-800 dark:border-gray-600 overflow-y-auto">
                  <div className="space-y-3">
                    {chatMessages.map((message) => (
                      <div
                        key={message.id}
                        className={`p-3 rounded-lg max-w-xs ${
                          message.role === "assistant"
                            ? "bg-blue-100 dark:bg-blue-900"
                            : "bg-white dark:bg-gray-700 ml-auto shadow-sm"
                        }`}
                      >
                        <p className="text-sm text-gray-800 dark:text-gray-200">{message.content}</p>
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
                            <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Sources:</p>
                            <div className="space-y-1">
                              {message.sources.map((source, index) => (
                                <p key={index} className="text-xs text-blue-600 dark:text-blue-400">
                                  • {source}
                                </p>
                              ))}
                            </div>
                          </div>
                        )}
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {message.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    ))}
                    {isSendingMessage && (
                      <div className="bg-blue-100 dark:bg-blue-900 p-3 rounded-lg max-w-xs">
                        <p className="text-sm text-gray-800 dark:text-gray-200">Thinking...</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Chat Error Display */}
                {chatError && (
                  <div className="p-3 rounded-lg border bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 mt-0.5" />
                        <p className="text-sm text-red-800 dark:text-red-200">{chatError}</p>
                      </div>
                      <button
                        onClick={closeChatError}
                        className="p-1 rounded-md text-red-600 dark:text-red-400 hover:bg-red-600 hover:bg-opacity-20"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Chat Input */}
                <form onSubmit={handleChatSubmit} className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Type your message..."
                    disabled={isSendingMessage}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={!chatInput.trim() || isSendingMessage}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <Send className="h-4 w-4" />
                    {isSendingMessage ? "Sending..." : "Send"}
                  </button>
                </form>
              </div>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  // Show loading while determining auth state
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
        
        <style jsx>{`
          .loading-container {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }

          .loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
          }

          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }

          p {
            color: white;
            font-size: 16px;
          }
        `}</style>
      </div>
    )
  }

  // Main app UI for authenticated users
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Navigation Header */}
      <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container mx-auto px-4 py-3">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                Policy Pilot
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => signOut()}
                className="bg-red-500 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-600 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Upload & Chat
            </h2>
            <p className="text-gray-600 dark:text-gray-300">
              Upload documents and chat with AI assistance
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex justify-center mb-8">
            <div className="flex bg-white dark:bg-gray-800 rounded-lg shadow-sm p-1">
              {navigationItems.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.key}
                    onClick={() => setActiveTab(item.key)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === item.key
                        ? "bg-blue-600 text-white"
                        : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Content Area */}
          <div className="flex justify-center">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  )
}
