#!/bin/bash
cd ~/documents/github/japan-trip-ios
/opt/homebrew/bin/claude -p "$(cat poller/AGENT.md)" \
  --allowedTools "mcp__claude_ai_Gmail__search_threads,mcp__claude_ai_Gmail__get_thread,mcp__claude_ai_Gmail__list_labels,mcp__claude_ai_Gmail__list_drafts,mcp__claude_ai_Supabase__execute_sql,mcp__claude_ai_Supabase__list_tables,mcp__claude_ai_Supabase__apply_migration,Edit,Write,Read" \
  >> poller/poller.log 2>&1
