"use client"

import Link from 'next/link'
import AuthContainer from '@/components/auth/AuthContainer'

export default function AuthCodeErrorPage() {
  return (
    <AuthContainer 
      title="Authentication Error" 
      subtitle="Something went wrong with the sign-in process"
    >
      <div className="error-container">
        <div className="error-content">
          <div className="error-icon">⚠️</div>
          <h3>Authentication Failed</h3>
          <p>
            There was an issue with your authentication request. This could be due to:
          </p>
          <ul className="error-list">
            <li>Google OAuth is not properly configured</li>
            <li>Invalid or expired authentication code</li>
            <li>Network connectivity issues</li>
            <li>Browser security settings blocking the request</li>
          </ul>
          
          <div className="error-actions">
            <Link href="/auth/login" className="retry-btn">
              Try Again
            </Link>
            <Link href="/auth/signup" className="signup-link">
              Create Account Instead
            </Link>
          </div>
        </div>

        <style jsx>{`
          .error-container {
            text-align: center;
            padding: 20px;
          }

          .error-content {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 12px;
            padding: 32px 24px;
            margin-bottom: 24px;
          }

          .error-icon {
            font-size: 48px;
            margin-bottom: 16px;
          }

          h3 {
            color: #dc2626;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
          }

          p {
            color: #6b7280;
            font-size: 16px;
            line-height: 1.5;
            margin-bottom: 16px;
          }

          .error-list {
            text-align: left;
            max-width: 400px;
            margin: 0 auto 24px auto;
            color: #6b7280;
            font-size: 14px;
            line-height: 1.6;
          }

          .error-list li {
            margin-bottom: 8px;
          }

          .error-actions {
            display: flex;
            flex-direction: column;
            gap: 12px;
            align-items: center;
          }

          .retry-btn {
            background: #5865f2;
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-block;
          }

          .retry-btn:hover {
            background: #4f5acb;
            transform: translateY(-1px);
          }

          .signup-link {
            color: #5865f2;
            text-decoration: none;
            font-weight: 500;
            font-size: 14px;
            transition: color 0.2s ease;
          }

          .signup-link:hover {
            color: #4f5acb;
          }

          @media (max-width: 480px) {
            .error-content {
              padding: 24px 16px;
            }
            
            .error-actions {
              flex-direction: column;
            }
          }
        `}</style>
      </div>
    </AuthContainer>
  )
} 