// File: workers/queue-processor.js

// Configuration
const SUPABASE_FUNCTION_URL = process.env.SUPABASE_FUNCTION_URL
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY
const POLL_INTERVAL_MS = 5000  // 5 seconds

// Validate configuration
if (!SUPABASE_FUNCTION_URL) {
  console.error('[WORKER] ERROR: SUPABASE_FUNCTION_URL environment variable is not set')
  process.exit(1)
}
if (!SUPABASE_ANON_KEY) {
  console.error('[WORKER] ERROR: SUPABASE_ANON_KEY environment variable is not set')
  process.exit(1)
}

// Function implementations will be added in next steps

async function processQueue() {
  try {
    console.log(`[WORKER] ${new Date().toISOString()} - Polling queue...`)

    const response = await fetch(
      `${SUPABASE_FUNCTION_URL}/process-announcement-queue`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json'
        },
        signal: AbortSignal.timeout(45000)  // 45s timeout (Edge Function has 30s + buffer)
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const result = await response.json()

    // Validate response shape
    if (typeof result.processed !== 'number') {
      throw new Error(`Invalid response format: missing 'processed' field`)
    }

    if (result.processed > 0) {
      console.log(`[WORKER] ✓ Processed ${result.processed} items (${result.succeeded} succeeded, ${result.failed} failed)`)
    }
  } catch (error) {
    console.error(`[WORKER] ✗ Error:`, error.message)
  }
}
