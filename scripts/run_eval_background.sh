#!/bin/bash
# Run auto_eval in background and save output

echo "🚀 Starting auto_eval in background..."
echo "📝 Output will be saved to eval_run.log"
echo ""

source venv/bin/activate
nohup python3 scripts/auto_eval.py "$@" > eval_run.log 2>&1 &
PID=$!

echo "✓ Process started (PID: $PID)"
echo ""
echo "Monitor progress:"
echo "  tail -f eval_run.log"
echo ""
echo "Check if running:"
echo "  ps aux | grep $PID"
echo ""
echo "Kill if needed:"
echo "  kill $PID"
