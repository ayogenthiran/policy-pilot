import AuthContainer from '@/components/auth/AuthContainer'
import ForgotPasswordForm from '@/components/auth/ForgotPasswordForm'

export default function ForgotPasswordPage() {
  return (
    <AuthContainer 
      title="Reset password" 
      subtitle="We'll help you get back into your account"
    >
      <ForgotPasswordForm />
    </AuthContainer>
  )
} 