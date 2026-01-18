#!/bin/bash

# macOS notification when Claude is waiting for input
osascript -e 'display notification "Claude is waiting for your input" with title "Claude Code" sound name "Ping"'

# Terminal bell as backup
echo -e "\a"