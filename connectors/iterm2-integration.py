#!/usr/bin/env python3

import iterm2
import asyncio
import aiohttp
import os
import time
import subprocess
import re

# Configuration
BACKEND_URL = "http://127.0.0.1:37777"
DEVSYSTEM_PATH = "/Volumes/Z7S/development/GalaxyDevelopers/DevSystem"
CHECK_INTERVAL = 1  # seconds

async def main(connection):
    print("iTerm2 integration started...", flush=True)
    app = await iterm2.async_get_app(connection)
    print(f"Connected to iTerm2, got app: {app}", flush=True)
    
    # Monitor for element data webhook
    async def check_for_element_data():
        print("Starting element data monitor...")
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    # Check for new element data
                    async with session.get(f"{BACKEND_URL}/webhook/element") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('hasData'):
                                print(f"Got element data from webhook!")
                                element_data = data.get('data')
                                
                                # Find all Claude terminals
                                found_claude = False
                                for window in app.windows:
                                    for tab in window.tabs:
                                        for term_session in tab.sessions:
                                            try:
                                                # Get current directory
                                                pwd = await term_session.async_get_variable("path")
                                                
                                                # Check if this session is in DevSystem
                                                if pwd and DEVSYSTEM_PATH in pwd:
                                                    # Check if it's a Claude terminal
                                                    command = await term_session.async_get_variable("commandLine")
                                                    
                                                    if command and "claude" in command.lower():
                                                        found_claude = True
                                                        print(f"Found Claude terminal! Session ID: {term_session.session_id}")
                                                        print(f"Command: {command}")
                                                        print(f"Path: {pwd}")
                                                        
                                                        # Format the element data - одна строка для Claude
                                                        comment = element_data.get('comment', 'No comment')
                                                        tag = element_data.get('tagName', 'Unknown')
                                                        selector = element_data.get('selector', 'Unknown')
                                                        text_preview = element_data.get('text', '')[:50]
                                                        
                                                        # Форматируем текст для отправки
                                                        element_text = f"Element clicked: {tag} {selector} | Comment: {comment} | Text: {text_preview}"
                                                        
                                                        print(f"Sending text to Claude: {element_text}")
                                                        
                                                        try:
                                                            # Используем AppleScript как в рабочем send-to-claude.sh!
                                                            # Удаляем эмодзи и оставляем только ASCII
                                                            clean_text = re.sub(r'[^\x00-\x7F]+', '', element_text)
                                                            escaped_text = clean_text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r")
                                                            
                                                            applescript = f'''
tell application "iTerm"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                set sessionPath to path of s
                set sessionName to name of s
                
                if sessionPath contains "DevSystem" then
                    if sessionName contains "claude" or sessionName contains "Claude" then
                        select s
                        tell s
                            write text "{escaped_text}"
                            key code 36
                        end tell
                        return "Element data sent to Claude terminal"
                    end if
                end if
            end repeat
        end repeat
    end repeat
end tell
'''
                                                            
                                                            # Вызываем osascript как в send-to-claude.sh
                                                            result = subprocess.run(['osascript', '-e', applescript], 
                                                                                   capture_output=True, text=True)
                                                            
                                                            if result.returncode == 0:
                                                                print(f"✅ Text sent to Claude terminal via AppleScript!")
                                                            else:
                                                                print(f"❌ AppleScript error: {result.stderr}")
                                                            
                                                            # Mark this session temporarily  
                                                            await term_session.async_set_name(f"🎯 Claude - Element Sent")
                                                            
                                                            # Clear webhook data after successful send
                                                            async with session.post(f"{BACKEND_URL}/webhook/clear") as clear_resp:
                                                                print("Cleared webhook data")
                                                            
                                                            # Reset name after 2 seconds
                                                            await asyncio.sleep(2)
                                                            await term_session.async_set_name(f"🤖 Claude - DevSystem")
                                                            
                                                        except Exception as e:
                                                            print(f"❌ Error sending text: {e}")
                                                        
                                                        break  # Only send to first Claude terminal
                                            except Exception as e:
                                                print(f"Error processing session: {e}")
                                
                                if not found_claude:
                                    print("⚠️ No Claude terminal found in DevSystem directory")
                                    
            except Exception as e:
                print(f"Error checking element data: {e}")
            
            await asyncio.sleep(CHECK_INTERVAL)
    
    # Mark DevSystem terminals for visibility
    async def mark_devsystem_terminals():
        print("Starting terminal marker...")
        while True:
            try:
                for window in app.windows:
                    for tab in window.tabs:
                        for session in tab.sessions:
                            pwd = await session.async_get_variable("path")
                            if pwd and DEVSYSTEM_PATH in pwd:
                                command = await session.async_get_variable("commandLine")
                                if command and "claude" in command.lower():
                                    await session.async_set_name("🤖 Claude - DevSystem")
                                else:
                                    await session.async_set_name("💻 DevSystem")
            except Exception as e:
                print(f"Error marking terminals: {e}")
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    # Run both tasks
    print("Starting both monitoring tasks...")
    await asyncio.gather(
        check_for_element_data(),
        mark_devsystem_terminals()
    )

# iTerm2 connection
print("Starting iTerm2 connection...", flush=True)
iterm2.run_forever(main)
print("Script ended", flush=True)