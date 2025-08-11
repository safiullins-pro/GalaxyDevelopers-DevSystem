#\!/bin/bash
echo 'Для автоматической вставки скриншотов в Claude:'
echo '1. Откройте iTerm2 Preferences (⌘,)'
echo '2. General → Magic'  
echo '3. Включите Enable Python API'
echo '4. Перезапустите iTerm2'
echo '5. Запустите: python3 connectors/iterm2-integration.py'
echo ''
echo 'Или сделать скриншот вручную и отправить в Claude:'
./scripts/send-to-claude.sh
