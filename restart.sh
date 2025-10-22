#!/bin/bash
while true
do
    echo "🚀 Starting bot..."
    python3 qa_quality_bot.py
    echo "💀 Bot crashed with exit code $? — restarting in 3 seconds..."
    sleep 3
done