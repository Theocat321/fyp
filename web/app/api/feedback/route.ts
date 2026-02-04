import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Get Python backend URL from environment
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.PY_BACKEND_URL;

    if (!backendUrl) {
      // If no backend configured, log and return success to not block user
      console.warn('[Feedback] No backend configured, feedback not persisted:', body);
      return NextResponse.json({ ok: true, stored: false, warning: 'no_backend' }, { status: 202 });
    }

    // Forward to Python backend
    const response = await fetch(`${backendUrl}/api/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': request.headers.get('user-agent') || 'Next.js',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });

  } catch (error) {
    console.error('[Feedback API] Error:', error);
    return NextResponse.json(
      { ok: false, error: 'feedback_proxy_failed' },
      { status: 500 }
    );
  }
}
