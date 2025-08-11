#!/usr/bin/env node

const { GoogleGenAI } = require('@google/genai');

const models = [
  'gemini-1.5-pro-latest',
  'gemini-1.5-pro-002',
  'gemini-1.5-pro',
  'gemini-1.5-flash-latest',
  'gemini-1.5-flash',
  'gemini-1.5-flash-002',
  'gemini-1.5-flash-8b',
  'gemini-2.5-pro',
  'gemini-2.5-flash',
  'gemini-2.0-flash-exp',
  'gemini-2.0-flash',
  'gemini-2.0-flash-lite',
  'gemini-2.0-pro-exp',
  'gemini-exp-1206',
  'gemini-2.0-flash-thinking-exp',
  'learnlm-2.0-flash-experimental'
];

const genAI = new GoogleGenAI({ apiKey: 'AIzaSyCW3xoPx80zVg77Yj8XozZTf5QrL9M_56U' });

async function testModel(modelName) {
  try {
    const result = await genAI.models.generateContent({
      model: `models/${modelName}`,
      contents: [{
        parts: [{ text: 'Say hi' }],
        role: 'user'
      }],
      generationConfig: {
        maxOutputTokens: 10,
      }
    });
    
    if (result && result.candidates) {
      return '✓';
    }
    return '✗ No response';
  } catch (e) {
    const msg = e.message || String(e);
    if (msg.includes('429') || msg.includes('quota')) {
      return '⚠️ Quota';
    }
    if (msg.includes('not found')) {
      return '✗ Not found';
    }
    return '✗ ' + msg.substring(0, 30);
  }
}

async function testAll() {
  console.log('Testing models for generateContent support:\n');
  
  for (const model of models) {
    const result = await testModel(model);
    console.log(`${result} ${model}`);
    await new Promise(r => setTimeout(r, 300));
  }
}

testAll();