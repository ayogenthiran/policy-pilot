"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Upload, MessageCircle, BarChart3, X, CheckCircle, AlertCircle, Send, LogOut, FileText } from "lucide-react"
import { useAuth } from "@/components/auth/AuthProvider"
import { useRouter } from "next/navigation"
import ThemeToggle from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

interface ChatMessage {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
  sources?: string[]
}

export default function DashboardPage() {
  const { user, loading, signOut } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login")
    }
  }, [user, loading, router])

  const [activeTab, setActiveTab] = useState("upload")
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [messageType, setMessageType] = useState<"success" | "error">("success")
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
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
    {
      key: "dashboard",
      label: "Dashboard",
      icon: BarChart3,
    },
  ]

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

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
    } catch {
      setUploadMessage("Network error occurred while uploading")
      setMessageType("error")
    } finally {
      setIsUploading(false)
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

    const newUserMessage: ChatMessage = {
      id: Date.now().toString(),
      content: userMessage,
      role: "user",
      timestamp: new Date(),
    }

    setChatMessages((prev) => [...prev, newUserMessage])
    setIsSendingMessage(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage }),
      })

      const result = await response.json()

      if (response.ok) {
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          content: result.answer || result.message,
          role: "assistant",
          timestamp: new Date(),
          sources: result.sources,
        }
        setChatMessages((prev) => [...prev, assistantMessage])
      } else {
        setChatError(result.message || "Failed to send message")
      }
    } catch {
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
          <Card className="w-full">
            <CardHeader>
              <CardTitle>Upload Documents</CardTitle>
              <CardDescription>Upload PDF files for AI analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors">
                  <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium text-foreground mb-2">Drop PDF files here or click to upload</p>
                  <p className="text-sm text-muted-foreground mb-4">Only PDF files are supported • Maximum 10MB</p>
                  <Button onClick={handleFileSelect} disabled={isUploading}>
                    {isUploading ? "Uploading..." : "Choose PDF File"}
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>

                {uploadMessage && (
                  <div
                    className={`p-4 rounded-lg border ${
                      messageType === "success"
                        ? "bg-secondary/10 border-secondary text-secondary-foreground"
                        : "bg-destructive/10 border-destructive text-destructive-foreground"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        {messageType === "success" ? (
                          <CheckCircle className="h-5 w-5 mt-0.5" />
                        ) : (
                          <AlertCircle className="h-5 w-5 mt-0.5" />
                        )}
                        <p className="text-sm">{uploadMessage}</p>
                      </div>
                      <Button variant="ghost" size="icon" onClick={closeMessage} className="h-8 w-8">
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )
      case "chat":
        return (
          <Card className="w-full">
            <CardHeader>
              <CardTitle>AI Chat Assistant</CardTitle>
              <CardDescription>Ask questions about your uploaded documents</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="h-96 border rounded-lg p-4 bg-muted/30 overflow-y-auto">
                  <div className="space-y-3">
                    {chatMessages.length === 0 && (
                      <div className="flex flex-col items-center justify-center h-full text-center">
                        <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-3">
                          <FileText className="h-6 w-6 text-primary" />
                        </div>
                        <h3 className="text-lg font-semibold text-foreground mb-2">Policy Assistant</h3>
                        <p className="text-sm text-muted-foreground max-w-xs">
                          Hi! I'm your Policy Assistant. Upload documents and ask me anything about your policies!
                        </p>
                      </div>
                    )}

                    {chatMessages.map((message) => (
                      <div
                        key={message.id}
                        className={`p-3 rounded-lg max-w-xs ${
                          message.role === "assistant" ? "bg-primary/10 text-foreground" : "bg-card ml-auto shadow-sm"
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        {message.sources && message.sources.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-border">
                            <p className="text-xs text-muted-foreground mb-1">Sources:</p>
                            <div className="space-y-1">
                              {message.sources.map((source, index) => (
                                <p key={index} className="text-xs text-primary">
                                  • {source}
                                </p>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                    {isSendingMessage && (
                      <div className="bg-primary/10 p-3 rounded-lg max-w-xs">
                        <p className="text-sm text-foreground">Thinking...</p>
                      </div>
                    )}
                  </div>
                </div>

                {chatError && (
                  <div className="p-3 rounded-lg border bg-destructive/10 border-destructive">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="h-4 w-4 text-destructive mt-0.5" />
                        <p className="text-sm text-destructive-foreground">{chatError}</p>
                      </div>
                      <Button variant="ghost" size="icon" onClick={closeChatError} className="h-8 w-8">
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}

                <form onSubmit={handleChatSubmit} className="flex gap-2">
                  <Input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask about your policy documents..."
                    disabled={isSendingMessage}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={!chatInput.trim() || isSendingMessage}>
                    <Send className="h-4 w-4" />
                  </Button>
                </form>
              </div>
            </CardContent>
          </Card>
        )
      case "dashboard":
        return (
          <div className="w-full space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Analytics Dashboard</CardTitle>
                <CardDescription>Overview of your document analysis activity</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-primary/10 rounded-lg">
                    <h3 className="font-semibold text-primary mb-2">Documents Uploaded</h3>
                    <p className="text-2xl font-bold text-foreground">12</p>
                  </div>
                  <div className="p-4 bg-secondary/10 rounded-lg">
                    <h3 className="font-semibold text-secondary mb-2">Chat Messages</h3>
                    <p className="text-2xl font-bold text-foreground">48</p>
                  </div>
                  <div className="p-4 bg-accent/10 rounded-lg">
                    <h3 className="font-semibold text-accent mb-2">AI Insights</h3>
                    <p className="text-2xl font-bold text-foreground">156</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
                    <FileText className="h-5 w-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">Policy Document uploaded</p>
                      <p className="text-xs text-muted-foreground">2 hours ago</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
                    <MessageCircle className="h-5 w-5 text-secondary" />
                    <div>
                      <p className="text-sm font-medium">Chat session completed</p>
                      <p className="text-xs text-muted-foreground">4 hours ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex">
      <div className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col">
        <div className="p-6 border-b border-sidebar-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-sidebar-primary rounded-lg flex items-center justify-center">
              <FileText className="h-5 w-5 text-sidebar-primary-foreground" />
            </div>
            <span className="text-lg font-bold text-sidebar-foreground">Policy Pilot</span>
          </div>
        </div>

        <nav className="flex-1 p-4">
          <div className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.key}
                  onClick={() => setActiveTab(item.key)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                    activeTab === item.key
                      ? "bg-sidebar-primary text-sidebar-primary-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {item.label}
                </button>
              )
            })}
          </div>
        </nav>

        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-sidebar-accent rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-sidebar-accent-foreground">
                  {user?.name?.charAt(0) || "U"}
                </span>
              </div>
              <span className="text-sm text-sidebar-foreground">AY</span>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Button
                variant="ghost"
                size="icon"
                onClick={signOut}
                className="h-8 w-8 text-sidebar-foreground hover:text-destructive"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <main className="flex-1 p-8">
          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-foreground mb-2">
                {navigationItems.find((item) => item.key === activeTab)?.label}
              </h1>
              <p className="text-muted-foreground">
                {activeTab === "upload" && "Upload and process your PDF documents"}
                {activeTab === "chat" && "Chat with your AI assistant about your documents"}
                {activeTab === "dashboard" && "View your analytics and recent activity"}
              </p>
            </div>

            {renderContent()}
          </div>
        </main>
      </div>
    </div>
  )
}
