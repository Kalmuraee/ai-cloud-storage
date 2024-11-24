import { useRouter } from 'next/navigation'
import { useMutation } from '@tanstack/react-query'
import { authAPI } from '@/lib/api'
import { LoginInput, RegisterInput } from '@/lib/validations/auth'

export function useAuth() {
  const router = useRouter()

  const login = useMutation({
    mutationFn: async (data: LoginInput) => {
      const response = await authAPI.login(data.email, data.password)
      return response
    },
    onSuccess: () => {
      router.push('/dashboard')
      router.refresh()
    },
  })

  const register = useMutation({
    mutationFn: async (data: RegisterInput) => {
      const response = await authAPI.register(
        data.email,
        data.username,
        data.password,
        data.fullName
      )
      return response
    },
    onSuccess: () => {
      router.push('/login')
    },
  })

  return {
    login,
    register,
  }
}
