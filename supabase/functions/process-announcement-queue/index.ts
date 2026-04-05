// File: supabase/functions/process-announcement-queue/index.ts

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const VERCEL_API_URL = Deno.env.get('VERCEL_API_URL') || 'https://your-app.vercel.app'
const MAX_RETRIES = 3
const PROCESSING_TIMEOUT_MS = 30000  // 30 seconds

serve(async (req) => {
  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    console.log('[QUEUE] Starting queue processing cycle')

    // 1. Fetch pending items (limit to 10 per cycle)
    const { data: pendingItems, error: fetchError } = await supabaseClient
      .from('announcement_processing_queue')
      .select('*, announcements(*)')
      .eq('status', 'pending')
      .order('created_at', { ascending: true })
      .limit(10)

    if (fetchError) throw fetchError

    if (!pendingItems || pendingItems.length === 0) {
      console.log('[QUEUE] No pending items')
      return new Response(JSON.stringify({ processed: 0 }), {
        headers: { 'Content-Type': 'application/json' },
      })
    }

    console.log(`[QUEUE] Found ${pendingItems.length} pending items`)

    // 2. Process each item
    const results = []
    for (const item of pendingItems) {
      try {
        // Mark as processing
        await supabaseClient
          .from('announcement_processing_queue')
          .update({ status: 'processing' })
          .eq('id', item.id)

        console.log(`[QUEUE] Processing ${item.announcement_id}`)

        // Call Vercel API
        const response = await fetch(
          `${VERCEL_API_URL}/api/analyze_sentiment`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ announcement_id: item.announcement_id }),
            signal: AbortSignal.timeout(PROCESSING_TIMEOUT_MS)
          }
        )

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`)
        }

        const result = await response.json()

        // Mark as completed
        await supabaseClient
          .from('announcement_processing_queue')
          .update({
            status: 'completed',
            processed_at: new Date().toISOString()
          })
          .eq('id', item.id)

        console.log(`[QUEUE] ✓ Completed ${item.announcement_id}`)
        results.push({ id: item.id, success: true })

      } catch (error) {
        console.error(`[QUEUE] ✗ Failed ${item.announcement_id}:`, error)
        // Error handling will be added in next step
        results.push({ id: item.id, success: false, error: error.message })
      }
    }

    return new Response(
      JSON.stringify({
        processed: results.length,
        succeeded: results.filter(r => r.success).length,
        failed: results.filter(r => !r.success).length,
        results: results
      }),
      { headers: { 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('[QUEUE] Edge function error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
})
