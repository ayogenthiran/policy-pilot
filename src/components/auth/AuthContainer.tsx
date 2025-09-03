'use client'

import React from 'react'
import ThemeToggle from '@/components/theme-toggle'

interface AuthContainerProps {
  children: React.ReactNode
  title: string
  subtitle: string
}

export default function AuthContainer({ children, title, subtitle }: AuthContainerProps) {
  return (
    <div className="auth-page-wrapper">
      <div className="theme-toggle-container">
        <ThemeToggle />
      </div>
      <div className="auth-container">
        <div className="auth-header">
          <h1 className="auth-title">{title}</h1>
          <p className="auth-subtitle">{subtitle}</p>
        </div>
        
        {children}
      </div>

      <style jsx>{`
        .auth-page-wrapper {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          background: white;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          position: relative;
        }

        :global(.dark) .auth-page-wrapper {
          background: #0a0a0a;
        }

        .theme-toggle-container {
          position: absolute;
          top: 20px;
          right: 20px;
          z-index: 10;
        }

        .auth-container {
          background: white;
          border-radius: 12px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
          padding: 48px 40px;
          width: 100%;
          max-width: 400px;
          position: relative;
          animation: slideIn 0.6s ease-out;
        }

        :global(.dark) .auth-container {
          background: #1a1a1a;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .auth-header {
          text-align: center;
          margin-bottom: 32px;
        }

        .auth-title {
          font-size: 32px;
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 8px;
        }

        :global(.dark) .auth-title {
          color: #ededed;
        }

        .auth-subtitle {
          font-size: 16px;
          color: #666;
          font-weight: 400;
          line-height: 1.4;
        }

        :global(.dark) .auth-subtitle {
          color: #a0a0a0;
        }



        /* Success state animation */
        :global(.success-animation) {
          animation: success 0.6s ease-out;
        }

        @keyframes success {
          0% { transform: scale(1); }
          50% { transform: scale(1.05); }
          100% { transform: scale(1); }
        }

        /* Mobile responsiveness */
        @media (max-width: 480px) {
          .auth-container {
            padding: 32px 24px;
            margin: 16px;
          }
          
          .auth-title {
            font-size: 28px;
          }
        }
      `}</style>
    </div>
  )
} 