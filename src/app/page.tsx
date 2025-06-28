"use client"

import { useState } from "react"
import { Upload, MessageCircle } from "lucide-react"

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("upload")

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

  const renderContent = () => {
    switch (activeTab) {
      case "upload":
        return (
          <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-lg shadow-md">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200">Upload Files</h2>
            </div>
            <div className="p-6">
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center hover:border-gray-400 dark:hover:border-gray-500 transition-colors">
                <Upload className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
                <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  Drop files here or click to upload
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Support for various file formats</p>
                <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
                  Choose Files
                </button>
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
                <div className="h-96 border rounded-lg p-4 bg-gray-50 dark:bg-gray-800 dark:border-gray-600 overflow-y-auto">
                  <div className="space-y-3">
                    <div className="bg-blue-100 dark:bg-blue-900 p-3 rounded-lg max-w-xs">
                      <p className="text-sm text-gray-800 dark:text-gray-200">Hello! How can I help you today?</p>
                    </div>
                    <div className="bg-white dark:bg-gray-700 p-3 rounded-lg max-w-xs ml-auto shadow-sm">
                      <p className="text-sm text-gray-800 dark:text-gray-200">
                        Hi there! I'm looking for some assistance.
                      </p>
                    </div>
                    <div className="bg-blue-100 dark:bg-blue-900 p-3 rounded-lg max-w-xs">
                      <p className="text-sm text-gray-800 dark:text-gray-200">
                        I'd be happy to help! What do you need assistance with?
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Type your message..."
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
                    Send
                  </button>
                </div>
              </div>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Vertical Navigation Sidebar */}
      <div className="w-64 bg-white dark:bg-gray-900 shadow-lg">
        <div className="p-6">
          <h1 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-8">My App</h1>
          <nav className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.key}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-md text-left transition-colors ${
                    activeTab === item.key
                      ? "bg-blue-600 text-white"
                      : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                  }`}
                  onClick={() => setActiveTab(item.key)}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-8 dark:bg-gray-600">
        <div className="flex items-center justify-center h-full">{renderContent()}</div>
      </div>
    </div>
  )
}
