# claude_api_client.py - Claude AI API Client for TaskMaster
import logging
import json
import os
import asyncio
from typing import Dict, Any, Optional
import aiohttp
import time

logger = logging.getLogger(__name__)

class ClaudeAPIClient:
    """Client for interacting with Claude AI API"""
    
    def __init__(self):
        self.api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        self.base_url = 'https://api.anthropic.com/v1'
        self.model = 'claude-3-haiku-20240307'  # Fast, cost-effective model
        self.max_tokens = 1000
        self.timeout = 30
        self.rate_limit_delay = 1  # Seconds between requests
        self.last_request_time = 0
        
        if not self.api_key:
            logger.warning("Anthropic API key not found. Claude analysis will be unavailable.")
    
    def is_available(self) -> bool:
        """Check if Claude API is available"""
        return bool(self.api_key)
    
    async def analyze_task(self, task_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze task using Claude AI"""
        if not self.is_available():
            raise Exception("Claude API not available - missing API key")
        
        try:
            # Respect rate limiting
            await self._respect_rate_limit()
            
            # Prepare the prompt
            prompt = self._build_analysis_prompt(task_data, context)
            
            # Make API request
            response = await self._make_api_request(prompt)
            
            # Parse and structure the response
            analysis = self._parse_analysis_response(response)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Claude API analysis failed: {e}")
            raise
    
    def _build_analysis_prompt(self, task_data: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Build analysis prompt for Claude focused on task queue properties"""
        title = task_data.get('title', '')
        description = task_data.get('description', '')
        duration = task_data.get('duration', 60)
        urgency = task_data.get('urgency', 5)
        
        prompt = f"""Analyze this task to determine properties needed for intelligent task queue organization:

TASK: "{title}"
DESCRIPTION: {description}
CURRENT DURATION: {duration} minutes
CURRENT URGENCY: {urgency}/10

Analyze the task and respond with ONLY a JSON object with these specific properties:

{{
  "duration_analysis": {{
    "recommended_minutes": <number>,
    "confidence": "high|medium|low",
    "reasoning": "<brief explanation of duration estimate>"
  }},
  "task_structure": {{
    "is_divisible": <true/false>,
    "min_chunk_minutes": <number or null>,
    "natural_breakpoints": "<description of how to divide, or null>"
  }},
  "energy_requirements": {{
    "energy_level": "low|medium|high",
    "energy_type": "physical|mental|mixed",
    "cognitive_load": "low|medium|high"
  }},
  "environment": {{
    "location": "indoor|outdoor|flexible",
    "weather_dependent": <true/false>,
    "weather_requirements": "<specific conditions needed, or null>"
  }},
  "scheduling": {{
    "urgency_assessment": <1-10>,
    "urgency_reasoning": "<why this urgency level>",
    "optimal_time": "morning|afternoon|evening|anytime",
    "time_sensitivity": "<any time constraints or preferences>"
  }},
  "resources": {{
    "equipment_needed": ["<list of required tools/materials>"],
    "preparation_time": <minutes for setup>,
    "location_requirements": "<specific location needs>"
  }}
}}

Focus on practical scheduling properties. Be specific and actionable."""
        
        return prompt
    
    async def _make_api_request(self, prompt: str) -> str:
        """Make API request to Claude"""
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Claude API error {response.status}: {error_text}")
                
                result = await response.json()
                
                # Extract content from Claude's response format
                if 'content' in result and result['content']:
                    return result['content'][0]['text']
                else:
                    raise Exception("Unexpected response format from Claude API")
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's response into structured analysis"""
        try:
            # Try to extract JSON from the response
            # Claude sometimes includes text before/after JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                parsed = json.loads(json_text)
                
                # Structure the response according to our format
                analysis = {
                    'complexity_assessment': {
                        'ai_complexity_score': parsed.get('complexity_score', 5),
                        'ai_estimated_duration': parsed.get('time_estimate_minutes', 60),
                        'ai_confidence': self._map_confidence(parsed.get('confidence_level', 'medium')),
                        'complexity_factors': parsed.get('complexity_factors', [])
                    },
                    'dependency_insights': {
                        'ai_detected_dependencies': parsed.get('likely_dependencies', []),
                        'dependency_signals': parsed.get('dependency_signals', []),
                        'sequential_vs_parallel': parsed.get('sequential_vs_parallel', 'unknown'),
                        'ai_confidence': 0.8
                    },
                    'context_enhancement': {
                        'ai_generated_tags': parsed.get('suggested_tags', []),
                        'skill_requirements': parsed.get('skill_requirements', []),
                        'resource_requirements': parsed.get('resource_requirements', []),
                        'optimal_timing': parsed.get('optimal_time_of_day', 'anytime'),
                        'ai_confidence': 0.85
                    },
                    'smart_suggestions': self._format_ai_suggestions(parsed),
                    'confidence': 0.8,
                    'raw_response': response_text
                }
                
                return analysis
            
            else:
                raise ValueError("No valid JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse Claude response as JSON: {e}")
            
            # Fallback: extract insights from free text
            return self._extract_insights_from_text(response_text)
    
    def _map_confidence(self, confidence_str: str) -> float:
        """Map confidence string to numeric value"""
        mapping = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5
        }
        return mapping.get(confidence_str.lower(), 0.7)
    
    def _format_ai_suggestions(self, parsed_data: Dict[str, Any]) -> list:
        """Format AI suggestions into our standard format"""
        suggestions = []
        
        # Breaking down suggestion
        if parsed_data.get('breaking_down'):
            suggestions.append({
                'type': 'ai_chunking',
                'priority': 'medium',
                'suggestion': parsed_data['breaking_down'],
                'reasoning': 'AI analysis suggests task decomposition',
                'implementation': 'Consider creating sub-tasks',
                'source': 'claude_ai'
            })
        
        # Prioritization advice
        if parsed_data.get('prioritization_advice'):
            suggestions.append({
                'type': 'ai_scheduling',
                'priority': 'medium',
                'suggestion': parsed_data['prioritization_advice'],
                'reasoning': 'AI scheduling recommendation',
                'implementation': 'Adjust task scheduling accordingly',
                'source': 'claude_ai'
            })
        
        # Efficiency tips
        if parsed_data.get('efficiency_tips'):
            suggestions.append({
                'type': 'ai_optimization',
                'priority': 'low',
                'suggestion': parsed_data['efficiency_tips'],
                'reasoning': 'AI efficiency recommendation',
                'implementation': 'Apply suggested optimization',
                'source': 'claude_ai'
            })
        
        return suggestions
    
    def _extract_insights_from_text(self, text: str) -> Dict[str, Any]:
        """Fallback method to extract insights from free text response"""
        # Basic fallback analysis when JSON parsing fails
        logger.info("Using fallback text analysis for Claude response")
        
        return {
            'complexity_assessment': {
                'ai_complexity_score': 5,
                'ai_estimated_duration': 60,
                'ai_confidence': 0.3,
                'complexity_factors': []
            },
            'dependency_insights': {
                'ai_detected_dependencies': [],
                'ai_confidence': 0.3
            },
            'context_enhancement': {
                'ai_generated_tags': [],
                'ai_confidence': 0.3
            },
            'smart_suggestions': [],
            'confidence': 0.3,
            'raw_response': text,
            'parse_error': True
        }
    
    async def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()

# Synchronous wrapper for Flask integration
class SyncClaudeAPIClient:
    """Synchronous wrapper for Claude API client"""
    
    def __init__(self):
        self.async_client = ClaudeAPIClient()
    
    def is_available(self) -> bool:
        return self.async_client.is_available()
    
    def analyze_task(self, task_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Synchronous task analysis using Claude AI"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.async_client.analyze_task(task_data, context)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Sync Claude analysis failed: {e}")
            raise

# Global client instance
_claude_client: Optional[SyncClaudeAPIClient] = None

def get_claude_client() -> SyncClaudeAPIClient:
    """Get the global Claude API client instance"""
    global _claude_client
    if not _claude_client:
        _claude_client = SyncClaudeAPIClient()
    return _claude_client