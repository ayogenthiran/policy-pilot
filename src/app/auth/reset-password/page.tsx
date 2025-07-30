'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import AuthContainer from '@/components/auth/AuthContainer'

export default function ResetPasswordPage() {
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    // Handle the password reset session
    supabase.auth.onAuthStateChange(async (event) => {
      if (event === 'PASSWORD_RECOVERY') {
        // The user has clicked the reset password link
        // They are now logged in with a temporary session
      }
    })
  }, [supabase])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setLoading(true)

    const { error: updateError } = await supabase.auth.updateUser({
      password: password
    })

    if (updateError) {
      setError(updateError.message)
      setLoading(false)
    } else {
      setSuccess(true)
      setTimeout(() => {
        router.push('/dashboard')
      }, 2000)
    }
  }

  if (success) {
    return (
      <AuthContainer 
        title="Password Updated!" 
        subtitle="Your password has been successfully updated"
      >
        <div className="success-message">
          <div className="success-icon">✓</div>
          <p>Redirecting to your dashboard...</p>
          
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

            .success-message p {
              color: #666;
              font-size: 16px;
            }
          `}</style>
        </div>
      </AuthContainer>
    )
  }

  return (
    <AuthContainer 
      title="Set new password" 
      subtitle="Enter your new password below"
    >
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="form-group">
          <div className="password-container">
            <input 
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input" 
              placeholder="New Password"
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

        <div className="form-group">
          <div className="password-container">
            <input 
              type={showConfirmPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="form-input" 
              placeholder="Confirm New Password"
              required
            />
            <button 
              type="button" 
              className="password-toggle"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            >
              {showConfirmPassword ? 'hide' : 'show'}
            </button>
          </div>
        </div>

        <button 
          type="submit" 
          className="sign-in-btn"
          disabled={loading}
        >
          {loading ? (
            <div className="loading-spinner"></div>
          ) : (
            'Update Password'
          )}
        </button>
      </form>

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
    </AuthContainer>
  )
} 