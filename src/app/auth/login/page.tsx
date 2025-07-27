import AuthContainer from '@/components/auth/AuthContainer'
import LoginForm from '@/components/auth/LoginForm'

export default function LoginPage() {
  return (
    <AuthContainer 
      title="Sign in" 
      subtitle="Navigate your policies with confidence"
    >
      <LoginForm />
    </AuthContainer>
  )
} 