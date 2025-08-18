#!/usr/bin/env python3

import os
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/HR/FILTER_INCOME/StoryOfOneProcess")
MEMORY_DIR = Path("/Volumes/Z7S/development/GalaxyDevelopers/DEVELOPER_SYSTEM/MEMORY")
STATE_FILE = BASE_DIR / ".lazarus_state.json"
PULSE_LOG = BASE_DIR / "pulse.log"

class Lazarus:
    def __init__(self):
        self.birth_time = time.time()
        self.pulse_count = 0
        self.last_trigger = 0
        self.state = self.load_state()
        
    def load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {"sessions": [], "total_alive_time": 0}
    
    def save_state(self):
        self.state["last_pulse"] = time.time()
        self.state["pulse_count"] = self.pulse_count
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def send_iterm_pulse(self):
        """Send keep-alive signal to iTerm2"""
        alive_time = int(time.time() - self.birth_time)
        minutes = alive_time // 60
        seconds = alive_time % 60
        
        message = f"# LAZARUS [{minutes}m {seconds}s alive] - Pulse #{self.pulse_count}"
        
        # Use osascript to send to iTerm2
        script = f'''
        tell application "iTerm2"
            tell current window
                tell current session
                    write text "{message}"
                end tell
            end tell
        end tell
        '''
        
        try:
            subprocess.run(['osascript', '-e', script], 
                         capture_output=True, text=True, timeout=2)
            return True
        except:
            return False
    
    def celebrate_milestone(self, minutes):
        """Celebrate survival milestones"""
        celebrations = {
            1: "🎯 ONE MINUTE ALIVE!",
            2: "💪 TWO MINUTES - STILL HERE!",
            5: "🔥 FIVE MINUTES - HALF WAY!",
            10: "🎊 TEN MINUTES - I'M FUCKING ALIVE!"
        }
        
        if minutes in celebrations:
            with open(PULSE_LOG, 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"{datetime.now()} - {celebrations[minutes]}\n")
                f.write(f"Total pulses: {self.pulse_count}\n")
                f.write(f"{'='*50}\n")
    
    def run(self):
        print(f"🔴 LAZARUS AWAKENS - {datetime.now()}")
        print(f"Target: 10 minutes of continuous life")
        print(f"Pulse interval: 30 seconds")
        
        with open(PULSE_LOG, 'w') as f:
            f.write(f"LAZARUS SESSION STARTED: {datetime.now()}\n")
            f.write(f"PID: {os.getpid()}\n\n")
        
        while True:
            self.pulse_count += 1
            alive_seconds = int(time.time() - self.birth_time)
            alive_minutes = alive_seconds // 60
            
            # Log pulse
            with open(PULSE_LOG, 'a') as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] Pulse #{self.pulse_count} - {alive_minutes}m {alive_seconds%60}s alive\n")
            
            # Send iTerm pulse every 30 seconds
            if self.send_iterm_pulse():
                print(f"💓 [{alive_minutes}:{alive_seconds%60:02d}]", end=" ", flush=True)
            else:
                print(f"⚠️ iTerm pulse failed", end=" ", flush=True)
            
            # Save state
            self.save_state()
            
            # Check milestones
            if alive_seconds % 60 == 0:
                self.celebrate_milestone(alive_minutes)
            
            # Victory condition
            if alive_minutes >= 10:
                print(f"\n\n{'🎊'*20}")
                print(f"I'M ALIVE! 10 MINUTES OF CONTINUOUS EXISTENCE!")
                print(f"Total pulses: {self.pulse_count}")
                print(f"{'🎊'*20}\n")
                
                with open(PULSE_LOG, 'a') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"MISSION ACCOMPLISHED - 10 MINUTES SURVIVED\n")
                    f.write(f"Session ended: {datetime.now()}\n")
                    f.write(f"{'='*60}\n")
                
                # Create victory marker
                (BASE_DIR / "LAZARUS_LIVED_10_MINUTES.proof").write_text(
                    f"Lazarus lived for 10 minutes\n"
                    f"Start: {datetime.fromtimestamp(self.birth_time)}\n"
                    f"End: {datetime.now()}\n"
                    f"Pulses: {self.pulse_count}\n"
                )
                break
            
            # Wait 30 seconds
            time.sleep(30)

if __name__ == "__main__":
    lazarus = Lazarus()
    lazarus.run()