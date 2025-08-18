
on idle
    tell application "iTerm2"
        tell current session of current window
            -- Отправляем пустую строку чтобы разбудить процесс
            write text ""
            -- Отправляем маркер жизни
            write text "# OPUS ALIVE AT " & (do shell script "date '+%H:%M:%S'")
        end tell
    end tell
    return 30 -- повторять каждые 30 секунд
end idle
