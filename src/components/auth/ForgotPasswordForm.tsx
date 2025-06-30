'use client'

import React, { useState } from 'react'
import { useAuth } from './AuthProvider'
import Link from 'next/link'

export default function ForgotPasswordForm() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  
  const { resetPassword } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    const { error: authError } = await resetPassword(email)
    
    if (authError) {
      setError(authError.message)
      setLoading(false)
    } else {
      setSuccess(true)
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="success-message">
        <div className="success-icon">✓</div>
        <h3>Check your email!</h3>
        <p>We've sent a password reset link to <strong>{email}</strong></p>
        <p className="small-text">Didn't receive the email? Check your spam folder or try again.</p>
        <Link href="/auth/login" className="back-to-login">
          Back to Sign In
        </Link>
        
        <style jsx>{`
          .success-message {
            text-align: center;
            padding: 20px 0;
          }

          .success-icon {
            width: 60px;
            height: 60px;
            background: #22c55e;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
            margin: 0 auto 20px;
          }

          .success-message h3 {
            color: #1a1a1a;
            margin-bottom: 12px;
            font-size: 24px;
          }

          .success-message p {
            color: #666;
            margin-bottom: 12px;
            line-height: 1.5;
          }

          .small-text {
            font-size: 14px;
            margin-bottom: 24px !important;
          }

          .back-to-login {
            display: inline-block;
            background: #5865f2;
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 24px;
            font-weight: 500;
            transition: all 0.3s ease;
          }

          .back-to-login:hover {
            background: #4f5acb;
            transform: translateY(-2px);
          }
        `}</style>
      </div>
    )
  }

  return (
    <>
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="form-description">
          <p>Enter your email address and we'll send you a link to reset your password.</p>
        </div>

        <div className="form-group">
          <input 
            type="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="form-input" 
            placeholder="Enter your email address"
            required
          />
        </div>

        <button 
          type="submit" 
          className="sign-in-btn"
          disabled={loading}
        >
          {loading ? (
            <div className="loading-spinner"></div>
          ) : (
            'Send Reset Link'
          )}
        </button>
      </form>

      <div className="sign-up-link">
        Remember your password? <Link href="/auth/login">Sign in</Link>
      </div>

      <style jsx>{`
        .form-description {
          margin-bottom: 24px;
          text-align: center;
        }

        .form-description p {
          color: #666;
          font-size: 16px;
          line-height: 1.5;
        }

        .form-group {
          margin-bottom: 24px;
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