"""
Advanced Search Service for TaskMaster

Provides comprehensive full-text search capabilities with faceting, suggestions,
and advanced query processing. Uses SQLite FTS5 for high-performance search.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
from flask import current_app
from sqlalchemy import text, and_, or_, func, distinct
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import json
import re
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

from models import db, Task, Event, Initiative, Project, Meal, Dish


@dataclass
class SearchResult:
    """Structured search result with relevance scoring"""
    id: str
    type: str  # task, event, initiative, project, meal, dish
    title: str
    description: str
    relevance_score: float
    snippet: str
    metadata: Dict[str, Any]


@dataclass
class FacetResult:
    """Faceted search result with category counts"""
    value: str
    count: int
    filter_key: str


@dataclass
class SearchResponse:
    """Complete search response with results and metadata"""
    results: List[SearchResult]
    total_count: int
    facets: Dict[str, List[FacetResult]]
    query_time_ms: float
    suggestions: List[str]
    corrected_query: Optional[str]


class SearchIndex:
    """FTS5 search index management"""
    
    def __init__(self):
        self.fts_tables = {
            'tasks_fts': 'tasks',
            'events_fts': 'events', 
            'initiatives_fts': 'initiatives',
            'projects_fts': 'projects',
            'meals_fts': 'meals',
            'dishes_fts': 'dishes'
        }
    
    def initialize_fts_tables(self):
        """Create FTS5 virtual tables for full-text search"""
        try:
            # Create FTS tables for each searchable entity
            fts_queries = {
                'tasks_fts': """
                    CREATE VIRTUAL TABLE IF NOT EXISTS tasks_fts USING fts5(
                        id UNINDEXED, title, description, notes,
                        content='tasks', content_rowid='rowid'
                    )
                """,
                'events_fts': """
                    CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
                        id UNINDEXED, title, description, location,
                        content='events', content_rowid='rowid'
                    )
                """,
                'initiatives_fts': """
                    CREATE VIRTUAL TABLE IF NOT EXISTS initiatives_fts USING fts5(
                        id UNINDEXED, title, description, notes,
                        content='initiatives', content_rowid='rowid'
                    )
                """,
                'projects_fts': """
                    CREATE VIRTUAL TABLE IF NOT EXISTS projects_fts USING fts5(
                        id UNINDEXED, title, description, notes,
                        content='projects', content_rowid='rowid'
                    )
                """,
                'meals_fts': """
                    CREATE VIRTUAL TABLE IF NOT EXISTS meals_fts USING fts5(
                        id UNINDEXED, name, description, notes,
                        content='meals', content_rowid='rowid'
                    )
                """,
                'dishes_fts': """
                    CREATE VIRTUAL TABLE IF NOT EXISTS dishes_fts USING fts5(
                        id UNINDEXED, name, description, category,
                        content='dishes', content_rowid='rowid'
                    )
                """
            }
            
            for table_name, query in fts_queries.items():
                db.session.execute(text(query))
            
            db.session.commit()
            current_app.logger.info("FTS5 tables initialized successfully")
            
        except Exception as e:
            current_app.logger.error(f"Failed to initialize FTS tables: {e}")
            db.session.rollback()
            raise
    
    def rebuild_index(self, table_name: str = None):
        """Rebuild FTS index for specific table or all tables"""
        try:
            tables_to_rebuild = [table_name] if table_name else list(self.fts_tables.keys())
            
            for fts_table in tables_to_rebuild:
                # Rebuild the FTS index
                db.session.execute(text(f"INSERT INTO {fts_table}({fts_table}) VALUES('rebuild')"))
            
            db.session.commit()
            current_app.logger.info(f"FTS index rebuilt for: {', '.join(tables_to_rebuild)}")
            
        except Exception as e:
            current_app.logger.error(f"Failed to rebuild FTS index: {e}")
            db.session.rollback()
            raise
    
    def update_document(self, table_name: str, document_id: str):
        """Update specific document in FTS index"""
        try:
            fts_table = f"{table_name}_fts"
            if fts_table in self.fts_tables:
                # Delete old entry
                db.session.execute(
                    text(f"DELETE FROM {fts_table} WHERE id = :id"),
                    {'id': document_id}
                )
                
                # Re-insert will happen automatically via FTS content table
                db.session.execute(text(f"INSERT INTO {fts_table}({fts_table}) VALUES('rebuild')"))
                db.session.commit()
                
        except Exception as e:
            current_app.logger.error(f"Failed to update FTS document: {e}")
            db.session.rollback()


class SearchQueryProcessor:
    """Advanced query processing with DSL support"""
    
    def __init__(self):
        self.operators = ['AND', 'OR', 'NOT', '-', '+', '"']
        self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process search query and extract components"""
        processed = {
            'original_query': query,
            'cleaned_query': self._clean_query(query),
            'terms': self._extract_terms(query),
            'phrases': self._extract_phrases(query),
            'filters': self._extract_filters(query),
            'fts_query': self._build_fts_query(query)
        }
        
        return processed
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize search query"""
        # Remove special characters except those used in search
        cleaned = re.sub(r'[^\w\s\-\+\":]', ' ', query)
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
    
    def _extract_terms(self, query: str) -> List[str]:
        """Extract individual search terms"""
        # Remove phrases first
        query_without_phrases = re.sub(r'"[^"]*"', '', query)
        # Split on whitespace and remove stop words
        terms = [term.lower() for term in query_without_phrases.split() 
                if term.lower() not in self.stop_words and len(term) > 2]
        return terms
    
    def _extract_phrases(self, query: str) -> List[str]:
        """Extract quoted phrases"""
        phrases = re.findall(r'"([^"]*)"', query)
        return [phrase.strip() for phrase in phrases if phrase.strip()]
    
    def _extract_filters(self, query: str) -> Dict[str, str]:
        """Extract field-specific filters (e.g., type:task)"""
        filters = {}
        filter_pattern = r'(\w+):(\w+)'
        matches = re.findall(filter_pattern, query)
        
        for field, value in matches:
            filters[field.lower()] = value.lower()
        
        return filters
    
    def _build_fts_query(self, query: str) -> str:
        """Build FTS5-compatible query string"""
        # Remove field filters for FTS query
        fts_query = re.sub(r'\w+:\w+', '', query)
        
        # Handle quoted phrases
        phrases = self._extract_phrases(fts_query)
        for phrase in phrases:
            fts_query = fts_query.replace(f'"{phrase}"', f'"{phrase}"')
        
        # Handle terms with operators
        terms = self._extract_terms(fts_query)
        if terms:
            # Build basic OR query for terms
            term_query = ' OR '.join(terms)
            return term_query if not phrases else f'({term_query}) OR ({" ".join(phrases)})'
        
        return query.strip() if query.strip() else '*'


class FacetedSearch:
    """Faceted search implementation with category counts"""
    
    def __init__(self):
        self.facet_fields = {
            'type': {
                'field': 'type',
                'display_name': 'Content Type'
            },
            'status': {
                'field': 'status', 
                'display_name': 'Status'
            },
            'priority': {
                'field': 'priority',
                'display_name': 'Priority'
            },
            'date_range': {
                'field': 'created_at',
                'display_name': 'Date Created'
            }
        }
    
    def generate_facets(self, base_results: List[SearchResult]) -> Dict[str, List[FacetResult]]:
        """Generate facet counts from search results"""
        facets = defaultdict(lambda: defaultdict(int))
        
        for result in base_results:
            # Type facet
            facets['type'][result.type] += 1
            
            # Status facet (if available in metadata)
            if 'status' in result.metadata:
                facets['status'][result.metadata['status']] += 1
            
            # Priority facet (if available in metadata)
            if 'priority' in result.metadata:
                facets['priority'][result.metadata['priority']] += 1
            
            # Date range facet
            if 'created_at' in result.metadata:
                date_range = self._get_date_range(result.metadata['created_at'])
                facets['date_range'][date_range] += 1
        
        # Convert to FacetResult objects
        formatted_facets = {}
        for facet_name, values in facets.items():
            formatted_facets[facet_name] = [
                FacetResult(value=value, count=count, filter_key=f"{facet_name}:{value}")
                for value, count in sorted(values.items(), key=lambda x: x[1], reverse=True)
            ]
        
        return formatted_facets
    
    def _get_date_range(self, date_str: str) -> str:
        """Categorize date into range buckets"""
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            now = datetime.now()
            diff = now - date_obj
            
            if diff.days <= 1:
                return 'Today'
            elif diff.days <= 7:
                return 'This Week'
            elif diff.days <= 30:
                return 'This Month'
            elif diff.days <= 365:
                return 'This Year'
            else:
                return 'Older'
        except:
            return 'Unknown'


class SearchService:
    """Main search service coordinating all search functionality"""
    
    def __init__(self):
        self.index = SearchIndex()
        self.query_processor = SearchQueryProcessor()
        self.faceted_search = FacetedSearch()
        self._ensure_fts_initialized()
    
    def _ensure_fts_initialized(self):
        """Ensure FTS tables are initialized"""
        try:
            # Check if FTS tables exist
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'"))
            existing_fts = [row[0] for row in result.fetchall()]
            
            if len(existing_fts) < len(self.index.fts_tables):
                current_app.logger.info("Initializing FTS tables...")
                self.index.initialize_fts_tables()
                self.rebuild_all_indexes()
                
        except Exception as e:
            current_app.logger.error(f"Failed to ensure FTS initialization: {e}")
    
    def search(self, query: str, entity_types: List[str] = None, 
              limit: int = 20, offset: int = 0, 
              include_facets: bool = True) -> SearchResponse:
        """Perform comprehensive search across all entities"""
        start_time = datetime.now()
        
        try:
            # Process the query
            processed_query = self.query_processor.process_query(query)
            
            # Determine which entity types to search
            if not entity_types:
                entity_types = ['tasks', 'events', 'initiatives', 'projects', 'meals', 'dishes']
            
            # Filter by explicit type filters
            if 'type' in processed_query['filters']:
                entity_types = [processed_query['filters']['type']]
            
            # Perform FTS search for each entity type
            all_results = []
            for entity_type in entity_types:
                results = self._search_entity_type(entity_type, processed_query)
                all_results.extend(results)
            
            # Sort by relevance score
            all_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Generate facets before pagination
            facets = {}
            if include_facets:
                facets = self.faceted_search.generate_facets(all_results)
            
            # Apply pagination
            total_count = len(all_results)
            paginated_results = all_results[offset:offset + limit]
            
            # Generate suggestions (simple implementation)
            suggestions = self._generate_suggestions(query, all_results)
            
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return SearchResponse(
                results=paginated_results,
                total_count=total_count,
                facets=facets,
                query_time_ms=query_time,
                suggestions=suggestions,
                corrected_query=None  # TODO: Implement spell correction
            )
            
        except Exception as e:
            current_app.logger.error(f"Search failed: {e}")
            return SearchResponse(
                results=[],
                total_count=0,
                facets={},
                query_time_ms=0,
                suggestions=[],
                corrected_query=None
            )
    
    def _search_entity_type(self, entity_type: str, processed_query: Dict) -> List[SearchResult]:
        """Search specific entity type using FTS"""
        try:
            fts_table = f"{entity_type}_fts"
            fts_query = processed_query['fts_query']
            
            # Build FTS search query
            search_sql = f"""
                SELECT id, rank, snippet({fts_table}, 1, '[', ']', '...', 32) as snippet
                FROM {fts_table}
                WHERE {fts_table} MATCH :query
                ORDER BY rank
                LIMIT 100
            """
            
            fts_results = db.session.execute(text(search_sql), {'query': fts_query}).fetchall()
            
            if not fts_results:
                return []
            
            # Get full entity data
            entity_ids = [result.id for result in fts_results]
            entities = self._get_entities_by_type_and_ids(entity_type, entity_ids)
            
            # Create SearchResult objects
            results = []
            for fts_result in fts_results:
                entity = entities.get(fts_result.id)
                if entity:
                    search_result = self._create_search_result(
                        entity, entity_type, fts_result.rank, fts_result.snippet
                    )
                    results.append(search_result)
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"Failed to search {entity_type}: {e}")
            return []
    
    def _get_entities_by_type_and_ids(self, entity_type: str, ids: List[str]) -> Dict[str, Any]:
        """Fetch full entity objects by type and IDs"""
        model_map = {
            'tasks': Task,
            'events': Event,
            'initiatives': Initiative,
            'projects': Project,
            'meals': Meal,
            'dishes': Dish
        }
        
        model = model_map.get(entity_type)
        if not model:
            return {}
        
        entities = model.query.filter(model.id.in_(ids)).all()
        return {entity.id: entity for entity in entities}
    
    def _create_search_result(self, entity: Any, entity_type: str, 
                            rank: float, snippet: str) -> SearchResult:
        """Create SearchResult from entity object"""
        # Get title field based on entity type
        title_field = 'title' if hasattr(entity, 'title') else 'name'
        title = getattr(entity, title_field, 'Unknown')
        
        # Get description
        description = getattr(entity, 'description', '') or ''
        
        # Calculate relevance score (inverse of rank)
        relevance_score = 1.0 / (rank + 1)
        
        # Build metadata
        metadata = {
            'created_at': entity.created_at.isoformat() if hasattr(entity, 'created_at') else None,
            'updated_at': entity.updated_at.isoformat() if hasattr(entity, 'updated_at') else None
        }
        
        # Add type-specific metadata
        if hasattr(entity, 'status'):
            metadata['status'] = entity.status
        if hasattr(entity, 'priority'):
            metadata['priority'] = entity.priority
        if hasattr(entity, 'due_date'):
            metadata['due_date'] = entity.due_date.isoformat() if entity.due_date else None
        
        return SearchResult(
            id=entity.id,
            type=entity_type.rstrip('s'),  # Remove plural
            title=title,
            description=description,
            relevance_score=relevance_score,
            snippet=snippet,
            metadata=metadata
        )
    
    def _generate_suggestions(self, query: str, results: List[SearchResult]) -> List[str]:
        """Generate search suggestions based on query and results"""
        suggestions = []
        
        # Extract common terms from high-relevance results
        if results:
            top_results = results[:5]  # Top 5 results
            terms = set()
            
            for result in top_results:
                # Extract words from title and description
                text = f"{result.title} {result.description}".lower()
                words = re.findall(r'\b\w{3,}\b', text)
                terms.update(words[:3])  # Limit per result
            
            # Filter and format suggestions
            query_lower = query.lower()
            suggestions = [
                term for term in sorted(terms)
                if term not in query_lower and len(term) > 3
            ][:5]  # Limit suggestions
        
        return suggestions
    
    def rebuild_all_indexes(self):
        """Rebuild all FTS indexes"""
        try:
            for table_name in self.index.fts_tables.keys():
                self.index.rebuild_index(table_name)
            current_app.logger.info("All FTS indexes rebuilt successfully")
        except Exception as e:
            current_app.logger.error(f"Failed to rebuild indexes: {e}")
            raise
    
    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get auto-complete suggestions for partial queries"""
        # This is a simplified implementation
        # In production, you'd want to use a dedicated suggestion index
        suggestions = []
        
        if len(partial_query) >= 2:
            # Search for entities with titles starting with partial query
            query_pattern = f"{partial_query}%"
            
            # Search across different entity types
            for entity_type, model in [
                ('tasks', Task), ('events', Event), ('initiatives', Initiative),
                ('projects', Project), ('meals', Meal), ('dishes', Dish)
            ]:
                title_field = 'title' if hasattr(model, 'title') else 'name'
                column = getattr(model, title_field)
                
                results = model.query.filter(
                    column.like(query_pattern)
                ).limit(limit // 6).all()  # Distribute across types
                
                for result in results:
                    title = getattr(result, title_field)
                    if title and title not in suggestions:
                        suggestions.append(title)
        
        return suggestions[:limit]


# Global search service instance (lazy-loaded)
search_service = None

def get_search_service():
    """Get or create the search service instance"""
    global search_service
    if search_service is None:
        search_service = SearchService()
    return search_service