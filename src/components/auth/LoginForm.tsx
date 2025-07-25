'use client'

import React, { useState } from 'react'
import { useAuth } from './AuthProvider'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  
  const { signIn, signInWithGoogle } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const { error: authError } = await signIn(email, password)
    
    if (authError) {
      setError(authError.message)
      setLoading(false)
    } else {
      setSuccess(true)
      // Wait a moment for the auth state to propagate before redirecting
      setTimeout(() => {
        router.push('/')
      }, 500)
    }
  }

  const handleGoogleSignIn = async () => {
    try {
      setError('')
      setGoogleLoading(true)
      
      const { error: authError } = await signInWithGoogle()
      if (authError) {
        console.error('Google sign-in error:', authError)
        if (authError.message.includes('Email not confirmed')) {
          setError('Please verify your email address before signing in.')
        } else if (authError.message.includes('Invalid login credentials')) {
          setError('Google sign-in failed. Please try again.')
        } else if (authError.message.includes('OAuth') || authError.message.includes('provider')) {
          setError('Google authentication is not configured. Please use email/password or contact support.')
        } else {
          setError(authError.message || 'Google sign-in failed. Please try again.')
        }
        setGoogleLoading(false)
      }
      // If no error, the redirect will happen automatically
    } catch (error) {
      console.error('Unexpected error during Google sign-in:', error)
      setError('An unexpected error occurred. Please try again.')
      setGoogleLoading(false)
    }
  }

  return (
    <>
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="form-group">
          <input 
            type="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="form-input" 
            placeholder="Email or Phone"
            required
          />
        </div>

        <div className="form-group">
          <div className="password-container">
            <input 
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input" 
              placeholder="Password"
              required
            />
            <button 
              type="button" 
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? 'hide' : 'show'}
            </button>
          </div>
        </div>

        <div className="forgot-password-container">
          <Link href="/auth/forgot-password" className="forgot-password">
            Forgot password?
          </Link>
        </div>

        <button 
          type="submit" 
          className={`sign-in-btn ${success ? 'success-animation' : ''}`}
          disabled={loading}
        >
          {loading ? (
            <div className="loading-spinner"></div>
          ) : success ? (
            '✓ Success!'
          ) : (
            'Sign in'
          )}
        </button>
      </form>

      {/* Google sign-in temporarily disabled until OAuth is configured */}
      {false && (
        <>
          <div className="divider">
            <span>or</span>
          </div>

          <button 
            type="button" 
            className="social-btn" 
            onClick={handleGoogleSignIn}
            disabled={googleLoading}
          >
            {googleLoading ? (
              <div className="loading-spinner-google"></div>
            ) : (
              <svg className="google-icon" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
            )}
            {googleLoading ? 'Connecting...' : 'Sign in with Google'}
          </button>
        </>
      )}

      <div className="sign-up-link">
        New to our platform? <Link href="/auth/signup">Join now</Link>
      </div>

      <style jsx>{`
        .form-group {
          margin-bottom: 20px;
          position: relative;
        }

        .form-input {
          width: 100%;
          padding: 18px 16px;
          border: 2px solid #e1e5e9;
          border-radius: 12px;
          font-size: 16px;
          font-weight: 400;
          transition: all 0.3s ease;
          background: #ffffff;
          outline: none;
          color: #1a1a1a;
          line-height: 1.4;
        }

        .form-input:focus {
          border-color: #5865f2;
          box-shadow: 0 0 0 4px rgba(88, 101, 242, 0.12);
          transform: translateY(-1px);
        }

        .form-input::placeholder {
          color: #6b7280;
          font-weight: 400;
          opacity: 1;
        }

        .password-container {
          position: relative;
        }

        .password-toggle {
          position: absolute;
          right: 16px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          color: #5865f2;
          cursor: pointer;
          font-size: 14px;
          font-weight: 600;
          padding: 8px 10px;
          border-radius: 6px;
          transition: all 0.2s ease;
          user-select: none;
        }

        .password-toggle:hover {
          background-color: rgba(88, 101, 242, 0.1);
          color: #4f5acb;
        }

        .forgot-password-container {
          display: flex;
          justify-content: flex-end;
          margin-bottom: 28px;
          height: auto;
          visibility: visible;
          padding: 12px 0;
        }

        .forgot-password {
          display: inline-flex !important;
          color: #000000 !important;
          background-color: #ff6b35 !important;
          text-decoration: none !important;
          font-size: 16px !important;
          font-weight: 800 !important;
          transition: all 0.3s ease !important;
          visibility: visible !important;
          opacity: 1 !important;
          padding: 14px 24px !important;
          border-radius: 12px !important;
          border: 3px solid #ff4500 !important;
          min-height: 50px !important;
          align-items: center !important;
          justify-content: center !important;
          box-shadow: 0 4px 12px rgba(255, 107, 53, 0.4) !important;
          letter-spacing: 0.5px !important;
          white-space: nowrap !important;
          z-index: 99999 !important;
          text-transform: uppercase !important;
        }

        .forgot-password:hover {
          color: #ffffff !important;
          background: #ff4500 !important;
          border-color: #ff3300 !important;
          text-decoration: none !important;
          transform: translateY(-4px) scale(1.05) !important;
          box-shadow: 0 8px 20px rgba(255, 69, 0, 0.6) !important;
        }

        .forgot-password:active {
          transform: translateY(-1px) !important;
          box-shadow: 0 3px 8px rgba(88, 101, 242, 0.3) !important;
        }

        .sign-in-btn {
          width: 100%;
          background: #5865f2;
          color: white;
          border: none;
          border-radius: 12px;
          padding: 18px 16px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          margin-bottom: 28px;
          box-shadow: 0 4px 14px rgba(88, 101, 242, 0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 56px;
        }

        .sign-in-btn:hover:not(:disabled) {
          background: #4f5acb;
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(88, 101, 242, 0.4);
        }

        .sign-in-btn:active {
          transform: translateY(0);
        }

        .sign-in-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .loading-spinner {
          width: 20px;
          height: 20px;
          border: 2px solid #ffffff;
          border-radius: 50%;
          border-top-color: transparent;
          animation: spin 1s ease-in-out infinite;
        }

        .loading-spinner-google {
          width: 20px;
          height: 20px;
          border: 2px solid #e5e7eb;
          border-radius: 50%;
          border-top-color: #5865f2;
          animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .divider {
          text-align: center;
          margin: 28px 0;
          position: relative;
          color: #6b7280;
          font-size: 14px;
          font-weight: 500;
        }

        .divider::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 0;
          right: 0;
          height: 1px;
          background: #e5e7eb;
        }

        .divider span {
          background: white;
          padding: 0 20px;
          position: relative;
          z-index: 1;
        }

        .social-btn {
          width: 100%;
          background: white;
          color: #374151;
          border: 2px solid #e5e7eb;
          border-radius: 12px;
          padding: 16px;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          margin-bottom: 16px;
          min-height: 56px;
        }

        .social-btn:hover {
          background: #f9fafb;
          border-color: #d1d5db;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        }

        .google-icon {
          width: 20px;
          height: 20px;
        }

        .sign-up-link {
          text-align: center;
          margin-top: 28px;
          color: #6b7280;
          font-size: 15px;
          line-height: 1.5;
        }

        .sign-up-link :global(a) {
          color: #5865f2;
          text-decoration: none;
          font-weight: 600;
          transition: color 0.2s ease;
        }

        .sign-up-link :global(a:hover) {
          color: #4f5acb;
        }

        .error-message {
          background: #fef2f2;
          color: #dc2626;
          border: 1px solid #fecaca;
          padding: 14px 16px;
          border-radius: 10px;
          margin-bottom: 24px;
          font-size: 14px;
          font-weight: 500;
          text-align: center;
        }

        /* Additional contrast improvements */
        .form-input:not(:placeholder-shown) {
          color: #111827;
          font-weight: 500;
        }

        /* Mobile responsiveness */
        @media (max-width: 480px) {
          .form-input {
            padding: 16px 14px;
            font-size: 16px; /* Prevents zoom on iOS */
          }
          
          .sign-in-btn, .social-btn {
            padding: 16px 14px;
            min-height: 52px;
          }
          
          .forgot-password {
            font-size: 14px !important;
            padding: 10px 16px !important;
            min-height: 44px !important;
          }
        }
      `}</style>
    </>
  )
}