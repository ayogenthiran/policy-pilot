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
      setTimeout(() => {
        router.push('/')
      }, 1500)
    }
  }

  const handleGoogleSignIn = async () => {
    const { error: authError } = await signInWithGoogle()
    if (authError) {
      setError(authError.message)
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

      <div className="divider">
        <span>or</span>
      </div>

      <button type="button" className="social-btn" onClick={handleGoogleSignIn}>
        <svg className="google-icon" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Sign in with Google
      </button>

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
          padding: 16px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 16px;
          transition: all 0.3s ease;
          background: #fff;
          outline: none;
        }

        .form-input:focus {
          border-color: #5865f2;
          box-shadow: 0 0 0 3px rgba(88, 101, 242, 0.1);
          transform: translateY(-1px);
        }

        .form-input::placeholder {
          color: #999;
          font-weight: 400;
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
          font-weight: 500;
          padding: 4px 8px;
          border-radius: 4px;
          transition: all 0.2s ease;
        }

        .password-toggle:hover {
          background-color: rgba(88, 101, 242, 0.1);
        }

        .forgot-password-container {
          text-align: right;
          margin-bottom: 24px;
          height: auto;
          visibility: visible;
        }

        .forgot-password {
          display: inline-block !important;
          color: #000000 !important;
          text-decoration: none !important;
          font-size: 14px !important;
          font-weight: 700 !important;
          transition: color 0.2s ease !important;
          visibility: visible !important;
          opacity: 1 !important;
        }

        .forgot-password:hover {
          color: #5865f2 !important;
        }

        .sign-in-btn {
          width: 100%;
          background: #5865f2;
          color: white;
          border: none;
          border-radius: 24px;
          padding: 16px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          margin-bottom: 24px;
          box-shadow: 0 4px 12px rgba(88, 101, 242, 0.3);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .sign-in-btn:hover:not(:disabled) {
          background: #4f5acb;
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(88, 101, 242, 0.4);
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

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .divider {
          text-align: center;
          margin: 24px 0;
          position: relative;
          color: #666;
          font-size: 14px;
        }

        .divider::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 0;
          right: 0;
          height: 1px;
          background: #e0e0e0;
        }

        .divider span {
          background: white;
          padding: 0 16px;
          position: relative;
          z-index: 1;
        }

        .social-btn {
          width: 100%;
          background: white;
          color: #1a1a1a;
          border: 1px solid #ddd;
          border-radius: 24px;
          padding: 14px;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          margin-bottom: 12px;
        }

        .social-btn:hover {
          background: #f8f8f8;
          border-color: #ccc;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .google-icon {
          width: 20px;
          height: 20px;
        }

        .sign-up-link {
          text-align: center;
          margin-top: 24px;
          color: #666;
          font-size: 14px;
        }

        .sign-up-link :global(a) {
          color: #5865f2;
          text-decoration: none;
          font-weight: 500;
          transition: color 0.2s ease;
        }

        .sign-up-link :global(a:hover) {
          color: #4f5acb;
        }

        .error-message {
          background: #fee;
          color: #c33;
          padding: 12px;
          border-radius: 8px;
          margin-bottom: 20px;
          font-size: 14px;
          text-align: center;
        }
      `}</style>
    </>
  )
} 