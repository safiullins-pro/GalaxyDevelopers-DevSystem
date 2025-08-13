/**
 * РЕАЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С GEMINI API
 * Без заглушек, с полными настройками
 */

const { GoogleGenerativeAI } = require('@google/generative-ai');
const fs = require('fs');
const path = require('path');

// Загружаем конфигурацию
const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'gemini-config.json'), 'utf8'));

class GeminiFunctions {
  constructor(apiKey) {
    if (!apiKey) {
      throw new Error('API key is required!');
    }
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.config = config;
  }

  /**
   * Создать модель с полными настройками
   */
  createModel(modelName = 'gemini-2.5-flash', customConfig = {}) {
    let generationConfig = {
      ...this.config.default_generation_config,
      ...customConfig
    };

    // Удаляем seed если он undefined, чтобы API не ругался
    if (generationConfig.seed === undefined) {
      delete generationConfig.seed;
    }

    console.log('Creating model with config:', generationConfig);
    
    return this.genAI.getGenerativeModel({
      model: modelName,
      generationConfig: generationConfig,
      safetySettings: [
        {
          category: 'HARM_CATEGORY_HARASSMENT',
          threshold: 'BLOCK_NONE'
        },
        {
          category: 'HARM_CATEGORY_HATE_SPEECH',
          threshold: 'BLOCK_NONE'
        },
        {
          category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
          threshold: 'BLOCK_NONE'
        },
        {
          category: 'HARM_CATEGORY_DANGEROUS_CONTENT',
          threshold: 'BLOCK_NONE'
        }
      ]
    });
  }

  /**
   * Генерация в режиме FORGE (детерминированный)
   */
  async generateForgeMode(prompt, modelName = 'gemini-2.5-pro') {
    const model = this.createModel(modelName, this.config.forge_mode);
    
    console.log(`FORGE MODE: Generating with ${modelName}`);
    console.log(`Settings: temp=0, topK=1, topP=1.0`);
    
    const result = await model.generateContent(prompt);
    return result.response.text();
  }

  /**
   * Генерация в креативном режиме
   */
  async generateCreativeMode(prompt, modelName = 'gemini-2.5-flash') {
    const model = this.createModel(modelName, this.config.creative_mode);
    
    console.log(`CREATIVE MODE: Generating with ${modelName}`);
    console.log(`Settings: temp=0.7, topK=40, topP=0.95`);
    
    const result = await model.generateContent(prompt);
    return result.response.text();
  }

  /**
   * Генерация с кастомными настройками
   */
  async generateCustom(prompt, options = {}) {
    const {
      model: modelName = 'gemini-2.5-flash',
      temperature = 0.0,
      topK = 1,
      topP = 1.0,
      maxOutputTokens = 8192,
      stopSequences = [],
      seed = undefined
    } = options;

    const model = this.createModel(modelName, {
      temperature,
      topK,
      topP,
      maxOutputTokens,
      stopSequences,
      seed
    });

    console.log(`CUSTOM MODE: Generating with ${modelName}`);
    console.log(`Settings: temp=${temperature}, topK=${topK}, topP=${topP}, seed=${seed}`);
    
    const result = await model.generateContent(prompt);
    return result.response.text();
  }

  /**
   * Потоковая генерация (streaming)
   */
  async *generateStream(prompt, modelName = 'gemini-2.5-flash') {
    const model = this.createModel(modelName, this.config.forge_mode);
    
    console.log(`STREAM MODE: Generating with ${modelName}`);
    
    const result = await model.generateContentStream(prompt);
    
    for await (const chunk of result.stream) {
      yield chunk.text();
    }
  }

  /**
   * Мультимодальная генерация (с изображениями)
   */
  async generateWithImage(prompt, imagePath, modelName = 'gemini-2.5-flash') {
    const model = this.createModel(modelName, this.config.forge_mode);
    
    // Читаем изображение
    const imageBuffer = fs.readFileSync(imagePath);
    const base64Image = imageBuffer.toString('base64');
    
    const parts = [
      { text: prompt },
      {
        inlineData: {
          mimeType: 'image/jpeg',
          data: base64Image
        }
      }
    ];
    
    console.log(`MULTIMODAL MODE: Generating with ${modelName} and image`);
    
    const result = await model.generateContent(parts);
    return result.response.text();
  }

  /**
   * Подсчет токенов
   */
  async countTokens(prompt, modelName = 'gemini-2.5-flash') {
    const model = this.createModel(modelName);
    
    const result = await model.countTokens(prompt);
    
    console.log(`Token count for ${modelName}: ${result.totalTokens}`);
    
    return result.totalTokens;
  }

  /**
   * Проверка доступности модели
   */
  async testModel(modelName) {
    try {
      const model = this.createModel(modelName);
      const result = await model.generateContent('Hello');
      console.log(`✅ Model ${modelName} is available`);
      return true;
    } catch (error) {
      console.error(`❌ Model ${modelName} failed:`, error.message);
      return false;
    }
  }

  /**
   * Получить список всех доступных моделей
   */
  async listAvailableModels() {
    const modelsConfig = JSON.parse(
      fs.readFileSync(path.join(__dirname, '..', 'resources', 'available-models.json'), 'utf8')
    );
    
    const results = [];
    
    for (const model of modelsConfig.models) {
      const available = await this.testModel(model.name);
      results.push({
        ...model,
        available
      });
    }
    
    return results;
  }

  /**
   * Сохранить сессию для воспроизводимости
   */
  saveSession(sessionId, prompt, response, config) {
    const session = {
      id: sessionId,
      timestamp: new Date().toISOString(),
      prompt,
      response,
      config,
      model: config.model || 'gemini-2.5-flash'
    };
    
    const sessionsPath = path.join(__dirname, 'sessions');
    if (!fs.existsSync(sessionsPath)) {
      fs.mkdirSync(sessionsPath);
    }
    
    fs.writeFileSync(
      path.join(sessionsPath, `${sessionId}.json`),
      JSON.stringify(session, null, 2)
    );
    
    console.log(`Session saved: ${sessionId}`);
    
    return session;
  }

  /**
   * Воспроизвести сессию
   */
  async replaySession(sessionId) {
    const sessionPath = path.join(__dirname, 'sessions', `${sessionId}.json`);
    
    if (!fs.existsSync(sessionPath)) {
      throw new Error(`Session ${sessionId} not found`);
    }
    
    const session = JSON.parse(fs.readFileSync(sessionPath, 'utf8'));
    
    console.log(`Replaying session ${sessionId}...`);
    console.log(`Original response length: ${session.response.length}`);
    
    const newResponse = await this.generateCustom(session.prompt, session.config);
    
    const match = newResponse === session.response;
    
    console.log(`Replay match: ${match ? '✅ EXACT' : '❌ DIFFERENT'}`);
    
    return {
      original: session.response,
      replay: newResponse,
      match
    };
  }
}

module.exports = GeminiFunctions;
