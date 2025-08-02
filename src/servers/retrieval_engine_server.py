#!/usr/bin/env python3
"""
AI Agent Context Management System - Retrieval Engine Server

This MCP server handles intelligent context retrieval with cross-technology 
pattern matching, semantic search, and relevance scoring optimized for 
solo developers working across multiple technology stacks.

Port: 8002
"""

import asyncio
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import chromadb
from chromadb.config import Settings
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
import os
from dotenv import load_dotenv

from fastmcp import FastMCP

load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Retrieval Engine Server")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorSearchEngine:
    """Handles vector-based semantic search across projects"""
    
    def __init__(self, chroma_path: str = "./chroma_db"):
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(allow_reset=True)
        )
        self.collections = {}
        
    async def search_similar_contexts(
        self, 
        query: str, 
        technology: str,
        project_id: Optional[str] = None,
        cross_tech: bool = True,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar contexts with technology-aware matching"""
        
        results = []
        
        # Primary search in target technology
        if technology in self.collections:
            collection = self.collections[technology]
            primary_results = collection.query(
                query_texts=[query],
                n_results=min(limit, 5),
                where={"project_id": project_id} if project_id else None
            )
            
            for i, doc in enumerate(primary_results['documents'][0]):
                metadata = primary_results['metadatas'][0][i]
                distance = primary_results['distances'][0][i]
                
                results.append({
                    'content': doc,
                    'metadata': metadata,
                    'relevance_score': 1.0 - distance,
                    'match_type': 'exact_tech',
                    'technology': technology
                })
        
        # Cross-technology search if enabled
        if cross_tech and len(results) < limit:
            cross_tech_mappings = {
                'swift': ['javascript', 'react'],
                'android': ['python', 'javascript'],
                'python': ['javascript', 'android'],
                'react': ['swift', 'javascript'],
                'javascript': ['swift', 'python', 'react']
            }
            
            related_techs = cross_tech_mappings.get(technology, [])
            remaining_limit = limit - len(results)
            
            for related_tech in related_techs:
                if related_tech in self.collections and remaining_limit > 0:
                    collection = self.collections[related_tech]
                    cross_results = collection.query(
                        query_texts=[query],
                        n_results=min(remaining_limit // len(related_techs) + 1, 3)
                    )
                    
                    for i, doc in enumerate(cross_results['documents'][0]):
                        metadata = cross_results['metadatas'][0][i]
                        distance = cross_results['distances'][0][i]
                        
                        # Apply cross-technology penalty
                        cross_tech_score = (1.0 - distance) * 0.8
                        
                        results.append({
                            'content': doc,
                            'metadata': metadata,
                            'relevance_score': cross_tech_score,
                            'match_type': 'cross_tech',
                            'technology': related_tech,
                            'original_tech': technology
                        })
                        
                        remaining_limit -= 1
                        if remaining_limit <= 0:
                            break
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:limit]

class PatternMatcher:
    """Advanced pattern matching for code patterns and solutions"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 3)
        )
        self.lda_model = None
        self.pattern_cache = {}
        
    async def find_similar_patterns(
        self, 
        code_snippet: str,
        technology: str,
        pattern_type: str = 'implementation',
        min_similarity: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Find similar code patterns across projects"""
        
        cache_key = f"{technology}_{pattern_type}_{hash(code_snippet)}"
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        # This would connect to the Context Storage Server
        # For now, simulating pattern matching logic
        patterns = await self._query_patterns_database(technology, pattern_type)
        
        if not patterns:
            return []
        
        # Extract text features for comparison
        pattern_texts = [p['code'] + ' ' + p['description'] for p in patterns]
        query_text = code_snippet
        
        # TF-IDF similarity
        all_texts = pattern_texts + [query_text]
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
        
        # Calculate similarities
        similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
        
        similar_patterns = []
        for i, similarity in enumerate(similarities):
            if similarity >= min_similarity:
                pattern = patterns[i].copy()
                pattern['similarity_score'] = float(similarity)
                pattern['match_reason'] = self._explain_match(query_text, pattern_texts[i])
                similar_patterns.append(pattern)
        
        # Sort by similarity
        similar_patterns.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Cache results
        self.pattern_cache[cache_key] = similar_patterns
        return similar_patterns
    
    async def _query_patterns_database(self, technology: str, pattern_type: str) -> List[Dict[str, Any]]:
        """Query patterns from the database (would connect to Context Storage Server)"""
        # Simulated pattern data - in real implementation this would query the database
        return [
            {
                'id': 'pattern_1',
                'code': 'function fetchData() { return api.get("/data"); }',
                'description': 'API data fetching pattern',
                'technology': technology,
                'pattern_type': pattern_type,
                'usage_count': 5,
                'success_rate': 0.9
            }
        ]
    
    def _explain_match(self, query: str, pattern: str) -> str:
        """Generate explanation for why patterns match"""
        # Simple keyword overlap explanation
        query_words = set(query.lower().split())
        pattern_words = set(pattern.lower().split())
        overlap = query_words.intersection(pattern_words)
        
        if len(overlap) > 3:
            return f"High keyword overlap: {', '.join(list(overlap)[:3])}"
        elif len(overlap) > 1:
            return f"Moderate keyword overlap: {', '.join(overlap)}"
        else:
            return "Semantic similarity detected"

class RelevanceScorer:
    """Calculates relevance scores based on multiple factors"""
    
    @staticmethod
    def calculate_comprehensive_score(
        context_item: Dict[str, Any],
        query: str,
        user_profile: Dict[str, Any],
        project_context: Dict[str, Any]
    ) -> float:
        """Calculate comprehensive relevance score"""
        
        base_score = context_item.get('relevance_score', 0.5)
        
        # Recency factor (newer content gets higher score)
        time_factor = RelevanceScorer._calculate_time_factor(
            context_item.get('timestamp', datetime.now().isoformat())
        )
        
        # Technology alignment factor
        tech_factor = RelevanceScorer._calculate_tech_factor(
            context_item.get('technology', ''),
            user_profile.get('current_technology', ''),
            user_profile.get('tech_preferences', {})
        )
        
        # Project relevance factor
        project_factor = RelevanceScorer._calculate_project_factor(
            context_item.get('project_id', ''),
            project_context.get('current_project_id', ''),
            project_context.get('related_projects', [])
        )
        
        # Usage pattern factor
        usage_factor = RelevanceScorer._calculate_usage_factor(
            context_item.get('usage_count', 0),
            context_item.get('success_rate', 0.5)
        )
        
        # Combine factors with weights
        comprehensive_score = (
            base_score * 0.4 +
            time_factor * 0.2 +
            tech_factor * 0.2 +
            project_factor * 0.1 +
            usage_factor * 0.1
        )
        
        return min(1.0, max(0.0, comprehensive_score))
    
    @staticmethod
    def _calculate_time_factor(timestamp_str: str) -> float:
        """Calculate time-based relevance factor"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age_hours = (datetime.now() - timestamp.replace(tzinfo=None)).total_seconds() / 3600
            
            # Recent items (< 24h) get full score
            if age_hours < 24:
                return 1.0
            # Items within a week get partial score
            elif age_hours < 168:  # 7 days
                return 0.8
            # Items within a month get lower score
            elif age_hours < 720:  # 30 days
                return 0.6
            else:
                return 0.4
        except:
            return 0.5
    
    @staticmethod
    def _calculate_tech_factor(item_tech: str, current_tech: str, tech_prefs: Dict) -> float:
        """Calculate technology alignment factor"""
        if item_tech == current_tech:
            return 1.0
        
        # Check cross-technology compatibility
        cross_tech_scores = {
            ('swift', 'react'): 0.8,
            ('swift', 'javascript'): 0.7,
            ('android', 'python'): 0.8,
            ('python', 'javascript'): 0.7,
            ('react', 'javascript'): 0.9
        }
        
        score = cross_tech_scores.get((current_tech, item_tech), 0.5)
        score = cross_tech_scores.get((item_tech, current_tech), score)
        
        return score
    
    @staticmethod
    def _calculate_project_factor(item_project: str, current_project: str, related_projects: List[str]) -> float:
        """Calculate project relevance factor"""
        if item_project == current_project:
            return 1.0
        elif item_project in related_projects:
            return 0.7
        else:
            return 0.3
    
    @staticmethod
    def _calculate_usage_factor(usage_count: int, success_rate: float) -> float:
        """Calculate usage pattern factor"""
        # Normalize usage count (assuming max of 100 uses)
        usage_score = min(1.0, usage_count / 100.0)
        return (usage_score * 0.6) + (success_rate * 0.4)

class DatabaseManager:
    """Manages database connections and queries"""
    
    def __init__(self, db_path: str = "context_management.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    technology TEXT,
                    project_id TEXT,
                    results_count INTEGER,
                    user_interaction TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    async def log_search(self, query: str, technology: str, project_id: str, results_count: int):
        """Log search queries for analytics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO search_analytics (query, technology, project_id, results_count) VALUES (?, ?, ?, ?)",
                (query, technology, project_id, results_count)
            )
    
    async def get_user_profile(self, user_id: str = "default") -> Dict[str, Any]:
        """Get user profile for personalized results"""
        # This would query the Context Storage Server
        # Returning mock data for now
        return {
            'user_id': user_id,
            'current_technology': 'swift',
            'tech_preferences': {
                'swift': 0.9,
                'react': 0.8,
                'python': 0.7,
                'javascript': 0.8,
                'android': 0.6
            },
            'project_history': ['project_1', 'project_2'],
            'search_patterns': ['UI patterns', 'API integration', 'state management']
        }

class RetrievalEngineServer:
    """Main retrieval engine server class"""
    
    def __init__(self):
        self.vector_engine = VectorSearchEngine()
        self.pattern_matcher = PatternMatcher()
        self.relevance_scorer = RelevanceScorer()
        self.db_manager = DatabaseManager()
        
        # Register tools with global MCP server
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @mcp.tool()
        async def intelligent_search(
            query: str,
            technology: str,
            project_id: str = None,
            search_type: str = "semantic",
            include_cross_tech: bool = True,
            limit: int = 10
        ) -> Dict[str, Any]:
            """
            Perform intelligent context search with cross-technology pattern matching.
            
            Args:
                query: Search query or code snippet
                technology: Current technology (swift, android, python, react, javascript)
                project_id: Optional project ID to focus search
                search_type: Type of search (semantic, pattern, hybrid)
                include_cross_tech: Whether to include cross-technology results
                limit: Maximum number of results
            """
            
            try:
                # Get user profile for personalization
                user_profile = await self.db_manager.get_user_profile()
                project_context = {
                    'current_project_id': project_id,
                    'related_projects': user_profile.get('project_history', [])
                }
                
                results = []
                
                if search_type in ["semantic", "hybrid"]:
                    # Semantic search using vector similarity
                    semantic_results = await self.vector_engine.search_similar_contexts(
                        query=query,
                        technology=technology,
                        project_id=project_id,
                        cross_tech=include_cross_tech,
                        limit=limit
                    )
                    results.extend(semantic_results)
                
                if search_type in ["pattern", "hybrid"]:
                    # Pattern-based search for code snippets
                    pattern_results = await self.pattern_matcher.find_similar_patterns(
                        code_snippet=query,
                        technology=technology,
                        pattern_type='implementation'
                    )
                    
                    # Convert pattern results to standard format
                    for pattern in pattern_results:
                        results.append({
                            'content': pattern['code'],
                            'metadata': {
                                'pattern_id': pattern['id'],
                                'description': pattern['description'],
                                'usage_count': pattern['usage_count'],
                                'success_rate': pattern['success_rate']
                            },
                            'relevance_score': pattern['similarity_score'],
                            'match_type': 'pattern',
                            'technology': pattern['technology']
                        })
                
                # Calculate comprehensive relevance scores
                for result in results:
                    result['comprehensive_score'] = self.relevance_scorer.calculate_comprehensive_score(
                        context_item=result,
                        query=query,
                        user_profile=user_profile,
                        project_context=project_context
                    )
                
                # Sort by comprehensive score and remove duplicates
                results = self._deduplicate_results(results)
                results.sort(key=lambda x: x['comprehensive_score'], reverse=True)
                results = results[:limit]
                
                # Log search for analytics
                await self.db_manager.log_search(
                    query=query,
                    technology=technology,
                    project_id=project_id or "none",
                    results_count=len(results)
                )
                
                return {
                    'query': query,
                    'technology': technology,
                    'search_type': search_type,
                    'results_count': len(results),
                    'results': results,
                    'search_metadata': {
                        'include_cross_tech': include_cross_tech,
                        'user_preferences': user_profile.get('tech_preferences', {}),
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(f"Search failed: {str(e)}")
                return {
                    'error': f"Search failed: {str(e)}",
                    'results': [],
                    'results_count': 0
                }
        
        @mcp.tool()
        async def find_related_patterns(
            code_snippet: str,
            technology: str,
            pattern_type: str = "implementation",
            min_similarity: float = 0.6
        ) -> Dict[str, Any]:
            """
            Find code patterns related to a given snippet.
            
            Args:
                code_snippet: Code to find patterns for
                technology: Technology stack
                pattern_type: Type of pattern (implementation, testing, architecture)
                min_similarity: Minimum similarity threshold
            """
            
            try:
                patterns = await self.pattern_matcher.find_similar_patterns(
                    code_snippet=code_snippet,
                    technology=technology,
                    pattern_type=pattern_type,
                    min_similarity=min_similarity
                )
                
                return {
                    'code_snippet': code_snippet,
                    'technology': technology,
                    'pattern_type': pattern_type,
                    'patterns_found': len(patterns),
                    'patterns': patterns
                }
                
            except Exception as e:
                logger.error(f"Pattern search failed: {str(e)}")
                return {
                    'error': f"Pattern search failed: {str(e)}",
                    'patterns': [],
                    'patterns_found': 0
                }
        
        @mcp.tool()
        async def get_cross_technology_insights(
            current_tech: str,
            target_tech: str,
            context: str = ""
        ) -> Dict[str, Any]:
            """
            Get insights for translating concepts between technologies.
            
            Args:
                current_tech: Current technology
                target_tech: Target technology to translate to
                context: Optional context or code snippet
            """
            
            try:
                # Technology mapping insights
                tech_mappings = {
                    ('swift', 'react'): {
                        'concepts': {
                            'UIViewController': 'Component',
                            '@State': 'useState',
                            'NavigationView': 'React Router',
                            'List': 'map() function'
                        },
                        'patterns': ['State management', 'Navigation', 'Data binding'],
                        'common_issues': ['Lifecycle management', 'State persistence']
                    },
                    ('android', 'python'): {
                        'concepts': {
                            'Activity': 'Class/Module',
                            'Intent': 'Function call',
                            'SharedPreferences': 'ConfigParser/JSON',
                            'AsyncTask': 'asyncio/threading'
                        },
                        'patterns': ['Background processing', 'Data persistence', 'API calls'],
                        'common_issues': ['Threading', 'Memory management']
                    }
                }
                
                mapping_key = (current_tech, target_tech)
                reverse_key = (target_tech, current_tech)
                
                insights = tech_mappings.get(mapping_key) or tech_mappings.get(reverse_key, {
                    'concepts': {},
                    'patterns': ['General programming patterns'],
                    'common_issues': ['Syntax differences', 'Paradigm differences']
                })
                
                # If context is provided, search for related examples
                related_examples = []
                if context:
                    search_results = await self.vector_engine.search_similar_contexts(
                        query=context,
                        technology=target_tech,
                        cross_tech=False,
                        limit=3
                    )
                    related_examples = [r['content'] for r in search_results]
                
                return {
                    'current_technology': current_tech,
                    'target_technology': target_tech,
                    'concept_mappings': insights['concepts'],
                    'common_patterns': insights['patterns'],
                    'potential_issues': insights['common_issues'],
                    'related_examples': related_examples,
                    'translation_confidence': self._calculate_translation_confidence(current_tech, target_tech)
                }
                
            except Exception as e:
                logger.error(f"Cross-tech insights failed: {str(e)}")
                return {
                    'error': f"Cross-tech insights failed: {str(e)}",
                    'concept_mappings': {},
                    'common_patterns': [],
                    'potential_issues': []
                }
        
        @mcp.tool()
        async def get_search_suggestions(
            partial_query: str,
            technology: str,
            project_id: str = None
        ) -> Dict[str, Any]:
            """
            Get search suggestions based on partial query and user history.
            
            Args:
                partial_query: Partial search query
                technology: Current technology
                project_id: Optional project ID
            """
            
            try:
                # This would analyze user's search history and popular queries
                # For now, providing smart suggestions based on technology
                
                tech_suggestions = {
                    'swift': [
                        'SwiftUI navigation',
                        'Core Data setup',
                        'URLSession best practices',
                        'Auto Layout constraints',
                        'Property wrappers usage'
                    ],
                    'react': [
                        'useState examples',
                        'useEffect cleanup',
                        'React Router setup',
                        'API integration patterns',
                        'Component composition'
                    ],
                    'python': [
                        'FastAPI endpoints',
                        'SQLAlchemy models',
                        'Async/await patterns',
                        'Error handling',
                        'Testing with pytest'
                    ],
                    'android': [
                        'RecyclerView adapter',
                        'Room database setup',
                        'Retrofit API calls',
                        'Fragment lifecycle',
                        'Material Design components'
                    ],
                    'javascript': [
                        'Promise handling',
                        'ES6 destructuring',
                        'DOM manipulation',
                        'Event handling',
                        'Module imports'
                    ]
                }
                
                base_suggestions = tech_suggestions.get(technology, [])
                
                # Filter suggestions based on partial query
                filtered_suggestions = [
                    s for s in base_suggestions 
                    if partial_query.lower() in s.lower()
                ] if partial_query else base_suggestions[:5]
                
                return {
                    'partial_query': partial_query,
                    'technology': technology,
                    'suggestions': filtered_suggestions,
                    'suggestion_count': len(filtered_suggestions)
                }
                
            except Exception as e:
                logger.error(f"Search suggestions failed: {str(e)}")
                return {
                    'error': f"Search suggestions failed: {str(e)}",
                    'suggestions': [],
                    'suggestion_count': 0
                }
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on content similarity"""
        unique_results = []
        seen_content = set()
        
        for result in results:
            content_hash = hash(result['content'][:100])  # Use first 100 chars for comparison
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _calculate_translation_confidence(self, current_tech: str, target_tech: str) -> float:
        """Calculate confidence score for cross-technology translation"""
        confidence_matrix = {
            ('swift', 'react'): 0.8,
            ('swift', 'javascript'): 0.7,
            ('android', 'python'): 0.8,
            ('python', 'javascript'): 0.7,
            ('react', 'javascript'): 0.9,
            ('android', 'swift'): 0.6
        }
        
        key = (current_tech, target_tech)
        reverse_key = (target_tech, current_tech)
        
        return confidence_matrix.get(key, confidence_matrix.get(reverse_key, 0.5))

async def main():
    """Main server function"""
    server = RetrievalEngineServer()
    
    # Get port from environment or use default
    port = int(os.getenv('RETRIEVAL_ENGINE_PORT', 8002))
    
    logger.info(f"Starting Retrieval Engine Server on port {port}")
    logger.info("Features: Semantic search, Pattern matching, Cross-technology insights")
    
    await mcp.run(transport="stdio")

if __name__ == "__main__":
    asyncio.run(main())