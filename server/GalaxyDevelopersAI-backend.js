#!/usr/bin/env node

const express = require('express');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const KeyRotator = require('./GalaxyDevelopersAI-key-rotator');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Автоматическая очистка macOS метаданных при запуске
try {
  execSync('find /Volumes/Z7S/development/GalaxyDevelopers/DevSystem -name "._*" -delete 2>/dev/null');
} catch (e) {
  // Игнорируем ошибки очистки
}

// Отключаем все логи
console.log = () => {};
console.debug = () => {};
console.info = () => {};

// Оставляем только ошибки
const error = console.error;

const app = express();
app.use(express.json({ limit: '50mb' }));

// Initialize key rotator
const keyRotator = new KeyRotator();

// Webhook state for iTerm2
let lastScreenshot = null;
let screenshotPending = false;

// CORS для локальной разработки
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
});

// Статические файлы
app.use(express.static(path.join(__dirname, '..')));

// Redirect root to web interface
app.get('/', (req, res) => {
  res.redirect('/interface/GalaxyDevelopersAI-web.html');
});

// Endpoint для получения списка моделей
app.get('/models', (req, res) => {
  const models = require('../resources/available-models.json');
  res.json(models);
});

// Screenshot endpoint
app.post('/screenshot', (req, res) => {
  try {
    const timestamp = new Date().toISOString().replace(/:/g, '-').substring(0, 19);
    const filename = `screenshot-${timestamp}.png`;
    const screenshotPath = path.join(__dirname, '..', 'connectors', 'ScreenShots', filename);
    
    // Ensure directory exists
    if (!fs.existsSync(path.join(__dirname, '..', 'connectors', 'ScreenShots'))) {
      fs.mkdirSync(path.join(__dirname, '..', 'connectors', 'ScreenShots'), { recursive: true });
    }
    
    // Take screenshot using screencapture command
    execSync(`screencapture -x "${screenshotPath}"`);
    
    // Set webhook state for iTerm2
    lastScreenshot = filename;
    screenshotPending = true;
    
    error(`Screenshot saved: ${filename}`);
    res.json({ success: true, filename });
  } catch (err) {
    error('Screenshot error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// Webhook endpoints for iTerm2
app.get('/webhook/status', (req, res) => {
  res.json({
    new_screenshot: screenshotPending,
    filename: lastScreenshot
  });
});

app.post('/webhook/clear', (req, res) => {
  screenshotPending = false;
  res.json({ success: true });
});

// Auto-insert screenshot for Claude terminals
app.post('/webhook/notify-claude', (req, res) => {
  const { filename } = req.body;
  if (filename) {
    lastScreenshot = filename;
    screenshotPending = true;
    res.json({ success: true, message: 'Claude terminals will be notified' });
  } else {
    res.status(400).json({ error: 'No filename provided' });
  }
});

// Element selector endpoint для отправки в терминал
app.post('/element-selected', (req, res) => {
  const data = req.body;
  if (data) {
    // Выводим полученные данные в консоль чтобы Claude их увидел
    error('=== ELEMENT DATA FOR CLAUDE ===');
    error(JSON.stringify(data, null, 2));
    error('=== END ELEMENT DATA ===');
    res.json({ success: true, message: 'Element sent to terminal' });
  } else {
    res.status(400).json({ error: 'No data provided' });
  }
});

// MCP endpoint for AI agents to trigger screenshot
app.get('/mcp/screenshot', (req, res) => {
  try {
    const timestamp = new Date().toISOString().replace(/:/g, '-').substring(0, 19);
    const filename = `mcp-screenshot-${timestamp}.png`;
    const screenshotPath = path.join(__dirname, '..', 'connectors', 'ScreenShots', filename);
    
    // Ensure directory exists
    if (!fs.existsSync(path.join(__dirname, '..', 'connectors', 'ScreenShots'))) {
      fs.mkdirSync(path.join(__dirname, '..', 'connectors', 'ScreenShots'), { recursive: true });
    }
    
    // Take screenshot
    execSync(`screencapture -x "${screenshotPath}"`);
    
    error(`MCP Screenshot saved: ${filename}`);
    res.json({ 
      success: true, 
      filename,
      path: screenshotPath,
      message: `Screenshot saved to ScreenShots/${filename}`
    });
  } catch (err) {
    error('MCP Screenshot error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// Один endpoint - и всё
app.post('/chat', async (req, res) => {
  try {
    const { prompt, instruction, context, model } = req.body;
    
    if (!prompt) {
      return res.status(400).json({ error: 'No prompt provided' });
    }

    // Каждый раз новый клиент и новый ключ - никакой памяти
    let apiKey;
    try {
      apiKey = keyRotator.getNextValidKey();
      error(`Using key: ${apiKey.substring(0, 10)}...${apiKey.substring(apiKey.length - 4)}`);
    } catch (e) {
      // Fallback to env key if no valid keys
      apiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
      if (!apiKey) {
        return res.status(500).json({ error: 'No API keys available' });
      }
    }
    
    const genAI = new GoogleGenerativeAI(apiKey);

    // Собираем полный промпт
    const fullPrompt = [
      instruction ? `INSTRUCTION:\n${instruction}\n` : '',
      context ? `CONTEXT:\n${context}\n` : '',
      `REQUEST:\n${prompt}`
    ].filter(Boolean).join('\n');

    // Используем выбранную модель или дефолтную
    const selectedModel = model || 'gemini-1.5-flash';
    error(`Using model: ${selectedModel}`);
    
    // Для streaming ответов - ВРЕМЕННО ОТКЛЮЧЕНО из-за ошибки API
    // TODO: Исправить когда Google починит generateContentStream
    /*
    if (req.body.stream) {
      // Streaming пока не работает с текущей версией API
    }
    */
    
    // Обычный режим - отправляем и забываем
    const genModel = genAI.getGenerativeModel({ model: selectedModel });
    const result = await genModel.generateContent(fullPrompt);
    
    // Проверяем что есть ответ
    const response = result.response.text();

    // Отдаем ответ и разрываем соединение
    res.json({ response });
    
    // Убиваем все ссылки
    delete genAI;
    delete model;
    delete result;

  } catch (err) {
    error('API Error:', err.message);
    error('Full error:', err);
    
    // If quota exceeded, mark key and retry with next one
    if (err.message && (err.message.includes('quota') || err.message.includes('limit'))) {
      keyRotator.markKeyAsExhausted(apiKey);
      error('Key exhausted, will use next one on next request');
    }
    
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 37777;
app.listen(PORT, '127.0.0.1', () => {
  error(`Backend running on http://127.0.0.1:${PORT}`);
  error('POST /chat - {prompt, instruction, context}');
});

// Graceful shutdown
process.on('SIGTERM', () => process.exit(0));
process.on('SIGINT', () => process.exit(0));