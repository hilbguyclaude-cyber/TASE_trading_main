// File: supabase/functions/process-announcement-queue/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const VERCEL_API_URL = Deno.env.get('VERCEL_API_URL') || 'https://your-app.vercel.app'
const MAX_RETRIES = 3
const PROCESSING_TIMEOUT_MS = 30000  // 30 seconds
