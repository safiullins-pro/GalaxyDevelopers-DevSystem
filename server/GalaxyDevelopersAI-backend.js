#!/usr/bin/env node
const { executeCommandSecure, authenticateToken, validateInput, validationSchemas, rateLimiters } = require('../McKinsey_Transformation/Horizon_1_Simplify/Week1_Security_Fixes.js');

const express = require('express');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const KeyRotator = require('./GalaxyDevelopersAI-key-rotator');
const { spawn } = require('child_process'); // execSync REMOVED FOREVER - LAZARUS AUDIT FIX
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const crypto = require('crypto');
const os = require('os');

// Загружаем конфигурацию Gemini
const geminiConfig = JSON.parse(fs.readFileSync(path.join(__dirname, 'gemini-config.json'), 'utf8'));

// Настоящие логи вместо заглушек
const log = console.log;
const debug = console.debug;
const info = console.info;
const error = console.error;

const app = express();

const helmet = require('helmet');
const cors = require('cors');

// Security headers
app.use(helmet());
app.use(cors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    credentials: true
}));

app.use(express.json({ limit: '50mb' }));

const keyRotator = new KeyRotator();
const MEMORY_API_URL = 'http://127.0.0.1:37778';
let memoryAPIAvailable = false;

const startMemoryAPI = () => {
  const memoryProcess = spawn('/opt/homebrew/bin/python3', [path.join(__dirname, '..', 'memory', 'memory_api.py')], { detached: false, stdio: 'inherit' });
  memoryProcess.on('error', (err) => error('Failed to start Memory API:', err.message));
  setTimeout(async () => {
    try {
      const response = await axios.get(`${MEMORY_API_URL}/health`);
      if (response.data.status === 'healthy') {
        memoryAPIAvailable = true;
        error('✅ Memory API is running on port 37778');
      }
    } catch (err) {
      error('⚠️ Memory API not available, running without memory');
    }
  }, 2000);
};

startMemoryAPI();

app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

app.use(express.static(path.join(__dirname, '..')));
app.get('/', (req, res) => res.redirect('/interface/index.html'));

// =================================================================
// SEED GENERATION ENDPOINT
// =================================================================

function getClaudeChecksumSeed() {
    try {
        const credentialsPath = path.join(os.homedir(), '.claude', '.credentials.json');
        if (!fs.existsSync(credentialsPath)) {
            return { error: 'Claude credentials not found', checksum: null, seed: null };
        }

        const credsContent = fs.readFileSync(credentialsPath, 'utf8');
        const creds = JSON.parse(credsContent);
        const accessToken = creds?.claudeAiOauth?.accessToken;

        if (!accessToken) {
            return { error: 'Invalid Claude credentials format', checksum: null, seed: null };
        }

        const checksum = accessToken.slice(-12);
        const hash = crypto.createHash('sha256').update(checksum).digest('hex');
        const seed = parseInt(hash.substring(0, 8), 16) % 1000000;

        return { checksum, seed };

    } catch (e) {
        error('Error extracting Claude checksum:', e.message);
        return { error: e.message, checksum: null, seed: null };
    }
}

app.get('/api/get-seed', (req, res) => {
    const seedData = getClaudeChecksumSeed();
    if (seedData.error) {
        return res.status(500).json(seedData);
    }
    res.json(seedData);
});


// =================================================================
// TOOL DEFINITIONS
// =================================================================

const tools = [
  {
    functionDeclarations: [
      {
        name: 'run_shell_command',
        description: 'Executes a shell command and returns the output.',
        parameters: {
          type: "object",
          properties: {
            command: { type: "string", description: 'The command to execute.' },
          },
          required: ['command'],
        },
      },
      {
        name: 'read_file',
        description: 'Reads the content of a file.',
        parameters: {
          type: "object",
          properties: {
            absolute_path: { type: "string", description: 'The absolute path to the file.' },
          },
          required: ['absolute_path'],
        },
      },
      {
        name: 'write_file',
        description: 'Writes content to a file.',
        parameters: {
          type: "object",
          properties: {
            file_path: { type: "string", description: 'The absolute path to the file.' },
            content: { type: "string", description: 'The content to write.' },
          },
          required: ['file_path', 'content'],
        },
      },
    ],
  },
];

const toolFunctions = {
  run_shell_command: async ({ command }) => {
    try {
      log(`SHELL EXEC: ${command}`);
      const output = await executeCommandSecure(command, { encoding: 'utf8', stdio: 'pipe' });
      return { result: { output } };
    } catch (e) {
      log(`SHELL ERROR: ${command}`, e);
      return { result: { error: e.message, stdout: e.stdout, stderr: e.stderr } };
    }
  },
  read_file: ({ absolute_path }) => {
    try {
      log(`FS READ: ${absolute_path}`);
      if (fs.existsSync(absolute_path)) {
        const content = fs.readFileSync(absolute_path, 'utf8');
        return { result: { content } };
      } else {
        return { result: { error: `File not found: ${absolute_path}` } };
      }
    } catch (e) {
      log(`FS READ ERROR: ${absolute_path}`, e);
      return { result: { error: e.message } };
    }
  },
  write_file: ({ file_path, content }) => {
    try {
      log(`FS WRITE: ${file_path}`);
      fs.writeFileSync(file_path, content, 'utf8');
      return { result: { success: true } };
    } catch (e) {
      log(`FS WRITE ERROR: ${file_path}`, e);
      return { result: { error: e.message } };
    }
  },
};

// =================================================================
// CHAT ENDPOINT WITH FUNCTION CALLING LOOP
// =================================================================

app.post('/chat', async (req, res) => {
  let apiKey;
  try {
    const { prompt, instruction, context, model, temperature, topK, topP, maxTokens, useMemory, history } = req.body;

    if (!prompt) {
      return res.status(400).json({ error: 'No prompt provided' });
    }

    apiKey = keyRotator.getNextValidKey();
    const genAI = new GoogleGenerativeAI(apiKey);

    const config = geminiConfig.forge_mode; // Always use forge_mode for now
    const selectedModel = model || 'gemini-1.5-pro-latest';

    const genModel = genAI.getGenerativeModel({
      model: selectedModel,
      tools: tools,
      generationConfig: {
        temperature: temperature !== undefined ? temperature : config.temperature,
        topK: topK !== undefined ? topK : config.topK,
        topP: topP !== undefined ? topP : config.topP,
        maxOutputTokens: maxTokens || config.maxOutputTokens,
      }
    });

    const chat = genModel.startChat({ history: history || [] });

    const fullPrompt = [
      instruction ? `INSTRUCTION:\n${instruction}\n` : '',
      context ? `CONTEXT:\n${context}\n` : '',
      `REQUEST:\n${prompt}`
    ].filter(Boolean).join('\n');

    let result = await chat.sendMessage(fullPrompt);

    // Function calling loop with protection
    let iterations = 0;
    const maxIterations = 10;
    const startTime = Date.now();
    const timeout = 30000; // 30 seconds
    
    while (iterations < maxIterations && (Date.now() - startTime) < timeout) {
      const call = result.response.functionCalls()?.[0];
      if (!call) {
        // No more function calls, break the loop and return the text response
        break;
      }
      
      iterations++;

      log(`TOOL CALL: ${call.name}`, call.args);
      const toolResult = toolFunctions[call.name](call.args);
      log(`TOOL RESULT:`, toolResult);

      result = await chat.sendMessage(JSON.stringify([
        {
          functionResponse: {
            name: call.name,
            response: toolResult,
          },
        },
      ]));
    }
    
    // Check if loop ended due to timeout or max iterations
    if (iterations >= maxIterations) {
      log('⚠️ Function calling loop stopped: max iterations reached');
    }
    if ((Date.now() - startTime) >= timeout) {
      log('⚠️ Function calling loop stopped: timeout reached');
    }

    const textResponse = result.response.text();

    if (useMemory && memoryAPIAvailable) {
        try {
            log('💾 Saving to memory...');
            await axios.post(`${MEMORY_API_URL}/save_conversation`, {
                user_message: prompt,
                ai_response: textResponse,
                context: { instruction, context },
                model: selectedModel,
            });
            log('✅ Saved to memory');
        } catch (err) {
            error('❌ Failed to save to memory:', err.message);
        }
    }

    res.json({ response: textResponse });

  } catch (err) {
    error('API Error:', err.message, err.stack);
    if (err.message?.includes('quota') && apiKey) {
      keyRotator.markKeyAsExhausted(apiKey);
      error('Key exhausted, will use next one on next request');
    }
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 37777;
app.listen(PORT, '127.0.0.1', () => {
  error(`Backend running on http://127.0.0.1:${PORT}`);
});

process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));
