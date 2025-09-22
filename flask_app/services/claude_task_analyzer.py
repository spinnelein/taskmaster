# claude_task_analyzer.py - AI-Powered Task Analysis Service for TaskMaster YOLO
import logging
import json
import os
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import hashlib
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import db, Task, Project, ProjectPhase, Initiative
from services.claude_api_client import get_claude_client

logger = logging.getLogger(__name__)

# Analysis categories and scoring weights
COMPLEXITY_INDICATORS = {
    'high': ['complex', 'difficult', 'challenging', 'advanced', 'comprehensive', 'detailed', 'thorough'],
    'medium': ['moderate', 'standard', 'typical', 'normal', 'regular', 'basic'],
    'low': ['simple', 'easy', 'quick', 'basic', 'straightforward', 'minor']
}

DEPENDENCY_KEYWORDS = [
    'after', 'before', 'depends on', 'requires', 'needs', 'waiting for',
    'once', 'when', 'following', 'prerequisite', 'blocked by'
]

TIME_ESTIMATION_PATTERNS = {
    'minutes': r'(\d+)\s*(?:min|minute|minutes)',
    'hours': r'(\d+)\s*(?:hr|hour|hours)',
    'days': r'(\d+)\s*(?:day|days)',
    'weeks': r'(\d+)\s*(?:week|weeks)'
}

class ClaudeAnalysisCache:
    """Simple file-based cache for Claude API results"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), '.claude_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_duration_hours = 24  # Cache results for 24 hours
    
    def _get_cache_key(self, task_data: Dict[str, Any]) -> str:
        """Generate cache key from task data"""
        # Create hash from title and description for consistent caching
        content = f"{task_data.get('title', '')}{task_data.get('description', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached analysis if available and not expired"""
        try:
            cache_key = self._get_cache_key(task_data)
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            if not os.path.exists(cache_file):
                return None
            
            # Check if cache is expired
            cache_age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600
            if cache_age_hours > self.cache_duration_hours:
                os.remove(cache_file)
                return None
            
            with open(cache_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
    
    def set(self, task_data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
        """Cache analysis result"""
        try:
            cache_key = self._get_cache_key(task_data)
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            with open(cache_file, 'w') as f:
                json.dump(analysis, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Error writing cache: {e}")

class ClaudeTaskAnalyzer:
    """AI-powered task analysis service using Claude for intelligent insights"""
    
    def __init__(self):
        self.logger = logger
        self.cache = ClaudeAnalysisCache()
        
        # Check for API key in environment
        self.api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        if self.api_key:
            self.claude_client = get_claude_client()
            self.is_claude_available = self.claude_client.is_available()
        else:
            self.claude_client = None
            self.is_claude_available = False
            
        if not self.is_claude_available:
            self.logger.warning("Claude API key not found. Using fallback analysis only.")
    
    def analyze_task_comprehensive(self, task: Dict[str, Any], context: Dict[str, Any] = None, save_to_db: bool = False, apply_recommendations: bool = True) -> Dict[str, Any]:
        """
        Comprehensive task analysis combining AI and rule-based insights
        
        Args:
            task: Task dictionary with id, title, description, etc.
            context: Optional context information
            save_to_db: Whether to save analysis results to database YOLO fields
        
        Returns analysis with:
        - complexity_assessment: difficulty and time estimates
        - dependency_insights: detected dependencies and relationships
        - context_enhancement: enriched metadata and tags
        - smart_suggestions: optimization recommendations
        - ai_confidence: confidence score for AI-based insights
        """
        try:
            # Check cache first
            cached_analysis = self.cache.get(task)
            if cached_analysis and not save_to_db:
                self.logger.debug(f"Using cached analysis for task: {task.get('title', 'Unknown')}")
                return cached_analysis
            
            # Initialize analysis structure
            analysis = {
                'task_id': task.get('id'),
                'analyzed_at': datetime.now().isoformat(),
                'complexity_assessment': {},
                'dependency_insights': {},
                'context_enhancement': {},
                'smart_suggestions': [],
                'ai_confidence': 0.0,
                'analysis_source': 'hybrid'  # 'ai', 'rules', or 'hybrid'
            }
            
            # Rule-based analysis (always available)
            rule_analysis = self._analyze_with_rules(task, context)
            analysis.update(rule_analysis)
            
            # AI-enhanced analysis (if available)
            if self.is_claude_available:
                try:
                    ai_analysis = self._analyze_with_claude(task, context)
                    analysis = self._merge_analyses(analysis, ai_analysis)
                    analysis['analysis_source'] = 'hybrid'
                    analysis['ai_confidence'] = ai_analysis.get('confidence', 0.0)
                except Exception as e:
                    self.logger.warning(f"Claude analysis failed, using rules only: {e}")
                    analysis['analysis_source'] = 'rules'
            else:
                analysis['analysis_source'] = 'rules'
            
            # Cache the result
            self.cache.set(task, analysis)
            
            # Save to database YOLO fields if requested
            if save_to_db:
                self._save_analysis_to_database(task.get('id'), analysis, apply_recommendations)
            
            self.logger.info(f"Completed comprehensive analysis for task: {task.get('title', 'Unknown')}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive task analysis: {e}")
            return self._get_fallback_analysis(task)
    
    def _analyze_with_rules(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Rule-based analysis using pattern matching and heuristics"""
        title = task.get('title', '').lower()
        description = task.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        analysis = {
            'complexity_assessment': self._assess_complexity_rules(combined_text, task),
            'dependency_insights': self._detect_dependencies_rules(combined_text, task),
            'context_enhancement': self._enhance_context_rules(combined_text, task, context),
            'smart_suggestions': self._generate_suggestions_rules(task, context)
        }
        
        return analysis
    
    def _assess_complexity_rules(self, text: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Assess task complexity using rule-based heuristics"""
        complexity_score = 5  # Default medium complexity (1-10 scale)
        
        # Check complexity indicators
        for level, keywords in COMPLEXITY_INDICATORS.items():
            for keyword in keywords:
                if keyword in text:
                    if level == 'high':
                        complexity_score += 2
                    elif level == 'low':
                        complexity_score -= 2
        
        # Duration-based complexity
        duration = task.get('duration', 60)
        if duration > 240:  # > 4 hours
            complexity_score += 3
        elif duration > 120:  # > 2 hours
            complexity_score += 1
        elif duration < 30:  # < 30 minutes
            complexity_score -= 1
        
        # Text length indicates complexity
        if len(text) > 200:
            complexity_score += 1
        elif len(text) < 50:
            complexity_score -= 1
        
        # Clamp to 1-10 range
        complexity_score = max(1, min(10, complexity_score))
        
        # Estimate time adjustments
        time_multiplier = 1.0
        if complexity_score >= 8:
            time_multiplier = 1.5
            suggested_duration = int(duration * time_multiplier)
            time_confidence = 'low'
        elif complexity_score <= 3:
            time_multiplier = 0.8
            suggested_duration = int(duration * time_multiplier)
            time_confidence = 'medium'
        else:
            suggested_duration = duration
            time_confidence = 'medium'
        
        return {
            'complexity_score': complexity_score,
            'complexity_level': 'high' if complexity_score >= 7 else 'medium' if complexity_score >= 4 else 'low',
            'estimated_duration_minutes': suggested_duration,
            'time_confidence': time_confidence,
            'time_multiplier': time_multiplier,
            'factors': self._extract_complexity_factors(text)
        }
    
    def _detect_dependencies_rules(self, text: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential dependencies using pattern matching"""
        detected_dependencies = []
        dependency_signals = []
        
        # Look for dependency keywords
        for keyword in DEPENDENCY_KEYWORDS:
            if keyword in text:
                dependency_signals.append(keyword)
        
        # Extract time-based dependencies
        time_patterns = self._extract_time_references(text)
        
        # Look for task references (basic pattern matching)
        task_references = self._extract_task_references(text)
        
        # Check existing dependencies
        existing_deps = task.get('depends_on_task_ids', [])
        if isinstance(existing_deps, str):
            try:
                existing_deps = json.loads(existing_deps) if existing_deps != 'null' else []
            except:
                existing_deps = []
        
        return {
            'has_dependencies': len(dependency_signals) > 0 or len(existing_deps) > 0,
            'dependency_signals': dependency_signals,
            'time_references': time_patterns,
            'task_references': task_references,
            'existing_dependencies': existing_deps,
            'suggested_dependencies': detected_dependencies,
            'dependency_confidence': 'medium' if dependency_signals else 'low'
        }
    
    def _enhance_context_rules(self, text: str, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhance task context with extracted metadata"""
        tags = []
        categories = []
        priority_indicators = []
        
        # Extract action verbs
        action_words = self._extract_action_words(text)
        
        # Detect urgency indicators
        urgency_words = ['urgent', 'asap', 'immediately', 'today', 'now', 'critical']
        for word in urgency_words:
            if word in text:
                priority_indicators.append(word)
        
        # Detect skill requirements
        skill_indicators = ['code', 'program', 'design', 'write', 'research', 'call', 'email', 'meeting']
        detected_skills = [skill for skill in skill_indicators if skill in text]
        
        # Extract locations if mentioned
        location_indicators = ['office', 'home', 'store', 'online', 'phone', 'computer']
        detected_locations = [loc for loc in location_indicators if loc in text]
        
        # Categorize by domain
        if any(word in text for word in ['code', 'program', 'software', 'bug', 'deploy']):
            categories.append('development')
        if any(word in text for word in ['meeting', 'call', 'discuss', 'review']):
            categories.append('communication')
        if any(word in text for word in ['research', 'study', 'learn', 'analyze']):
            categories.append('research')
        if any(word in text for word in ['buy', 'purchase', 'order', 'shop']):
            categories.append('shopping')
        
        return {
            'extracted_tags': tags,
            'categories': categories,
            'action_words': action_words,
            'priority_indicators': priority_indicators,
            'skill_requirements': detected_skills,
            'location_context': detected_locations,
            'enhancement_confidence': 'medium'
        }
    
    def _generate_suggestions_rules(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on rules"""
        suggestions = []
        
        # Duration suggestions
        duration = task.get('duration', 60)
        if duration > 180:  # > 3 hours
            suggestions.append({
                'type': 'chunking',
                'priority': 'high',
                'suggestion': 'Consider breaking this long task into smaller chunks for better focus',
                'reasoning': f'Task duration of {duration} minutes may lead to fatigue',
                'implementation': 'Enable task chunking or create sub-tasks'
            })
        
        # Urgency vs duration mismatch
        urgency = task.get('urgency', 5)
        if urgency >= 8 and duration > 120:
            suggestions.append({
                'type': 'priority',
                'priority': 'high',
                'suggestion': 'High urgency task with long duration - consider delegating or simplifying',
                'reasoning': 'Urgent tasks should typically be shorter to enable quick completion',
                'implementation': 'Break into smaller urgent pieces or reassess urgency'
            })
        
        # Missing description
        if not task.get('description') or len(task.get('description', '')) < 10:
            suggestions.append({
                'type': 'clarity',
                'priority': 'medium',
                'suggestion': 'Add more detailed description for better planning',
                'reasoning': 'Detailed descriptions improve estimation and execution',
                'implementation': 'Expand description with specific steps or requirements'
            })
        
        # No due date for important tasks
        if urgency >= 7 and not task.get('due_date'):
            suggestions.append({
                'type': 'scheduling',
                'priority': 'medium',
                'suggestion': 'Add due date for this important task',
                'reasoning': 'Important tasks benefit from explicit deadlines',
                'implementation': 'Set appropriate due date based on priority'
            })
        
        return suggestions
    
    def _analyze_with_claude(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze task using Claude AI"""
        try:
            self.logger.info(f"Analyzing task with Claude AI: {task.get('title', 'Unknown')}")
            
            # Use the Claude API client
            ai_analysis = self.claude_client.analyze_task(task, context)
            
            self.logger.info("Claude AI analysis completed successfully")
            return ai_analysis
            
        except Exception as e:
            self.logger.error(f"Claude AI analysis failed: {e}")
            
            # Return fallback structure on failure
            return {
                'complexity_assessment': {
                    'ai_complexity_score': 5,
                    'ai_estimated_duration': task.get('duration', 60),
                    'ai_confidence': 0.3
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
                'error': str(e)
            }
    
    def _merge_analyses(self, rule_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Merge rule-based and AI analyses intelligently"""
        merged = rule_analysis.copy()
        
        # Merge complexity assessments
        if 'complexity_assessment' in ai_analysis:
            ai_complexity = ai_analysis['complexity_assessment']
            rule_complexity = merged['complexity_assessment']
            
            # Average complexity scores if both exist
            if 'ai_complexity_score' in ai_complexity:
                rule_score = rule_complexity.get('complexity_score', 5)
                ai_score = ai_complexity.get('ai_complexity_score', 5)
                merged_score = (rule_score + ai_score) / 2
                merged['complexity_assessment']['final_complexity_score'] = merged_score
        
        # Add AI insights
        merged['ai_insights'] = ai_analysis
        
        return merged
    
    def _get_fallback_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Provide basic fallback analysis when all methods fail"""
        return {
            'task_id': task.get('id'),
            'analyzed_at': datetime.now().isoformat(),
            'complexity_assessment': {
                'complexity_score': 5,
                'complexity_level': 'medium',
                'estimated_duration_minutes': task.get('duration', 60),
                'time_confidence': 'low'
            },
            'dependency_insights': {
                'has_dependencies': False,
                'dependency_confidence': 'low'
            },
            'context_enhancement': {
                'categories': ['general'],
                'enhancement_confidence': 'low'
            },
            'smart_suggestions': [],
            'ai_confidence': 0.0,
            'analysis_source': 'fallback'
        }
    
    def _extract_complexity_factors(self, text: str) -> List[str]:
        """Extract factors that contribute to complexity"""
        factors = []
        
        if any(word in text for word in ['multiple', 'several', 'many', 'various']):
            factors.append('multiple_components')
        if any(word in text for word in ['research', 'analyze', 'investigate']):
            factors.append('research_required')
        if any(word in text for word in ['coordinate', 'collaborate', 'team']):
            factors.append('coordination_needed')
        if any(word in text for word in ['new', 'first time', 'learn']):
            factors.append('learning_required')
        
        return factors
    
    def _extract_time_references(self, text: str) -> List[str]:
        """Extract time-based references that might indicate dependencies"""
        time_refs = []
        
        for pattern_name, pattern in TIME_ESTIMATION_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                time_refs.append(f"{match} {pattern_name}")
        
        return time_refs
    
    def _extract_task_references(self, text: str) -> List[str]:
        """Extract potential references to other tasks"""
        # Basic pattern for task references
        task_patterns = [
            r'after (\w+)',
            r'once (\w+) is (?:done|complete|finished)',
            r'depends on (\w+)',
            r'requires (\w+)'
        ]
        
        references = []
        for pattern in task_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        
        return references
    
    def _extract_action_words(self, text: str) -> List[str]:
        """Extract action verbs from task text"""
        action_verbs = [
            'create', 'build', 'design', 'implement', 'develop', 'write', 'code',
            'research', 'analyze', 'study', 'review', 'investigate',
            'call', 'email', 'contact', 'discuss', 'meet', 'schedule',
            'buy', 'purchase', 'order', 'get', 'obtain',
            'fix', 'repair', 'update', 'modify', 'change',
            'test', 'verify', 'check', 'validate', 'confirm'
        ]
        
        found_actions = []
        for verb in action_verbs:
            if verb in text:
                found_actions.append(verb)
        
        return found_actions
    
    def analyze_project_tasks(self, project_id: str) -> Dict[str, Any]:
        """Analyze all tasks in a project for collective insights"""
        try:
            # Get project tasks
            tasks = Task.query.filter_by(project_id=project_id, is_completed=False).all()
            task_dicts = [task.to_dict() for task in tasks]
            
            if not task_dicts:
                return {
                    'success': False,
                    'message': 'No incomplete tasks found in project',
                    'project_id': project_id
                }
            
            # Analyze each task
            task_analyses = []
            for task_dict in task_dicts:
                analysis = self.analyze_task_comprehensive(task_dict)
                task_analyses.append({
                    'task_id': task_dict['id'],
                    'task_title': task_dict.get('title', 'Unknown'),
                    'analysis': analysis
                })
            
            # Generate project-level insights
            project_insights = self._generate_project_insights(task_analyses)
            
            return {
                'success': True,
                'project_id': project_id,
                'tasks_analyzed': len(task_analyses),
                'task_analyses': task_analyses,
                'project_insights': project_insights,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing project tasks: {e}")
            return {
                'success': False,
                'message': f"Project analysis failed: {str(e)}",
                'project_id': project_id
            }
    
    def _generate_project_insights(self, task_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights about the entire project based on task analyses"""
        total_tasks = len(task_analyses)
        
        # Complexity distribution
        complexity_scores = []
        high_complexity_tasks = []
        
        for task_analysis in task_analyses:
            analysis = task_analysis['analysis']
            complexity = analysis.get('complexity_assessment', {})
            score = complexity.get('complexity_score', 5)
            complexity_scores.append(score)
            
            if score >= 7:
                high_complexity_tasks.append(task_analysis['task_title'])
        
        avg_complexity = sum(complexity_scores) / len(complexity_scores) if complexity_scores else 5
        
        # Dependency analysis
        tasks_with_deps = sum(1 for ta in task_analyses 
                             if ta['analysis'].get('dependency_insights', {}).get('has_dependencies', False))
        
        # Time estimation
        total_estimated_time = sum(
            ta['analysis'].get('complexity_assessment', {}).get('estimated_duration_minutes', 0)
            for ta in task_analyses
        )
        
        # Project risk assessment
        risk_level = 'low'
        risk_factors = []
        
        if avg_complexity >= 7:
            risk_level = 'high'
            risk_factors.append('High average task complexity')
        elif avg_complexity >= 5:
            risk_level = 'medium'
            risk_factors.append('Medium complexity tasks')
        
        if tasks_with_deps / total_tasks > 0.5:
            risk_factors.append('High dependency ratio')
            if risk_level == 'low':
                risk_level = 'medium'
        
        return {
            'total_tasks': total_tasks,
            'average_complexity': round(avg_complexity, 2),
            'high_complexity_tasks': high_complexity_tasks,
            'tasks_with_dependencies': tasks_with_deps,
            'dependency_ratio': round(tasks_with_deps / total_tasks, 2),
            'total_estimated_hours': round(total_estimated_time / 60, 1),
            'project_risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': self._generate_project_recommendations(avg_complexity, tasks_with_deps, total_tasks)
        }
    
    def _generate_project_recommendations(self, avg_complexity: float, dep_count: int, total_tasks: int) -> List[str]:
        """Generate recommendations for project management"""
        recommendations = []
        
        if avg_complexity >= 7:
            recommendations.append("Consider breaking down high-complexity tasks into smaller components")
            recommendations.append("Allocate extra time buffers for complex tasks")
        
        if dep_count / total_tasks > 0.4:
            recommendations.append("Pay special attention to dependency management")
            recommendations.append("Consider parallel work streams where possible")
        
        if total_tasks > 20:
            recommendations.append("Large project - consider milestone-based planning")
            recommendations.append("Regular progress reviews recommended")
        
        return recommendations
    
    def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """Get comprehensive context for a task including project/initiative relationships"""
        try:
            # Get the task
            task = Task.query.get(task_id)
            if not task:
                return {
                    'success': False,
                    'error': 'Task not found',
                    'task_id': task_id
                }
            
            context = {
                'task_id': task_id,
                'task_title': task.title,
                'success': True,
                'project_context': None,
                'initiative_context': None,
                'related_tasks': [],
                'dependencies': {
                    'depends_on': [],
                    'blocks': []
                }
            }
            
            # Get project context if task belongs to a project
            if task.project_id:
                try:
                    project = Project.query.get(task.project_id)
                    if project:
                        # Get other tasks in the same project
                        project_tasks = Task.query.filter_by(
                            project_id=task.project_id,
                            is_completed=False
                        ).filter(Task.id != task_id).limit(10).all()
                        
                        context['project_context'] = {
                            'id': project.id,
                            'title': project.title,
                            'description': project.description,
                            'status': project.status,
                            'priority': project.priority,
                            'total_tasks': len(project_tasks) + 1,
                            'related_tasks': [{'id': t.id, 'title': t.title} for t in project_tasks]
                        }
                        
                        context['related_tasks'].extend([{
                            'id': t.id,
                            'title': t.title,
                            'relationship': 'same_project'
                        } for t in project_tasks])
                        
                except Exception as e:
                    self.logger.warning(f"Error getting project context: {e}")
            
            # Get initiative context if task belongs to an initiative
            if task.initiative_id:
                try:
                    initiative = Initiative.query.get(task.initiative_id)
                    if initiative:
                        # Get other tasks in the same initiative
                        initiative_tasks = Task.query.filter_by(
                            initiative_id=task.initiative_id,
                            is_completed=False
                        ).filter(Task.id != task_id).limit(10).all()
                        
                        context['initiative_context'] = {
                            'id': initiative.id,
                            'title': initiative.title,
                            'description': initiative.description,
                            'status': initiative.status,
                            'total_tasks': len(initiative_tasks) + 1,
                            'related_tasks': [{'id': t.id, 'title': t.title} for t in initiative_tasks]
                        }
                        
                        context['related_tasks'].extend([{
                            'id': t.id,
                            'title': t.title,
                            'relationship': 'same_initiative'
                        } for t in initiative_tasks])
                        
                except Exception as e:
                    self.logger.warning(f"Error getting initiative context: {e}")
            
            # Parse task dependencies
            try:
                depends_on_ids = task.depends_on_task_ids
                if depends_on_ids and depends_on_ids != 'null':
                    if isinstance(depends_on_ids, str):
                        depends_on_ids = json.loads(depends_on_ids) if depends_on_ids != 'null' else []
                    
                    if depends_on_ids:
                        dependency_tasks = Task.query.filter(Task.id.in_(depends_on_ids)).all()
                        context['dependencies']['depends_on'] = [
                            {'id': t.id, 'title': t.title, 'status': t.status}
                            for t in dependency_tasks
                        ]
                
                blocks_ids = task.blocks_task_ids
                if blocks_ids and blocks_ids != 'null':
                    if isinstance(blocks_ids, str):
                        blocks_ids = json.loads(blocks_ids) if blocks_ids != 'null' else []
                    
                    if blocks_ids:
                        blocked_tasks = Task.query.filter(Task.id.in_(blocks_ids)).all()
                        context['dependencies']['blocks'] = [
                            {'id': t.id, 'title': t.title, 'status': t.status}
                            for t in blocked_tasks
                        ]
                        
            except Exception as e:
                self.logger.warning(f"Error parsing task dependencies: {e}")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting task context for {task_id}: {e}")
            return {
                'success': False,
                'error': f"Failed to get task context: {str(e)}",
                'task_id': task_id
            }
    
    def get_optimization_suggestions(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimization suggestions for a specific task"""
        try:
            suggestions = {
                'task_id': task_dict.get('id'),
                'task_title': task_dict.get('title', 'Unknown'),
                'suggestions': [],
                'priority_insights': {},
                'scheduling_recommendations': [],
                'success': True
            }
            
            # Use existing rule-based suggestion generation
            rule_suggestions = self._generate_suggestions_rules(task_dict)
            suggestions['suggestions'] = rule_suggestions
            
            # Add priority insights
            urgency = task_dict.get('urgency', 5)
            duration = task_dict.get('duration', 60)
            
            suggestions['priority_insights'] = {
                'current_urgency': urgency,
                'urgency_level': 'high' if urgency >= 8 else 'medium' if urgency >= 5 else 'low',
                'time_pressure': 'high' if duration > 180 else 'medium' if duration > 60 else 'low',
                'recommended_urgency': self._calculate_recommended_urgency(task_dict)
            }
            
            # Add scheduling recommendations
            scheduling_recs = []
            
            # Time of day recommendations
            if any(word in task_dict.get('title', '').lower() for word in ['creative', 'design', 'write', 'plan']):
                scheduling_recs.append({
                    'type': 'time_of_day',
                    'recommendation': 'Schedule during morning hours for optimal creativity',
                    'reasoning': 'Creative tasks benefit from fresh mental energy'
                })
            
            if any(word in task_dict.get('title', '').lower() for word in ['admin', 'email', 'organize', 'file']):
                scheduling_recs.append({
                    'type': 'time_of_day',
                    'recommendation': 'Schedule during afternoon for routine tasks',
                    'reasoning': 'Administrative tasks are good for lower-energy periods'
                })
            
            # Duration-based recommendations
            if duration > 120:  # > 2 hours
                scheduling_recs.append({
                    'type': 'chunking',
                    'recommendation': 'Consider breaking into 90-minute focused sessions',
                    'reasoning': 'Long tasks benefit from natural attention cycles'
                })
            
            # Context switching recommendations
            if task_dict.get('required_context'):
                scheduling_recs.append({
                    'type': 'context',
                    'recommendation': 'Batch with similar context-requiring tasks',
                    'reasoning': 'Minimize context switching overhead'
                })
            
            suggestions['scheduling_recommendations'] = scheduling_recs
            
            # AI enhancement if available
            if self.is_claude_available:
                try:
                    ai_suggestions = self._get_ai_optimization_suggestions(task_dict)
                    suggestions['ai_suggestions'] = ai_suggestions
                    suggestions['enhanced_by_ai'] = True
                except Exception as e:
                    self.logger.warning(f"AI optimization suggestions failed: {e}")
                    suggestions['enhanced_by_ai'] = False
            else:
                suggestions['enhanced_by_ai'] = False
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting optimization suggestions: {e}")
            return {
                'success': False,
                'error': f"Failed to get optimization suggestions: {str(e)}",
                'task_id': task_dict.get('id')
            }
    
    def assess_task_complexity(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the complexity of a task with detailed breakdown"""
        try:
            # Use existing rule-based complexity assessment
            title = task_dict.get('title', '').lower()
            description = task_dict.get('description', '').lower()
            combined_text = f"{title} {description}"
            
            # Get base complexity assessment from existing method
            base_assessment = self._assess_complexity_rules(combined_text, task_dict)
            
            # Enhance with additional analysis
            complexity_analysis = {
                'task_id': task_dict.get('id'),
                'task_title': task_dict.get('title', 'Unknown'),
                'success': True,
                'overall_complexity': base_assessment,
                'complexity_factors': {
                    'cognitive_load': self._assess_cognitive_load(task_dict),
                    'technical_complexity': self._assess_technical_complexity(combined_text),
                    'dependency_complexity': self._assess_dependency_complexity(task_dict),
                    'uncertainty_level': self._assess_uncertainty_level(combined_text)
                },
                'time_estimation_confidence': self._assess_time_confidence(task_dict, base_assessment),
                'risk_factors': self._identify_risk_factors(task_dict, combined_text),
                'complexity_recommendations': []
            }
            
            # Generate complexity-based recommendations
            complexity_score = base_assessment.get('complexity_score', 5)
            
            if complexity_score >= 8:
                complexity_analysis['complexity_recommendations'].extend([
                    "Consider breaking this task into smaller, more manageable subtasks",
                    "Allocate extra time for planning and potential obstacles",
                    "Consider pairing with a more experienced team member if possible"
                ])
            elif complexity_score >= 6:
                complexity_analysis['complexity_recommendations'].extend([
                    "Plan for potential challenges and have backup approaches ready",
                    "Consider a brief planning session before starting"
                ])
            else:
                complexity_analysis['complexity_recommendations'].append(
                    "This task appears straightforward - good candidate for efficient execution"
                )
            
            # AI enhancement if available
            if self.is_claude_available:
                try:
                    ai_complexity = self._get_ai_complexity_assessment(task_dict)
                    complexity_analysis['ai_assessment'] = ai_complexity
                    complexity_analysis['enhanced_by_ai'] = True
                except Exception as e:
                    self.logger.warning(f"AI complexity assessment failed: {e}")
                    complexity_analysis['enhanced_by_ai'] = False
            else:
                complexity_analysis['enhanced_by_ai'] = False
            
            return complexity_analysis
            
        except Exception as e:
            self.logger.error(f"Error assessing task complexity: {e}")
            return {
                'success': False,
                'error': f"Failed to assess task complexity: {str(e)}",
                'task_id': task_dict.get('id')
            }
    
    def _calculate_recommended_urgency(self, task_dict: Dict[str, Any]) -> int:
        """Calculate recommended urgency based on task characteristics"""
        base_urgency = task_dict.get('urgency', 5)
        
        # Adjust based on due date
        if task_dict.get('due_date'):
            # If due soon, increase urgency (simplified logic)
            base_urgency += 1
        
        # Adjust based on dependencies
        depends_on = task_dict.get('depends_on_task_ids')
        if depends_on and depends_on != 'null':
            base_urgency += 1  # Dependent tasks are more urgent
        
        return max(1, min(10, base_urgency))
    
    def _assess_cognitive_load(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the cognitive load required for the task"""
        text = f"{task_dict.get('title', '')} {task_dict.get('description', '')}".lower()
        
        cognitive_indicators = {
            'high': ['analyze', 'design', 'plan', 'strategy', 'complex', 'solve', 'research'],
            'medium': ['review', 'organize', 'coordinate', 'implement', 'update'],
            'low': ['copy', 'move', 'simple', 'routine', 'basic', 'standard']
        }
        
        cognitive_score = 5  # Default medium
        
        for level, keywords in cognitive_indicators.items():
            for keyword in keywords:
                if keyword in text:
                    if level == 'high':
                        cognitive_score += 2
                    elif level == 'low':
                        cognitive_score -= 1
        
        cognitive_score = max(1, min(10, cognitive_score))
        
        return {
            'score': cognitive_score,
            'level': 'high' if cognitive_score >= 7 else 'medium' if cognitive_score >= 4 else 'low',
            'indicators_found': [word for word in text.split() if any(word in indicators for indicators in cognitive_indicators.values())]
        }
    
    def _assess_technical_complexity(self, text: str) -> Dict[str, Any]:
        """Assess technical complexity of the task"""
        technical_keywords = [
            'code', 'program', 'develop', 'build', 'deploy', 'configure',
            'database', 'api', 'integration', 'system', 'technical', 'software'
        ]
        
        technical_count = sum(1 for keyword in technical_keywords if keyword in text)
        technical_score = min(10, technical_count * 2 + 3)  # Base score of 3, +2 per keyword
        
        return {
            'score': technical_score,
            'level': 'high' if technical_score >= 7 else 'medium' if technical_score >= 4 else 'low',
            'technical_keywords_found': [kw for kw in technical_keywords if kw in text]
        }
    
    def _assess_dependency_complexity(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Assess complexity introduced by task dependencies"""
        depends_on = task_dict.get('depends_on_task_ids', [])
        blocks = task_dict.get('blocks_task_ids', [])
        
        if isinstance(depends_on, str):
            try:
                depends_on = json.loads(depends_on) if depends_on != 'null' else []
            except:
                depends_on = []
        
        if isinstance(blocks, str):
            try:
                blocks = json.loads(blocks) if blocks != 'null' else []
            except:
                blocks = []
        
        dependency_count = len(depends_on) + len(blocks)
        dependency_score = min(10, dependency_count * 2 + 1)
        
        return {
            'score': dependency_score,
            'level': 'high' if dependency_score >= 7 else 'medium' if dependency_score >= 4 else 'low',
            'depends_on_count': len(depends_on),
            'blocks_count': len(blocks),
            'total_dependencies': dependency_count
        }
    
    def _assess_uncertainty_level(self, text: str) -> Dict[str, Any]:
        """Assess the level of uncertainty in the task"""
        uncertainty_keywords = [
            'research', 'investigate', 'explore', 'figure out', 'determine',
            'unclear', 'unknown', 'maybe', 'possibly', 'might', 'could'
        ]
        
        uncertainty_count = sum(1 for keyword in uncertainty_keywords if keyword in text)
        uncertainty_score = min(10, uncertainty_count * 2 + 1)
        
        return {
            'score': uncertainty_score,
            'level': 'high' if uncertainty_score >= 7 else 'medium' if uncertainty_score >= 4 else 'low',
            'uncertainty_indicators': [kw for kw in uncertainty_keywords if kw in text]
        }
    
    def _assess_time_confidence(self, task_dict: Dict[str, Any], complexity_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess confidence in time estimation"""
        duration = task_dict.get('duration', 60)
        complexity_score = complexity_assessment.get('complexity_score', 5)
        
        # Base confidence
        confidence = 7  # Medium confidence
        
        # Reduce confidence for high complexity
        if complexity_score >= 8:
            confidence -= 3
        elif complexity_score >= 6:
            confidence -= 1
        
        # Reduce confidence for very long or very short tasks
        if duration > 240 or duration < 15:
            confidence -= 2
        
        # Reduce confidence if task description is sparse
        description_length = len(task_dict.get('description', ''))
        if description_length < 20:
            confidence -= 1
        
        confidence = max(1, min(10, confidence))
        
        return {
            'score': confidence,
            'level': 'high' if confidence >= 7 else 'medium' if confidence >= 4 else 'low',
            'factors': {
                'complexity_impact': complexity_score >= 6,
                'duration_appropriate': 15 <= duration <= 240,
                'description_adequate': description_length >= 20
            }
        }
    
    def _identify_risk_factors(self, task_dict: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """Identify potential risk factors for the task"""
        risk_factors = []
        
        # High urgency + long duration = risk
        urgency = task_dict.get('urgency', 5)
        duration = task_dict.get('duration', 60)
        
        if urgency >= 8 and duration > 120:
            risk_factors.append({
                'type': 'urgency_duration_mismatch',
                'severity': 'high',
                'description': 'High urgency task with long duration',
                'impact': 'May lead to rushing and quality issues'
            })
        
        # Missing due date for urgent task
        if urgency >= 7 and not task_dict.get('due_date'):
            risk_factors.append({
                'type': 'missing_deadline',
                'severity': 'medium',
                'description': 'Urgent task without defined due date',
                'impact': 'Risk of deprioritization'
            })
        
        # Vague description
        if len(task_dict.get('description', '')) < 10:
            risk_factors.append({
                'type': 'insufficient_detail',
                'severity': 'medium',
                'description': 'Task lacks detailed description',
                'impact': 'May lead to scope creep or confusion'
            })
        
        # Dependency risks
        depends_on = task_dict.get('depends_on_task_ids')
        if depends_on and depends_on != 'null':
            risk_factors.append({
                'type': 'dependency_risk',
                'severity': 'medium',
                'description': 'Task depends on other tasks',
                'impact': 'Potential delays if dependencies are not completed'
            })
        
        return risk_factors
    
    def _get_ai_optimization_suggestions(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered optimization suggestions (placeholder for future implementation)"""
        # This would use the Claude API client when available
        return {
            'suggestions': [],
            'confidence': 0.0,
            'note': 'AI optimization suggestions require Claude API configuration'
        }
    
    def _get_ai_complexity_assessment(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered complexity assessment (placeholder for future implementation)"""
        # This would use the Claude API client when available
        return {
            'ai_complexity_score': 5,
            'ai_confidence': 0.0,
            'note': 'AI complexity assessment requires Claude API configuration'
        }
    
    def _save_analysis_to_database(self, task_id: str, analysis: Dict[str, Any], apply_recommendations: bool = True) -> bool:
        """
        Save analysis results to database and optionally apply AI recommendations to core task properties
        
        Updates the Task record with:
        - cognitive_load: extracted from complexity assessment  
        - ai_analysis: full JSON analysis
        - last_analyzed: current timestamp
        - energy_level: extracted from analysis
        
        If apply_recommendations=True, also updates core scheduling properties:
        - duration: AI-recommended duration
        - urgency: AI-assessed urgency level
        - is_divisible: whether task can be chunked
        - min_chunk_size: recommended chunk size
        - required_weather: weather requirements
        """
        try:
            # Get the task from database
            task = Task.query.get(task_id)
            if not task:
                self.logger.error(f"Task {task_id} not found for database save")
                return False
            
            # Store original values for logging
            original_duration = task.duration
            original_urgency = task.urgency
            
            # Extract cognitive load from complexity assessment
            complexity = analysis.get('complexity_assessment', {})
            cognitive_load = complexity.get('complexity_level', 'medium')  # low/medium/high
            
            # Extract energy level from AI analysis if available, otherwise use rules
            ai_insights = analysis.get('ai_insights', {})
            energy_reqs = ai_insights.get('energy_requirements', {})
            energy_level = energy_reqs.get('energy_level', 'medium')
            
            # Fallback to rule-based energy detection if AI didn't provide it
            if energy_level == 'medium' and not ai_insights:
                context_enhancement = analysis.get('context_enhancement', {})
                action_words = context_enhancement.get('action_words', [])
                
                # Physical/outdoor tasks = high energy
                if any(word in str(action_words).lower() for word in ['build', 'fix', 'repair', 'move']):
                    energy_level = 'high'
                # Mental/research tasks = medium energy  
                elif any(word in str(action_words).lower() for word in ['research', 'analyze', 'design', 'write']):
                    energy_level = 'medium'
                # Administrative tasks = low energy
                elif any(word in str(action_words).lower() for word in ['email', 'file', 'organize', 'schedule']):
                    energy_level = 'low'
                
                # High complexity usually requires more energy
                if cognitive_load == 'high':
                    energy_level = 'high'
                elif cognitive_load == 'low' and energy_level == 'medium':
                    energy_level = 'low'
            
            # Update YOLO fields
            task.cognitive_load = cognitive_load
            task.ai_analysis = json.dumps(analysis, default=str)  # Handle datetime serialization
            task.last_analyzed = datetime.now()
            task.energy_level = energy_level
            
            # Apply AI recommendations to core scheduling properties
            if apply_recommendations and ai_insights:
                changes_made = []
                
                # Update duration from AI recommendation
                duration_analysis = ai_insights.get('duration_analysis', {})
                if duration_analysis.get('recommended_minutes'):
                    new_duration = int(duration_analysis['recommended_minutes'])
                    if new_duration != task.duration:
                        task.duration = new_duration
                        changes_made.append(f"duration: {original_duration} → {new_duration} min")
                
                # Update urgency from AI assessment
                scheduling = ai_insights.get('scheduling', {})
                if scheduling.get('urgency_assessment'):
                    new_urgency = int(scheduling['urgency_assessment'])
                    if new_urgency != task.urgency:
                        task.urgency = new_urgency
                        changes_made.append(f"urgency: {original_urgency} → {new_urgency}")
                
                # Update divisibility properties
                task_structure = ai_insights.get('task_structure', {})
                if 'is_divisible' in task_structure:
                    task.is_divisible = bool(task_structure['is_divisible'])
                    if task_structure.get('min_chunk_minutes'):
                        task.min_chunk_size = int(task_structure['min_chunk_minutes'])
                        changes_made.append(f"divisible: {task.is_divisible}, chunk_size: {task.min_chunk_size}")
                
                # Update weather requirements
                environment = ai_insights.get('environment', {})
                if environment.get('weather_requirements'):
                    task.required_weather = environment['weather_requirements']
                    changes_made.append(f"weather: {task.required_weather}")
                
                # Log the changes applied
                if changes_made:
                    self.logger.info(f"Applied AI recommendations to task {task_id}: {', '.join(changes_made)}")
                else:
                    self.logger.info(f"No core property changes needed for task {task_id}")
            
            # Commit to database
            db.session.commit()
            
            self.logger.info(f"Saved analysis to database for task {task_id}: "
                           f"cognitive_load={cognitive_load}, energy_level={energy_level}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving analysis to database for task {task_id}: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return False
    
    def analyze_and_save_task(self, task_id: str, apply_recommendations: bool = True) -> Dict[str, Any]:
        """
        Convenience method to analyze a task and automatically save to database
        
        Args:
            task_id: The task to analyze
            apply_recommendations: Whether to apply AI recommendations to core task properties
        
        Returns:
            - analysis: The full analysis results
            - saved_to_db: Whether database save was successful
            - yolo_fields: The extracted YOLO field values that were saved
            - changes_applied: List of changes made to core properties (if apply_recommendations=True)
        """
        try:
            # Get the task
            task = Task.query.get(task_id)
            if not task:
                return {
                    'success': False,
                    'error': f'Task {task_id} not found',
                    'task_id': task_id
                }
            
            task_dict = task.to_dict()
            
            # Get context for richer analysis
            context = self.get_task_context(task_id)
            
            # Perform analysis with database save
            analysis = self.analyze_task_comprehensive(task_dict, context, save_to_db=True, apply_recommendations=apply_recommendations)
            
            # Extract the YOLO values that were saved
            complexity = analysis.get('complexity_assessment', {})
            cognitive_load = complexity.get('complexity_level', 'medium')
            
            # Determine energy level (same logic as _save_analysis_to_database)
            energy_level = 'medium'
            context_enhancement = analysis.get('context_enhancement', {})
            action_words = context_enhancement.get('action_words', [])
            
            if any(word in str(action_words).lower() for word in ['build', 'fix', 'repair', 'move']):
                energy_level = 'high'
            elif any(word in str(action_words).lower() for word in ['research', 'analyze', 'design', 'write']):
                energy_level = 'medium'
            elif any(word in str(action_words).lower() for word in ['email', 'file', 'organize', 'schedule']):
                energy_level = 'low'
            
            if cognitive_load == 'high':
                energy_level = 'high'
            elif cognitive_load == 'low' and energy_level == 'medium':
                energy_level = 'low'
            
            return {
                'success': True,
                'task_id': task_id,
                'task_title': task_dict.get('title', 'Unknown'),
                'analysis': analysis,
                'saved_to_db': True,
                'yolo_fields': {
                    'cognitive_load': cognitive_load,
                    'energy_level': energy_level,
                    'last_analyzed': datetime.now().isoformat(),
                    'ai_analysis_summary': f"Complexity: {cognitive_load}, Energy: {energy_level}, Source: {analysis.get('analysis_source', 'unknown')}"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in analyze_and_save_task for {task_id}: {e}")
            return {
                'success': False,
                'error': f"Analysis and save failed: {str(e)}",
                'task_id': task_id,
                'saved_to_db': False
            }

# Global service instance
_claude_task_analyzer: Optional[ClaudeTaskAnalyzer] = None

def get_claude_task_analyzer() -> ClaudeTaskAnalyzer:
    """Get the global Claude task analyzer instance"""
    global _claude_task_analyzer
    if not _claude_task_analyzer:
        _claude_task_analyzer = ClaudeTaskAnalyzer()
    return _claude_task_analyzer