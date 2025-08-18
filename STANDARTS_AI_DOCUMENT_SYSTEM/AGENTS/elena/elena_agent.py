"""
Elena Standards Research Agent - Полностью функциональный агент для исследования стандартов
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import google.generativeai as genai
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

# Import our config manager
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config_manager import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElenaAgent:
    """Elena - Expert in standards research and compliance"""
    
    def __init__(self):
        """Initialize Elena agent with all connections"""
        self.name = "Elena Standards Research Agent"
        self.version = "1.0.0"
        
        # Initialize Gemini
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Initialize PostgreSQL
        self.pg_conn = psycopg2.connect(config.postgres_url)
        self.pg_conn.autocommit = True
        
        # Initialize Redis
        self.redis_client = redis.from_url(config.redis_url, decode_responses=True)
        
        # Initialize Kafka
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=config.kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        self.kafka_consumer = KafkaConsumer(
            'standards-research',
            bootstrap_servers=config.kafka_servers,
            auto_offset_reset='latest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        logger.info(f"{self.name} v{self.version} initialized successfully")
    
    async def research_standards(self, query: str) -> Dict[str, Any]:
        """Research standards based on query"""
        logger.info(f"Researching standards for: {query}")
        
        # Check Redis cache first
        cache_key = f"elena:research:{query}"
        cached = self.redis_client.get(cache_key)
        if cached:
            logger.info("Returning cached result")
            return json.loads(cached)
        
        # Generate research using Gemini
        prompt = f"""
        As an expert in ISO, ITIL, COBIT, and NIST standards, research the following:
        {query}
        
        Provide:
        1. Relevant standards and frameworks
        2. Specific requirements and controls
        3. Implementation recommendations
        4. Compliance checklist
        
        Format as structured JSON.
        """
        
        response = self.model.generate_content(prompt)
        
        # Parse and structure the response
        result = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.name,
            "findings": self._parse_gemini_response(response.text),
            "status": "completed"
        }
        
        # Save to PostgreSQL
        self._save_to_database(result)
        
        # Cache result in Redis (24 hours)
        self.redis_client.setex(cache_key, 86400, json.dumps(result))
        
        # Send to Kafka
        self._send_to_kafka(result)
        
        logger.info(f"Research completed for: {query}")
        return result
    
    def parse_iso_documents(self, documents: List[str]) -> Dict[str, Any]:
        """Parse and analyze ISO documents"""
        logger.info(f"Parsing {len(documents)} ISO documents")
        
        parsed_results = []
        for doc in documents:
            # Use Gemini to parse and extract requirements
            prompt = f"""
            Parse this ISO document excerpt and extract:
            1. Control objectives
            2. Implementation requirements
            3. Audit criteria
            4. Evidence requirements
            
            Document: {doc[:2000]}  # Limit to 2000 chars for API
            """
            
            response = self.model.generate_content(prompt)
            parsed_results.append({
                "document": doc[:100] + "...",
                "parsed_content": response.text,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        result = {
            "total_documents": len(documents),
            "parsed_count": len(parsed_results),
            "results": parsed_results,
            "agent": self.name
        }
        
        # Save parsing results
        self._save_to_database(result)
        
        return result
    
    def extract_requirements(self, standard: str, category: str) -> List[Dict[str, str]]:
        """Extract specific requirements from standards"""
        logger.info(f"Extracting {category} requirements from {standard}")
        
        # Check cache
        cache_key = f"elena:requirements:{standard}:{category}"
        cached = self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        prompt = f"""
        Extract all {category} requirements from {standard} standard.
        For each requirement provide:
        - ID
        - Title
        - Description
        - Implementation guidance
        - Verification method
        
        Format as JSON array.
        """
        
        response = self.model.generate_content(prompt)
        requirements = self._parse_requirements(response.text)
        
        # Cache for 7 days
        self.redis_client.setex(cache_key, 604800, json.dumps(requirements))
        
        return requirements
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response into structured format"""
        try:
            # Try to parse as JSON first
            if response_text.strip().startswith('{'):
                return json.loads(response_text)
        except:
            pass
        
        # Fallback to text parsing
        return {
            "raw_response": response_text,
            "parsed": True,
            "format": "text"
        }
    
    def _parse_requirements(self, response_text: str) -> List[Dict[str, str]]:
        """Parse requirements from response"""
        try:
            if response_text.strip().startswith('['):
                return json.loads(response_text)
        except:
            pass
        
        # Fallback parsing
        return [{
            "raw_text": response_text,
            "parsed": False
        }]
    
    def _save_to_database(self, data: Dict[str, Any]):
        """Save results to PostgreSQL"""
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO research_results (agent_name, query, results, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (
                    self.name,
                    data.get('query', 'N/A'),
                    json.dumps(data),
                    datetime.utcnow()
                ))
            logger.info("Saved to database")
        except Exception as e:
            logger.error(f"Database save failed: {e}")
    
    def _send_to_kafka(self, data: Dict[str, Any]):
        """Send results to Kafka topic"""
        try:
            future = self.kafka_producer.send('research-completed', data)
            future.get(timeout=10)
            logger.info("Sent to Kafka topic: research-completed")
        except KafkaError as e:
            logger.error(f"Kafka send failed: {e}")
    
    def listen_for_requests(self):
        """Listen for research requests from Kafka"""
        logger.info("Listening for research requests...")
        
        for message in self.kafka_consumer:
            try:
                request = message.value
                logger.info(f"Received request: {request}")
                
                # Process request asynchronously
                asyncio.run(self.research_standards(request.get('query')))
                
            except Exception as e:
                logger.error(f"Error processing request: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check agent health status"""
        health = {
            "agent": self.name,
            "version": self.version,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "connections": {
                "postgresql": False,
                "redis": False,
                "kafka": False,
                "gemini": False
            }
        }
        
        # Check PostgreSQL
        try:
            with self.pg_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            health["connections"]["postgresql"] = True
        except:
            health["status"] = "degraded"
        
        # Check Redis
        try:
            self.redis_client.ping()
            health["connections"]["redis"] = True
        except:
            health["status"] = "degraded"
        
        # Check Kafka
        try:
            if self.kafka_producer.bootstrap_connected():
                health["connections"]["kafka"] = True
        except:
            health["status"] = "degraded"
        
        # Check Gemini
        try:
            test_response = self.model.generate_content("test")
            if test_response:
                health["connections"]["gemini"] = True
        except:
            health["status"] = "degraded"
        
        return health


if __name__ == "__main__":
    # Initialize and run Elena agent
    elena = ElenaAgent()
    
    # Check health
    health = elena.health_check()
    logger.info(f"Health check: {json.dumps(health, indent=2)}")
    
    # Example research
    asyncio.run(elena.research_standards("ISO 27001 access control requirements"))
    
    # Start listening for Kafka requests
    # elena.listen_for_requests()  # Uncomment to run as service