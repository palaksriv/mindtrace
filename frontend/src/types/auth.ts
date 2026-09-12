export type UserRole = 'student' | 'counsellor'

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
}

export interface User {
  id: number
  name: string
  email: string
  role: UserRole
  created_at: string
}
