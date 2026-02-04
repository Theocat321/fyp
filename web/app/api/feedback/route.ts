import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Get Supabase credentials from environment
    const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseKey) {
      console.error('[Feedback] Supabase not configured');
      return NextResponse.json(
        { ok: false, error: 'supabase_not_configured' },
        { status: 500 }
      );
    }

    // Create Supabase client
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Prepare feedback row matching condensed database schema
    const feedbackRow = {
      session_id: body.session_id || null,
      participant_id: body.participant_id || null,
      participant_group: body.participant_group || null,
      scenario_id: body.scenario_id || null,
      rating_overall: body.rating_overall || null,
      rating_task_success: body.rating_task_success || null,
      rating_clarity: body.rating_clarity || null,
      rating_empathy: body.rating_empathy || null,
      rating_accuracy: body.rating_accuracy || null,
      resolved: body.resolved === 'yes' ? true : body.resolved === 'no' ? false : null,
      comments_other: body.comments_other || null,
      user_agent: body.user_agent || request.headers.get('user-agent') || null,
      page_url: body.page_url || null,
    };

    // Insert into Supabase
    const { data, error } = await supabase
      .from('support_feedback')
      .insert([feedbackRow])
      .select();

    if (error) {
      console.error('[Feedback] Supabase insert error:', error);
      return NextResponse.json(
        { ok: false, error: 'insert_failed', details: error.message },
        { status: 500 }
      );
    }

    console.log('[Feedback] Successfully stored feedback:', data);
    return NextResponse.json({ ok: true, stored: true }, { status: 200 });

  } catch (error) {
    console.error('[Feedback API] Error:', error);
    return NextResponse.json(
      { ok: false, error: 'feedback_failed' },
      { status: 500 }
    );
  }
}
