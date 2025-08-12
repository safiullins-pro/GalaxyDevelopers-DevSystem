#!/usr/bin/env node

/**
 * ТЕСТИРОВАНИЕ GEMINI ФУНКЦИЙ
 * Запуск: node test-gemini.js
 */

const GeminiFunctions = require('./gemini-functions');
const KeyRotator = require('./GalaxyDevelopersAI-key-rotator'); // Импортируем ротатор

async function testGemini() {
  // --- ИЗМЕНЕНИЕ: Получаем ключ через ротатор ---
  let apiKey;
  try {
    const keyRotator = new KeyRotator();
    apiKey = keyRotator.getNextValidKey();
    console.log(`🔑 Using API key from rotator: ${apiKey.substring(0, 10)}...\n`);
  } catch (e) {
    console.error('❌ ERROR: Could not get API key from rotator. Make sure .galaxydevelopers-ai-keys file exists.');
    console.error(e.message);
    process.exit(1);
  }
  // --- КОНЕЦ ИЗМЕНЕНИЯ ---
  
  if (!apiKey) {
    console.error('❌ ERROR: No API key available!');
    process.exit(1);
  }
  
  console.log('🚀 Starting Gemini Functions Test...\n');
  
  const gemini = new GeminiFunctions(apiKey);
  
  // Тест 1: Forge Mode (детерминированный)
  console.log('📝 Test 1: FORGE MODE (temperature=0)');
  console.log('=========================================');
  
  const forgePrompt = 'What is 2+2? Answer with only the number.';
  
  try {
    const response1 = await gemini.generateForgeMode(forgePrompt);
    console.log('Response 1:', response1);
    
    const response2 = await gemini.generateForgeMode(forgePrompt);
    console.log('Response 2:', response2);
    
    const match = response1 === response2;
    console.log(`Deterministic match: ${match ? '✅ YES' : '❌ NO'}\n`);
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  // Тест 2: Custom настройки
  console.log('📝 Test 2: CUSTOM SETTINGS');
  console.log('=========================================');
  
  try {
    const customResponse = await gemini.generateCustom(
      'Write one word: the capital of France',
      {
        temperature: 0.0,
        topK: 1,
        topP: 1.0,
        maxOutputTokens: 10
      }
    );
    console.log('Custom response:', customResponse, '\n');
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  // Тест 3: Подсчет токенов
  console.log('📝 Test 3: TOKEN COUNTING');
  console.log('=========================================');
  
  try {
    const text = 'This is a test prompt to count tokens.';
    const tokens = await gemini.countTokens(text);
    console.log(`Text: "${text}"`);
    console.log(`Tokens: ${tokens}\n`);
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  // Тест 4: Проверка моделей
  console.log('📝 Test 4: MODEL AVAILABILITY');
  console.log('=========================================');
  
  const modelsToTest = [
    'gemini-2.5-flash',
    'gemini-2.5-pro',
    'gemini-2.0-flash',
    'gemini-1.5-flash'
  ];
  
  for (const model of modelsToTest) {
    await gemini.testModel(model);
  }
  
  console.log('\n');
  
  // Тест 5: Сохранение и воспроизведение сессии
  console.log('📝 Test 5: SESSION REPRODUCIBILITY');
  console.log('=========================================');
  
  try {
    const sessionPrompt = 'What is the first letter of alphabet? Answer with one letter only.';
    const sessionId = `test-${Date.now()}`;
    
    const response = await gemini.generateForgeMode(sessionPrompt);
    
    // Сохраняем сессию
    gemini.saveSession(sessionId, sessionPrompt, response, {
      temperature: 0.0,
      topK: 1,
      topP: 1.0
    });
    
    // Воспроизводим
    const replay = await gemini.replaySession(sessionId);
    
    console.log('Original:', replay.original);
    console.log('Replay:', replay.replay);
    console.log(`Match: ${replay.match ? '✅ EXACT' : '❌ DIFFERENT'}\n`);
  } catch (error) {
    console.error('Error:', error.message);
  }

  // Тест 6: Проверка параметра Seed
  console.log('📝 Test 6: SEED PARAMETER CHECK');
  console.log('=========================================');
  
  try {
    const seedPrompt = 'Generate a random short story about a robot who discovers music.';
    const seedValue = 42; // Static seed for reproducibility
    
    console.log(`Using static seed: ${seedValue} and temperature: 0.9`);

    const response1 = await gemini.generateCustom(
      seedPrompt,
      {
        temperature: 0.9,
        seed: seedValue,
        maxOutputTokens: 100
      }
    );
    
    const response2 = await gemini.generateCustom(
      seedPrompt,
      {
        temperature: 0.9,
        seed: seedValue,
        maxOutputTokens: 100
      }
    );
    
    console.log('Response 1:', response1.substring(0, 90) + '...');
    console.log('Response 2:', response2.substring(0, 90) + '...');

    const seedMatch = response1 === response2;
    console.log(`Responses with the same seed match: ${seedMatch ? '✅ YES' : '❌ NO'}\n`);

  } catch (error) {
    console.error('Error during seed test:', error.message);
  }
  
  console.log('✅ Tests completed!');
}

// Запускаем тесты
testGemini().catch(console.error);