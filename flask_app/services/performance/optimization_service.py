"""
Database Optimization Service

Provides database query optimization, index analysis, connection pooling,
and response optimization features for improved API performance.

Features:
- Database index analysis and creation
- Query performance profiling
- Connection pool optimization
- SQLAlchemy optimization
- Response compression
- Query result optimization
- Eager loading strategies
"""

import time
import gzip
import json
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass

from flask import current_app, request, Response
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Analysis results for a database query."""
    query: str
    execution_time: float
    table_scans: List[str]
    index_usage: List[str]
    recommendations: List[str]
    complexity_score: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'execution_time': self.execution_time,
            'table_scans': self.table_scans,
            'index_usage': self.index_usage,
            'recommendations': self.recommendations,
            'complexity_score': self.complexity_score
        }


@dataclass
class IndexRecommendation:
    """Database index recommendation."""
    table: str
    columns: List[str]
    index_type: str
    estimated_benefit: str
    priority: int
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'table': self.table,
            'columns': self.columns,
            'index_type': self.index_type,
            'estimated_benefit': self.estimated_benefit,
            'priority': self.priority,
            'reason': self.reason
        }


class OptimizationService:
    """Database and response optimization service."""
    
    def __init__(self):
        self.query_log: List[QueryAnalysis] = []
        self.slow_query_threshold = 100  # milliseconds
        self.compression_threshold = 1024  # bytes
        self.max_query_log_size = 1000
        
        # Index recommendations cache
        self._index_recommendations: List[IndexRecommendation] = []
        self._last_index_analysis = None
        
        # Performance counters
        self.stats = {
            'queries_analyzed': 0,
            'slow_queries_detected': 0,
            'indexes_recommended': 0,
            'compression_savings': 0,
            'total_response_time_saved': 0
        }
        
        logger.info("Database optimization service initialized")
    
    def analyze_database_schema(self, db) -> Dict[str, Any]:
        """Analyze database schema for optimization opportunities."""
        try:
            engine = db.engine
            inspector = inspect(engine)
            
            analysis = {
                'tables': {},
                'indexes': {},
                'recommendations': [],
                'statistics': {
                    'total_tables': 0,
                    'total_indexes': 0,
                    'missing_indexes': 0
                }
            }
            
            tables = inspector.get_table_names()
            analysis['statistics']['total_tables'] = len(tables)
            
            for table_name in tables:
                table_info = self._analyze_table(inspector, table_name)
                analysis['tables'][table_name] = table_info
                
                # Get existing indexes
                indexes = inspector.get_indexes(table_name)
                analysis['indexes'][table_name] = indexes
                analysis['statistics']['total_indexes'] += len(indexes)
                
                # Generate recommendations
                recommendations = self._generate_index_recommendations(table_name, table_info, indexes)
                analysis['recommendations'].extend(recommendations)
                analysis['statistics']['missing_indexes'] += len(recommendations)
            
            # Cache recommendations
            self._index_recommendations = analysis['recommendations']
            self._last_index_analysis = datetime.now()
            self.stats['indexes_recommended'] = len(analysis['recommendations'])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing database schema: {e}")
            return {'error': str(e)}
    
    def _analyze_table(self, inspector, table_name: str) -> Dict[str, Any]:
        """Analyze individual table structure."""
        try:
            columns = inspector.get_columns(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            primary_key = inspector.get_primary_keys(table_name)
            
            return {
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': str(col.get('default', '')),
                        'primary_key': col['name'] in primary_key
                    }
                    for col in columns
                ],
                'foreign_keys': [
                    {
                        'constrained_columns': fk['constrained_columns'],
                        'referred_table': fk['referred_table'],
                        'referred_columns': fk['referred_columns']
                    }
                    for fk in foreign_keys
                ],
                'primary_key': primary_key,
                'row_count': self._estimate_table_size(table_name)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {e}")
            return {'error': str(e)}
    
    def _estimate_table_size(self, table_name: str) -> int:
        """Estimate table row count."""
        try:
            # Simple count estimation - could be optimized for large tables
            from models import db
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
        except Exception:
            return 0
    
    def _generate_index_recommendations(self, table_name: str, table_info: Dict[str, Any], 
                                      existing_indexes: List[Dict]) -> List[IndexRecommendation]:
        """Generate index recommendations for a table."""
        recommendations = []
        
        # Get existing index columns
        existing_index_columns = set()
        for idx in existing_indexes:
            for col in idx['column_names']:
                existing_index_columns.add(col)
        
        # Common patterns that benefit from indexes
        columns = [col['name'] for col in table_info.get('columns', [])]
        
        # Recommend indexes for common query patterns
        index_candidates = []
        
        # Foreign key columns
        for fk in table_info.get('foreign_keys', []):
            for col in fk['constrained_columns']:
                if col not in existing_index_columns:
                    index_candidates.append({
                        'columns': [col],
                        'reason': 'Foreign key relationship',
                        'priority': 8
                    })
        
        # Common filter columns based on table name and column patterns
        filter_patterns = {
            'status': 'Frequently filtered status field',
            'created_at': 'Timestamp ordering and filtering',
            'updated_at': 'Recent updates filtering',
            'is_active': 'Boolean filter field',
            'is_completed': 'Completion status filtering',
            'priority': 'Priority-based sorting',
            'type': 'Type-based filtering',
            'category': 'Category filtering'
        }
        
        for col in columns:
            if col not in existing_index_columns:
                for pattern, reason in filter_patterns.items():
                    if pattern in col.lower():
                        index_candidates.append({
                            'columns': [col],
                            'reason': reason,
                            'priority': 6
                        })
                        break
        
        # Composite indexes for common query patterns
        if table_name in ['tasks', 'events']:
            # Status + timestamp combinations
            if 'status' in columns and 'created_at' in columns:
                composite_cols = ['status', 'created_at']
                if not any(set(composite_cols).issubset(set(idx['column_names'])) for idx in existing_indexes):
                    index_candidates.append({
                        'columns': composite_cols,
                        'reason': 'Status filtering with timestamp ordering',
                        'priority': 9
                    })
        
        # Create recommendations from candidates
        for candidate in index_candidates:
            row_count = table_info.get('row_count', 0)
            benefit = self._estimate_index_benefit(row_count, len(candidate['columns']))
            
            recommendation = IndexRecommendation(
                table=table_name,
                columns=candidate['columns'],
                index_type='btree',
                estimated_benefit=benefit,
                priority=candidate['priority'],
                reason=candidate['reason']
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _estimate_index_benefit(self, row_count: int, column_count: int) -> str:
        """Estimate performance benefit of an index."""
        if row_count < 100:
            return 'minimal'
        elif row_count < 1000:
            return 'low'
        elif row_count < 10000:
            return 'moderate'
        else:
            # More columns generally mean better selectivity for composite indexes
            benefit_multiplier = min(column_count * 0.5, 2.0)
            if row_count > 100000:
                return 'high' if benefit_multiplier > 1.5 else 'moderate'
            else:
                return 'moderate' if benefit_multiplier > 1.0 else 'low'
    
    def create_recommended_indexes(self, db, max_indexes: int = 5) -> Dict[str, Any]:
        """Create the most important recommended indexes."""
        if not self._index_recommendations:
            return {'error': 'No index recommendations available. Run analyze_database_schema first.'}
        
        # Sort by priority and take top recommendations
        top_recommendations = sorted(
            self._index_recommendations, 
            key=lambda x: x.priority, 
            reverse=True
        )[:max_indexes]
        
        results = {
            'created': [],
            'failed': [],
            'skipped': []
        }
        
        for rec in top_recommendations:
            try:
                # Check if index already exists
                inspector = inspect(db.engine)
                existing_indexes = inspector.get_indexes(rec.table)
                
                index_exists = any(
                    set(rec.columns) == set(idx['column_names'])
                    for idx in existing_indexes
                )
                
                if index_exists:
                    results['skipped'].append({
                        'table': rec.table,
                        'columns': rec.columns,
                        'reason': 'Index already exists'
                    })
                    continue
                
                # Create index
                index_name = f"idx_{rec.table}_{'_'.join(rec.columns)}"
                columns_str = ', '.join(rec.columns)
                
                create_sql = f"CREATE INDEX {index_name} ON {rec.table} ({columns_str})"
                
                db.session.execute(text(create_sql))
                db.session.commit()
                
                results['created'].append({
                    'table': rec.table,
                    'columns': rec.columns,
                    'index_name': index_name,
                    'estimated_benefit': rec.estimated_benefit
                })
                
                logger.info(f"Created index: {index_name}")
                
            except Exception as e:
                results['failed'].append({
                    'table': rec.table,
                    'columns': rec.columns,
                    'error': str(e)
                })
                logger.error(f"Failed to create index on {rec.table}: {e}")
        
        return results
    
    def analyze_query_performance(self, query: str, execution_time: float) -> QueryAnalysis:
        """Analyze query performance and provide recommendations."""
        analysis = QueryAnalysis(
            query=query[:500] + '...' if len(query) > 500 else query,
            execution_time=execution_time,
            table_scans=[],
            index_usage=[],
            recommendations=[],
            complexity_score=0
        )
        
        # Basic query analysis
        query_lower = query.lower()
        
        # Detect table scans
        if 'select * from' in query_lower:
            analysis.table_scans.append('Full table scan detected')
            analysis.recommendations.append('Consider selecting only needed columns')
            analysis.complexity_score += 2
        
        # Detect missing WHERE clauses on large tables
        if 'where' not in query_lower and any(table in query_lower for table in ['tasks', 'events']):
            analysis.recommendations.append('Consider adding WHERE clause to limit results')
            analysis.complexity_score += 3
        
        # Detect missing ORDER BY with LIMIT
        if 'limit' in query_lower and 'order by' not in query_lower:
            analysis.recommendations.append('Add ORDER BY clause with LIMIT for consistent results')
            analysis.complexity_score += 1
        
        # Detect complex JOINs
        join_count = query_lower.count('join')
        if join_count > 3:
            analysis.recommendations.append('Consider breaking complex joins into smaller queries')
            analysis.complexity_score += join_count
        
        # Performance assessment
        if execution_time > self.slow_query_threshold:
            self.stats['slow_queries_detected'] += 1
            
            if execution_time > 1000:  # > 1 second
                analysis.recommendations.append('Query is very slow - consider optimization')
                analysis.complexity_score += 5
            elif execution_time > 500:  # > 500ms
                analysis.recommendations.append('Query is slow - review indexes and query structure')
                analysis.complexity_score += 3
        
        # Add to query log
        self.query_log.append(analysis)
        if len(self.query_log) > self.max_query_log_size:
            self.query_log = self.query_log[-self.max_query_log_size:]
        
        self.stats['queries_analyzed'] += 1
        
        return analysis
    
    def optimize_sqlalchemy_config(self, app) -> Dict[str, Any]:
        """Optimize SQLAlchemy configuration for better performance."""
        optimizations = {
            'applied': [],
            'recommendations': [],
            'current_config': {}
        }
        
        try:
            # Get current configuration
            current_config = {
                'pool_size': app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_size', 5),
                'max_overflow': app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('max_overflow', 10),
                'pool_timeout': app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_timeout', 30),
                'pool_recycle': app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_recycle', -1),
                'echo': app.config.get('SQLALCHEMY_ECHO', False)
            }
            optimizations['current_config'] = current_config
            
            # Recommended optimizations
            recommended_config = {
                'pool_size': 20,  # Increase pool size for better concurrency
                'max_overflow': 30,  # Allow more overflow connections
                'pool_timeout': 30,  # Keep reasonable timeout
                'pool_recycle': 3600,  # Recycle connections every hour
                'pool_pre_ping': True,  # Test connections before use
                'echo': False  # Disable query logging in production
            }
            
            # Apply optimizations
            if not hasattr(app.config, 'SQLALCHEMY_ENGINE_OPTIONS'):
                app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
            
            for key, value in recommended_config.items():
                if key not in app.config['SQLALCHEMY_ENGINE_OPTIONS'] or app.config['SQLALCHEMY_ENGINE_OPTIONS'][key] != value:
                    optimizations['applied'].append(f"Set {key} to {value}")
                    app.config['SQLALCHEMY_ENGINE_OPTIONS'][key] = value
            
            # Additional recommendations
            optimizations['recommendations'].extend([
                'Consider using connection pooling with Redis for session storage',
                'Enable query result caching for frequently accessed data',
                'Use eager loading for relationships to reduce N+1 queries',
                'Consider read replicas for read-heavy workloads'
            ])
            
            logger.info("SQLAlchemy configuration optimized")
            
        except Exception as e:
            logger.error(f"Error optimizing SQLAlchemy config: {e}")
            optimizations['error'] = str(e)
        
        return optimizations
    
    def compress_response(self, data: Any, threshold: int = None) -> Tuple[bytes, bool]:
        """Compress response data if it exceeds threshold."""
        threshold = threshold or self.compression_threshold
        
        try:
            # Serialize data
            if isinstance(data, (dict, list)):
                json_data = json.dumps(data, separators=(',', ':'), default=str)
            else:
                json_data = str(data)
            
            json_bytes = json_data.encode('utf-8')
            
            # Compress if above threshold
            if len(json_bytes) > threshold:
                compressed = gzip.compress(json_bytes)
                savings = len(json_bytes) - len(compressed)
                self.stats['compression_savings'] += savings
                
                logger.debug(f"Compressed response: {len(json_bytes)} -> {len(compressed)} bytes ({savings} saved)")
                return compressed, True
            
            return json_bytes, False
            
        except Exception as e:
            logger.error(f"Error compressing response: {e}")
            return json_data.encode('utf-8'), False
    
    def get_slow_queries(self, min_execution_time: float = None) -> List[Dict[str, Any]]:
        """Get list of slow queries."""
        threshold = min_execution_time or self.slow_query_threshold
        
        slow_queries = [
            analysis.to_dict() 
            for analysis in self.query_log 
            if analysis.execution_time > threshold
        ]
        
        # Sort by execution time (slowest first)
        slow_queries.sort(key=lambda x: x['execution_time'], reverse=True)
        
        return slow_queries
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization service statistics."""
        return {
            **self.stats,
            'query_log_size': len(self.query_log),
            'index_recommendations_count': len(self._index_recommendations),
            'last_index_analysis': self._last_index_analysis.isoformat() if self._last_index_analysis else None,
            'avg_query_time': sum(q.execution_time for q in self.query_log) / len(self.query_log) if self.query_log else 0
        }
    
    def clear_query_log(self):
        """Clear the query performance log."""
        self.query_log.clear()
        logger.info("Query performance log cleared")


# Global optimization service instance
db_optimizer: Optional[OptimizationService] = None


def init_optimization_service(app):
    """Initialize optimization service with Flask app."""
    global db_optimizer
    
    db_optimizer = OptimizationService()
    app.db_optimizer = db_optimizer
    
    # Apply SQLAlchemy optimizations
    db_optimizer.optimize_sqlalchemy_config(app)
    
    return db_optimizer