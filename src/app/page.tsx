"use client"

import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, MessageCircle, BarChart3, ArrowRight, Sparkles, Shield, Zap } from "lucide-react"
import Link from "next/link"
import ThemeToggle from "@/components/theme-toggle"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <FileText className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">Policy Pilot</span>
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link href="/auth/login">
              <Button variant="outline">Sign In</Button>
            </Link>
            <Link href="/auth/login">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center max-w-4xl">
          <div className="inline-flex items-center gap-2 bg-muted px-3 py-1 rounded-full text-sm text-muted-foreground mb-6">
            <Sparkles className="h-4 w-4" />
            AI-Powered Document Analysis
          </div>
          <h1 className="text-5xl font-bold text-foreground mb-6 text-balance">
            Transform Your Documents with
            <span className="text-primary"> AI Intelligence</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 text-pretty max-w-2xl mx-auto">
            Upload, analyze, and chat with your documents using advanced AI. Get instant insights, summaries, and
            answers from your policy documents.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/login">
              <Button size="lg" className="text-lg px-8">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button variant="outline" size="lg" className="text-lg px-8 bg-transparent">
              Watch Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 bg-muted/30">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">Everything you need for document intelligence</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Powerful AI tools to help you understand, analyze, and interact with your documents like never before.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card className="border-border">
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <CardTitle>Smart Upload</CardTitle>
                <CardDescription>Drag and drop PDF documents for instant AI processing and analysis</CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-border">
              <CardHeader>
                <div className="w-12 h-12 bg-secondary/10 rounded-lg flex items-center justify-center mb-4">
                  <MessageCircle className="h-6 w-6 text-secondary" />
                </div>
                <CardTitle>AI Chat</CardTitle>
                <CardDescription>
                  Ask questions about your documents and get intelligent, contextual responses
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-border">
              <CardHeader>
                <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center mb-4">
                  <BarChart3 className="h-6 w-6 text-accent" />
                </div>
                <CardTitle>Analytics Dashboard</CardTitle>
                <CardDescription>Track document insights, usage patterns, and AI interaction metrics</CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-foreground mb-6">Why choose Policy Pilot?</h2>
              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Zap className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-2">Lightning Fast</h3>
                    <p className="text-muted-foreground">Process and analyze documents in seconds, not hours</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-8 h-8 bg-secondary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Shield className="h-4 w-4 text-secondary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-2">Secure & Private</h3>
                    <p className="text-muted-foreground">
                      Your documents are encrypted and never shared with third parties
                    </p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="w-8 h-8 bg-accent/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Sparkles className="h-4 w-4 text-accent" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-2">AI-Powered Insights</h3>
                    <p className="text-muted-foreground">
                      Get intelligent summaries, key points, and actionable insights
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-muted/30 rounded-2xl p-8 text-center">
              <div className="w-24 h-24 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <FileText className="h-12 w-12 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-4">Ready to get started?</h3>
              <p className="text-muted-foreground mb-6">
                Join thousands of professionals who trust Policy Pilot for their document analysis needs.
              </p>
              <Link href="/auth/login">
                <Button size="lg">
                  Start Your Free Trial
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12 px-4">
        <div className="container mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-6 h-6 bg-primary rounded-lg flex items-center justify-center">
              <FileText className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-bold text-foreground">Policy Pilot</span>
          </div>
          <p className="text-muted-foreground">© 2024 Policy Pilot. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
