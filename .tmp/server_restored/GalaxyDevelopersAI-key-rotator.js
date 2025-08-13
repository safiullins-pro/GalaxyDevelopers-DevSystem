#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { GoogleGenAI } = require('@google/genai');

const KEYS_FILE = path.join(__dirname, '..', '.galaxydevelopers-ai-keys');
const STATE_FILE = path.join(__dirname, '..', '.galaxydevelopers-ai-key-state.json');

class KeyRotator {
  constructor() {
    this.keys = this.loadKeys();
    this.state = this.loadState();
    this.currentIndex = this.state.currentIndex || 0;
    this.keyStatus = this.state.keyStatus || {};
  }

  loadKeys() {
    try {
      const content = fs.readFileSync(KEYS_FILE, 'utf-8');
      return content.split('\n').filter(k => k.trim());
    } catch (e) {
      console.error('No keys file found');
      return [];
    }
  }

  loadState() {
    try {
      const content = fs.readFileSync(STATE_FILE, 'utf-8');
      return JSON.parse(content);
    } catch (e) {
      return { currentIndex: 0, keyStatus: {} };
    }
  }

  saveState() {
    fs.writeFileSync(STATE_FILE, JSON.stringify({
      currentIndex: this.currentIndex,
      keyStatus: this.keyStatus,
      lastUpdate: new Date().toISOString()
    }, null, 2));
  }

  async validateKey(key) {
    try {
      const genAI = new GoogleGenAI({ apiKey: key });
      const result = await genAI.models.generateContent({
        model: 'models/gemini-1.5-flash',
        contents: [{
          parts: [{ text: 'Hi' }],
          role: 'user'
        }],
        generationConfig: {
          maxOutputTokens: 1,
        }
      });
      
      if (result && result.candidates) {
        return { valid: true, error: null, status: 'ACTIVE' };
      }
      return { valid: false, error: 'No response' };
    } catch (e) {
      const errorMsg = e.message || String(e);
      
      // Check for 429 rate limit
      if (errorMsg.includes('429') || errorMsg.includes('Resource has been exhausted')) {
        // Check if it's per-key or per-account limit
        if (errorMsg.includes('per-minute') || errorMsg.includes('per-day')) {
          return { valid: true, error: 'RATE_LIMITED', cooldown: 60000 }; // 1 minute cooldown
        }
        return { valid: true, error: 'QUOTA_EXCEEDED', cooldown: 86400000 }; // 24 hour cooldown
      }
      
      // Check for suspended consumer
      if (errorMsg.includes('CONSUMER_SUSPENDED') || errorMsg.includes('has been suspended')) {
        return { valid: false, error: 'SUSPENDED' };
      }
      
      // Check for invalid key
      if (errorMsg.includes('API key not valid') || errorMsg.includes('403')) {
        return { valid: false, error: 'INVALID_KEY' };
      }
      
      // Check for quota exceeded
      if (errorMsg.includes('quota') || errorMsg.includes('limit')) {
        return { valid: true, error: 'QUOTA_EXCEEDED', cooldown: 86400000 };
      }
      
      return { valid: false, error: errorMsg.substring(0, 100) };
    }
  }

  async validateAllKeys() {
    console.log(`Validating ${this.keys.length} keys...`);
    
    for (let i = 0; i < this.keys.length; i++) {
      const key = this.keys[i];
      const maskedKey = key.substring(0, 10) + '...' + key.substring(key.length - 4);
      
      process.stdout.write(`[${i+1}/${this.keys.length}] ${maskedKey}: `);
      
      const result = await this.validateKey(key);
      this.keyStatus[key] = {
        valid: result.valid,
        error: result.error,
        lastCheck: new Date().toISOString()
      };
      
      if (result.valid) {
        if (result.error === 'QUOTA_EXCEEDED') {
          console.log('✓ Valid (quota exceeded)');
        } else {
          console.log('✓ Valid');
        }
      } else {
        console.log(`✗ Invalid (${result.error})`);
      }
      
      // Small delay to avoid rate limiting
      await new Promise(r => setTimeout(r, 500));
    }
    
    this.saveState();
    
    const validKeys = Object.keys(this.keyStatus).filter(k => this.keyStatus[k].valid);
    console.log(`\nSummary: ${validKeys.length}/${this.keys.length} keys are valid`);
  }

  getNextValidKey() {
    const validKeys = this.keys.filter(k => 
      !this.keyStatus[k] || this.keyStatus[k].valid
    );
    
    if (validKeys.length === 0) {
      throw new Error('No valid keys available');
    }
    
    // Rotate through valid keys
    this.currentIndex = (this.currentIndex + 1) % validKeys.length;
    const selectedKey = validKeys[this.currentIndex];
    
    this.saveState();
    return selectedKey;
  }

  getCurrentKey() {
    const validKeys = this.keys.filter(k => 
      !this.keyStatus[k] || this.keyStatus[k].valid
    );
    
    if (validKeys.length === 0) {
      throw new Error('No valid keys available');
    }
    
    return validKeys[this.currentIndex % validKeys.length];
  }

  markKeyAsExhausted(key) {
    this.keyStatus[key] = {
      valid: true,
      error: 'QUOTA_EXCEEDED',
      lastCheck: new Date().toISOString()
    };
    this.saveState();
  }
}

// CLI usage
if (require.main === module) {
  const rotator = new KeyRotator();
  const command = process.argv[2];
  
  if (command === 'validate') {
    rotator.validateAllKeys().catch(console.error);
  } else if (command === 'next') {
    try {
      const key = rotator.getNextValidKey();
      console.log(key);
    } catch (e) {
      console.error(e.message);
      process.exit(1);
    }
  } else if (command === 'current') {
    try {
      const key = rotator.getCurrentKey();
      console.log(key);
    } catch (e) {
      console.error(e.message);
      process.exit(1);
    }
  } else {
    console.log('Usage:');
    console.log('  node GalaxyDevelopersAI-key-rotator.js validate  - Validate all keys');
    console.log('  node GalaxyDevelopersAI-key-rotator.js next      - Get next valid key');
    console.log('  node GalaxyDevelopersAI-key-rotator.js current   - Get current key');
  }
}

module.exports = KeyRotator;