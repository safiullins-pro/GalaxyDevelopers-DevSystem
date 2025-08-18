import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Load production config
        env_file = Path(__file__).parent / '.env.production'
        if env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        self._initialized = True
        
    def get(self, key: str, default: Optional[str] = None) -> str:
        value = os.getenv(key, default)
        if not value and not default:
            raise ValueError(f"Configuration key '{key}' is not set and no default provided")
        return value
    
    @property
    def gemini_api_key(self) -> str:
        return self.get('GEMINI_API_KEY')
    
    @property
    def perplexity_api_key(self) -> str:
        return self.get('PERPLEXITY_API_KEY')
    
    @property
    def openai_api_key(self) -> str:
        return self.get('OPENAI_API_KEY')
    
    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.get('POSTGRES_USER')}:{self.get('POSTGRES_PASSWORD')}@{self.get('POSTGRES_HOST')}:{self.get('POSTGRES_PORT')}/{self.get('POSTGRES_DB')}"
    
    @property
    def redis_url(self) -> str:
        return f"redis://:{self.get('REDIS_PASSWORD')}@{self.get('REDIS_HOST')}:{self.get('REDIS_PORT')}/0"
    
    @property
    def kafka_servers(self) -> str:
        return self.get('KAFKA_BOOTSTRAP_SERVERS')
    
    @property
    def neo4j_uri(self) -> str:
        return self.get('NEO4J_URI')
    
    @property
    def neo4j_auth(self) -> tuple:
        return (self.get('NEO4J_USER'), self.get('NEO4J_PASSWORD'))
    
    @property
    def jwt_secret(self) -> str:
        return self.get('JWT_SECRET_KEY')
    
    @property
    def is_production(self) -> bool:
        return self.get('APP_ENV') == 'production'

# Singleton instance
config = ConfigManager()