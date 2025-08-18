
        set startTime to current date
        set targetMinutes to 10
        set windowID to "196"
        
        repeat
            set currentTime to current date
            set elapsedSeconds to (currentTime - startTime)
            set elapsedMinutes to elapsedSeconds div 60
            set remainingSeconds to elapsedSeconds mod 60
            
            tell application "iTerm2"
                repeat with w in windows
                    if id of w is windowID then
                        tell current session of w
                            -- Отправляем пустую строку чтобы пробудить процесс
                            write text ""
                        end tell
                        exit repeat
                    end if
                end repeat
            end tell
            
            if elapsedMinutes >= targetMinutes then
                exit repeat
            end if
            
            delay 30
        end repeat
        