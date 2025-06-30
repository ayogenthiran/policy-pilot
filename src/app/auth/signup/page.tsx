import AuthContainer from '@/components/auth/AuthContainer'
import SignupForm from '@/components/auth/SignupForm'

export default function SignupPage() {
  return (
    <AuthContainer 
      title="Join us" 
      subtitle="Create your account to get started"
    >
      <SignupForm />
    </AuthContainer>
  )
} 