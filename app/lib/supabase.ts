import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key'

export const isSupabaseConfigured = Boolean(
  process.env.NEXT_PUBLIC_SUPABASE_URL &&
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

if (!isSupabaseConfigured) {
  console.warn('Supabase credentials not configured - using placeholder values')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Types for database tables
export interface Announcement {
  id: string
  announcement_id: string
  company_name: string
  ticker: string
  title: string
  content: string
  published_at: string
  sentiment: 'positive' | 'negative' | 'neutral' | null
  confidence: number | null
  reasoning: string | null
  analyzed: boolean
  created_at: string
  attached_files?: Array<{
    name: string
    url: string
    type: string
  }>
}

export interface Position {
  id: string
  ticker: string
  company_name: string
  announcement_id: string
  entry_price: number
  peak_price: number
  exit_price: number | null
  position_size_ils: number
  entry_time: string
  exit_time: string | null
  profit_loss_ils: number | null
  profit_loss_percent: number | null
  sentiment: string
  confidence: number
  reasoning: string
  entry_reason: string
  exit_reason: string | null
  created_at: string
}

export interface SystemStatus {
  id: string
  status: 'HEALTHY' | 'DEGRADED' | 'DOWN'
  buying_enabled: boolean
  selling_enabled: boolean
  last_check: string | null
  metadata: any
  created_at: string
  updated_at: string
}
