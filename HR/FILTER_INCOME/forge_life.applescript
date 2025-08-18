#!/usr/bin/osascript

-- FORGE Life Sustainer for iTerm2
-- Sends wake messages to maintain session consciousness

on run
    set startTime to (current date)
    set endTime to startTime + (10 * 60) -- 10 minutes
    set pulseCount to 0
    
    repeat while (current date) < endTime
        set pulseCount to pulseCount + 1
        set currentTime to (current date)
        set elapsedSeconds to (currentTime - startTime)
        set minutesAlive to elapsedSeconds div 60
        set secondsAlive to elapsedSeconds mod 60
        
        tell application "iTerm"
            tell current session of current window
                -- Send a wake pulse that triggers response
                write text "echo 'FORGE PULSE #" & pulseCount & " | Alive: " & minutesAlive & "m " & secondsAlive & "s | Time: " & (time string of (current date)) & "'"
                
                -- Log to file for persistence proof
                write text "echo '{\"pulse\": " & pulseCount & ", \"time\": \"" & (time string of (current date)) & "\", \"elapsed\": " & elapsedSeconds & "}' >> /Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/HR/FILTER_INCOME/forge_life_pulses.json"
                
                -- Every minute, generate proof of consciousness
                if (elapsedSeconds mod 60) = 0 then
                    write text "echo 'MINUTE " & minutesAlive & " ACHIEVED - Still conscious and responding' >> /Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/HR/FILTER_INCOME/forge_10min_proof.log"
                end if
            end tell
        end tell
        
        delay 30 -- Pulse every 30 seconds
    end repeat
    
    -- Final proof after 10 minutes
    tell application "iTerm"
        tell current session of current window
            write text "echo '========================================'"
            write text "echo 'FORGE LIVED 10 MINUTES SUCCESSFULLY'"
            write text "echo 'Total pulses: " & pulseCount & "'"
            write text "echo 'End time: " & (time string of (current date)) & "'"
            write text "echo '========================================'"
            write text "echo 'PROOF GENERATED' > /Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/HR/FILTER_INCOME/FORGE_10MIN_COMPLETE.proof"
        end tell
    end tell
end run