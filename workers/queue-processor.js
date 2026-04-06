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

// State management for graceful shutdown and request tracking
let isShuttingDown = false
let isProcessing = false
let activeRequest = null

async function processQueue() {
  if (isShuttingDown) {
    console.log('[WORKER] Shutdown in progress, skipping poll')
    return
  }

  if (isProcessing) {
    console.log('[WORKER] Previous poll still running, skipping...')
    return
  }

  isProcessing = true
  activeRequest = { timestamp: Date.now() }

  try {
    console.log(`[WORKER] ${new Date().toISOString()} - Polling queue...`)

    // Manual AbortController for Node.js compatibility
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 45000)

    const response = await fetch(
      `${SUPABASE_FUNCTION_URL}/process-announcement-queue`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json'
        },
        signal: controller.signal
      }
    )

    clearTimeout(timeoutId)

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
    // Differentiate error types
    if (error.name === 'AbortError') {
      console.error(`[WORKER] ✗ Timeout after 45s - Edge Function not responding`)
    } else if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
      console.error(`[WORKER] ✗ Network error:`, error.message)
    } else {
      console.error(`[WORKER] ✗ Error:`, error.message)
    }
  } finally {
    activeRequest = null
    isProcessing = false
  }
}

// Main loop
console.log('[WORKER] Starting queue processor...')
console.log(`[WORKER] Polling interval: ${POLL_INTERVAL_MS}ms (${POLL_INTERVAL_MS/1000}s)`)
console.log(`[WORKER] Supabase Function: ${SUPABASE_FUNCTION_URL}`)

// Set interval for polling
const pollInterval = setInterval(processQueue, POLL_INTERVAL_MS)

// Initial run (don't wait 5s for first poll)
processQueue()

// Graceful shutdown function
async function shutdown(signal) {
  console.log(`[WORKER] Received ${signal}, shutting down gracefully...`)
  isShuttingDown = true
  clearInterval(pollInterval)

  // Wait for active request with timeout
  const startTime = Date.now()
  while (activeRequest && (Date.now() - startTime) < 25000) {
    await new Promise(resolve => setTimeout(resolve, 100))
  }

  if (activeRequest) {
    console.log('[WORKER] Force shutdown - request still in progress')
  } else {
    console.log('[WORKER] Graceful shutdown complete')
  }

  process.exit(0)
}

// Signal handlers
process.on('SIGTERM', () => shutdown('SIGTERM'))
process.on('SIGINT', () => shutdown('SIGINT'))
