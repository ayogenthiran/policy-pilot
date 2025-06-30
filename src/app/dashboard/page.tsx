'use client'

import React from 'react'
import { useAuth } from '@/components/auth/AuthProvider'
import { useRouter } from 'next/navigation'

export default function DashboardPage() {
  const { user, signOut, loading } = useAuth()
  const router = useRouter()

  const handleSignOut = async () => {
    await signOut()
    router.push('/auth/login')
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading your dashboard...</p>
        
        <style jsx>{`
          .loading-container {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          }

          .loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #5865f2;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
          }

          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }

          p {
            color: #666;
            font-size: 16px;
          }
        `}</style>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Welcome to your Dashboard!</h1>
          <button onClick={handleSignOut} className="sign-out-btn">
            Sign Out
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="welcome-card">
          <div className="card-header">
            <h2>Hello, {user?.email}!</h2>
            <p>You have successfully signed in to your account.</p>
          </div>
          
          <div className="user-info">
            <div className="info-item">
              <strong>Email:</strong> {user?.email}
            </div>
            <div className="info-item">
              <strong>User ID:</strong> {user?.id}
            </div>
            <div className="info-item">
              <strong>Email Verified:</strong> {user?.email_confirmed_at ? 'Yes' : 'No'}
            </div>
            <div className="info-item">
              <strong>Last Sign In:</strong> {user?.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleString() : 'N/A'}
            </div>
          </div>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <h3>🔐 Secure Authentication</h3>
            <p>Your account is protected with industry-standard security measures.</p>
          </div>
          
          <div className="feature-card">
            <h3>🚀 Ready to Build</h3>
            <p>Start building your application with this authentication foundation.</p>
          </div>
          
          <div className="feature-card">
            <h3>📱 Responsive Design</h3>
            <p>Works perfectly on desktop, tablet, and mobile devices.</p>
          </div>
        </div>
      </main>

      <style jsx>{`
        .dashboard {
          min-height: 100vh;
          background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }

        .dashboard-header {
          background: white;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          padding: 16px 0;
        }

        .header-content {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 24px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .dashboard-header h1 {
          color: #1a1a1a;
          font-size: 24px;
          font-weight: 600;
          margin: 0;
        }

        .sign-out-btn {
          background: #5865f2;
          color: white;
          border: none;
          border-radius: 8px;
          padding: 12px 24px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .sign-out-btn:hover {
          background: #4f5acb;
          transform: translateY(-1px);
        }

        .dashboard-main {
          max-width: 1200px;
          margin: 0 auto;
          padding: 40px 24px;
        }

        .welcome-card {
          background: white;
          border-radius: 12px;
          padding: 32px;
          margin-bottom: 32px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .card-header h2 {
          color: #1a1a1a;
          font-size: 28px;
          font-weight: 600;
          margin: 0 0 8px 0;
        }

        .card-header p {
          color: #666;
          font-size: 16px;
          margin: 0 0 24px 0;
        }

        .user-info {
          display: grid;
          gap: 12px;
        }

        .info-item {
          padding: 12px 16px;
          background: #f8f9fa;
          border-radius: 8px;
          font-size: 14px;
          color: #666;
        }

        .info-item strong {
          color: #1a1a1a;
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 24px;
        }

        .feature-card {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transition: transform 0.3s ease;
        }

        .feature-card:hover {
          transform: translateY(-4px);
        }

        .feature-card h3 {
          color: #1a1a1a;
          font-size: 18px;
          font-weight: 600;
          margin: 0 0 12px 0;
        }

        .feature-card p {
          color: #666;
          font-size: 14px;
          line-height: 1.5;
          margin: 0;
        }

        @media (max-width: 768px) {
          .header-content {
            flex-direction: column;
            gap: 16px;
            text-align: center;
          }

          .dashboard-main {
            padding: 24px 16px;
          }

          .welcome-card {
            padding: 24px;
          }

          .features-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  )
} 