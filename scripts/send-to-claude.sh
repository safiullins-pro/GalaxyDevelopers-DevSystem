#!/bin/bash

# Send screenshot directly to Claude terminal

SCREENSHOT_PATH="$1"
if [ -z "$SCREENSHOT_PATH" ]; then
    # Take new screenshot if no path provided
    TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
    SCREENSHOT_PATH="/Volumes/Z7S/development/GalaxyDevelopers/DevSystem/connectors/ScreenShots/direct-$TIMESTAMP.png"
    screencapture -x "$SCREENSHOT_PATH"
fi

# Find iTerm2 window with Claude
osascript <<EOF
tell application "iTerm"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                set sessionName to name of s
                set sessionPath to path of s
                
                -- Check if this is a Claude session in DevSystem
                if sessionPath contains "DevSystem" then
                    if sessionName contains "claude" or sessionName contains "Claude" then
                        -- Found Claude terminal
                        select s
                        tell s
                            write text "# Screenshot: $SCREENSHOT_PATH"
                            write text "# Viewing screenshot..."
                            -- Send the actual screenshot viewing command
                            write text "open '$SCREENSHOT_PATH'"
                        end tell
                        return "Screenshot sent to Claude terminal"
                    end if
                end if
            end repeat
        end repeat
    end repeat
    
    -- If no Claude terminal found, notify all DevSystem terminals
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                set sessionPath to path of s
                if sessionPath contains "DevSystem" then
                    tell s
                        write text "# New screenshot available: $SCREENSHOT_PATH"
                    end tell
                end if
            end repeat
        end repeat
    end repeat
end tell
EOF

echo "Screenshot sent: $SCREENSHOT_PATH"