#!/usr/bin/env python3
"""
AI Agent Context Management System - Intelligence Engine Server

This MCP server handles advanced pattern learning, developer behavior analysis,
anti-pattern detection, and intelligent insights generation for solo developers
working across multiple technology stacks.

Port: 8003
"""

import asyncio
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA, LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict, Counter
import os
from dotenv import load_dotenv

from fastmcp import FastMCP

load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Intelligence Engine Server")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeveloperProfileAnalyzer:
    """Analyzes developer patterns and creates intelligence profiles"""
    
    def __init__(self):
        self.coding_patterns = defaultdict(list)
        self.technology_preferences = defaultdict(float)
        self.problem_solving_patterns = defaultdict(list)
        self.efficiency_metrics = defaultdict(dict)
        
    async def analyze_developer_dna(self, user_id: str = "default") -> Dict[str, Any]:
        """Generate comprehensive developer DNA profile"""
        
        # Fetch developer activity data (would connect to Context Storage Server)
        activity_data = await self._fetch_developer_activity(user_id)
        
        # Analyze coding patterns
        coding_analysis = self._analyze_coding_patterns(activity_data)
        
        # Analyze technology preferences and expertise
        tech_analysis = self._analyze_technology_patterns(activity_data)
        
        # Analyze problem-solving approaches
        problem_solving_analysis = self._analyze_problem_solving(activity_data)
        
        # Identify learning patterns
        learning_analysis = self._analyze_learning_patterns(activity_data)
        
        # Calculate developer efficiency metrics
        efficiency_analysis = self._calculate_efficiency_metrics(activity_data)
        
        # Generate cross-technology insights
        cross_tech_insights = self._generate_cross_tech_insights(tech_analysis)
        
        developer_dna = {
            'user_id': user_id,
            'profile_generated': datetime.now().isoformat(),
            'coding_patterns': coding_analysis,
            'technology_expertise': tech_analysis,
            'problem_solving_style': problem_solving_analysis,
            'learning_preferences': learning_analysis,
            'efficiency_metrics': efficiency_analysis,
            'cross_technology_insights': cross_tech_insights,
            'intelligence_score': self._calculate_intelligence_score(
                coding_analysis, tech_analysis, problem_solving_analysis, efficiency_analysis
            ),
            'recommendations': self._generate_recommendations(
                coding_analysis, tech_analysis, problem_solving_analysis
            )
        }
        
        return developer_dna
    
    async def _fetch_developer_activity(self, user_id: str) -> Dict[str, Any]:
        """Fetch developer activity from Context Storage Server"""
        # Mock data - in real implementation, this would query the database
        return {
            'projects': [
                {
                    'id': 'swift_ios_app',
                    'technology': 'swift',
                    'duration_weeks': 8,
                    'completion_rate': 0.9,
                    'patterns_used': ['MVVM', 'Coordinator', 'Repository'],
                    'issues_resolved': 23,
                    'code_quality_score': 0.8
                },
                {
                    'id': 'react_web_app',
                    'technology': 'react',
                    'duration_weeks': 6,
                    'completion_rate': 0.95,
                    'patterns_used': ['Hooks', 'Context API', 'Custom Hooks'],
                    'issues_resolved': 18,
                    'code_quality_score': 0.85
                }
            ],
            'code_sessions': [
                {
                    'session_id': 'session_1',
                    'technology': 'swift',
                    'duration_minutes': 120,
                    'lines_written': 150,
                    'bugs_introduced': 2,
                    'bugs_fixed': 5,
                    'patterns_applied': ['Observable pattern'],
                    'research_time_minutes': 30
                }
            ],
            'search_history': [
                {'query': 'SwiftUI navigation', 'technology': 'swift', 'success': True},
                {'query': 'React hooks best practices', 'technology': 'react', 'success': True}
            ]
        }
    
    def _analyze_coding_patterns(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze developer's coding patterns and preferences"""
        
        patterns_used = []
        for project in activity_data.get('projects', []):
            patterns_used.extend(project.get('patterns_used', []))
        
        pattern_frequency = Counter(patterns_used)
        
        # Analyze session productivity
        sessions = activity_data.get('code_sessions', [])
        productivity_metrics = {
            'avg_session_duration': np.mean([s['duration_minutes'] for s in sessions]) if sessions else 0,
            'avg_lines_per_minute': np.mean([s['lines_written'] / s['duration_minutes'] for s in sessions if s['duration_minutes'] > 0]) if sessions else 0,
            'bug_introduction_rate': np.mean([s['bugs_introduced'] / s['lines_written'] for s in sessions if s['lines_written'] > 0]) if sessions else 0,
            'bug_fix_rate': np.mean([s['bugs_fixed'] / s['duration_minutes'] for s in sessions if s['duration_minutes'] > 0]) if sessions else 0
        }
        
        return {
            'preferred_patterns': dict(pattern_frequency.most_common(5)),
            'coding_style': self._determine_coding_style(patterns_used),
            'productivity_metrics': productivity_metrics,
            'consistency_score': self._calculate_consistency_score(sessions)
        }
    
    def _analyze_technology_patterns(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technology expertise and preferences"""
        
        tech_experience = {}
        tech_proficiency = {}
        
        for project in activity_data.get('projects', []):
            tech = project['technology']
            if tech not in tech_experience:
                tech_experience[tech] = {
                    'projects_count': 0,
                    'total_weeks': 0,
                    'avg_completion_rate': 0,
                    'avg_quality_score': 0
                }
            
            tech_experience[tech]['projects_count'] += 1
            tech_experience[tech]['total_weeks'] += project['duration_weeks']
            tech_experience[tech]['avg_completion_rate'] += project['completion_rate']
            tech_experience[tech]['avg_quality_score'] += project['code_quality_score']
        
        # Calculate averages
        for tech, data in tech_experience.items():
            count = data['projects_count']
            data['avg_completion_rate'] /= count
            data['avg_quality_score'] /= count
            
            # Calculate proficiency score
            proficiency = (
                min(1.0, data['total_weeks'] / 20) * 0.4 +  # Experience factor
                data['avg_completion_rate'] * 0.3 +  # Success rate
                data['avg_quality_score'] * 0.3   # Quality factor
            )
            tech_proficiency[tech] = proficiency
        
        return {
            'technology_experience': tech_experience,
            'proficiency_scores': tech_proficiency,
            'primary_technology': max(tech_proficiency.items(), key=lambda x: x[1])[0] if tech_proficiency else None,
            'technology_versatility': len(tech_proficiency),
            'cross_tech_correlation': self._calculate_cross_tech_correlation(tech_proficiency)
        }
    
    def _analyze_problem_solving(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze problem-solving approaches and preferences"""
        
        search_patterns = activity_data.get('search_history', [])
        research_patterns = []
        
        for session in activity_data.get('code_sessions', []):
            if session.get('research_time_minutes', 0) > 0:
                research_ratio = session['research_time_minutes'] / session['duration_minutes']
                research_patterns.append(research_ratio)
        
        problem_solving_style = {
            'research_to_code_ratio': np.mean(research_patterns) if research_patterns else 0,
            'search_success_rate': np.mean([s['success'] for s in search_patterns]) if search_patterns else 0,
            'preferred_search_types': self._analyze_search_types(search_patterns),
            'debugging_efficiency': self._calculate_debugging_efficiency(activity_data),
            'solution_approach': self._determine_solution_approach(research_patterns, search_patterns)
        }
        
        return problem_solving_style
    
    def _analyze_learning_patterns(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how the developer learns and adopts new concepts"""
        
        learning_indicators = {
            'new_pattern_adoption_rate': self._calculate_pattern_adoption_rate(activity_data),
            'technology_exploration_frequency': self._calculate_tech_exploration(activity_data),
            'knowledge_retention_score': self._calculate_knowledge_retention(activity_data),
            'preferred_learning_style': self._determine_learning_style(activity_data)
        }
        
        return learning_indicators
    
    def _calculate_efficiency_metrics(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate various efficiency metrics"""
        
        projects = activity_data.get('projects', [])
        sessions = activity_data.get('code_sessions', [])
        
        efficiency_metrics = {
            'project_completion_efficiency': np.mean([p['completion_rate'] / p['duration_weeks'] for p in projects]) if projects else 0,
            'code_quality_consistency': np.std([p['code_quality_score'] for p in projects]) if projects else 0,
            'debugging_to_development_ratio': self._calculate_debug_ratio(sessions),
            'knowledge_reuse_efficiency': self._calculate_knowledge_reuse(activity_data),
            'overall_productivity_score': self._calculate_overall_productivity(projects, sessions)
        }
        
        return efficiency_metrics
    
    def _generate_cross_tech_insights(self, tech_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights about cross-technology knowledge transfer"""
        
        proficiency_scores = tech_analysis.get('proficiency_scores', {})
        
        # Technology similarity matrix
        tech_similarity = {
            ('swift', 'react'): 0.7,  # Both have component-based architecture
            ('swift', 'javascript'): 0.6,  # Similar syntax patterns
            ('android', 'python'): 0.8,  # Similar paradigms
            ('python', 'javascript'): 0.7,  # Both scripting languages
            ('react', 'javascript'): 0.9   # React is JavaScript
        }
        
        transfer_opportunities = []
        for (tech1, tech2), similarity in tech_similarity.items():
            if tech1 in proficiency_scores and tech2 in proficiency_scores:
                if proficiency_scores[tech1] > 0.7 and proficiency_scores[tech2] < 0.5:
                    transfer_opportunities.append({
                        'from_technology': tech1,
                        'to_technology': tech2,
                        'transfer_potential': similarity * proficiency_scores[tech1],
                        'recommended_concepts': self._get_transferable_concepts(tech1, tech2)
                    })
        
        return {
            'transfer_opportunities': transfer_opportunities,
            'strongest_tech_combination': self._find_strongest_combination(proficiency_scores),
            'knowledge_gaps': self._identify_knowledge_gaps(proficiency_scores),
            'synergy_score': self._calculate_synergy_score(proficiency_scores, tech_similarity)
        }
    
    def _calculate_intelligence_score(self, coding: Dict, tech: Dict, problem_solving: Dict, efficiency: Dict) -> float:
        """Calculate overall developer intelligence score"""
        
        # Weighted combination of different factors
        coding_score = (
            coding.get('productivity_metrics', {}).get('avg_lines_per_minute', 0) * 0.3 +
            (1 - coding.get('productivity_metrics', {}).get('bug_introduction_rate', 1)) * 0.4 +
            coding.get('consistency_score', 0) * 0.3
        )
        
        tech_score = tech.get('technology_versatility', 0) / 5.0  # Normalize by max expected techs
        
        problem_solving_score = (
            problem_solving.get('search_success_rate', 0) * 0.4 +
            problem_solving.get('debugging_efficiency', 0) * 0.6
        )
        
        efficiency_score = efficiency.get('overall_productivity_score', 0)
        
        overall_intelligence = (
            coding_score * 0.3 +
            tech_score * 0.2 +
            problem_solving_score * 0.25 +
            efficiency_score * 0.25
        )
        
        return min(1.0, max(0.0, overall_intelligence))
    
    def _generate_recommendations(self, coding: Dict, tech: Dict, problem_solving: Dict) -> List[Dict[str, Any]]:
        """Generate personalized recommendations for improvement"""
        
        recommendations = []
        
        # Coding pattern recommendations
        if coding.get('consistency_score', 0) < 0.7:
            recommendations.append({
                'type': 'coding_consistency',
                'priority': 'high',
                'recommendation': 'Focus on establishing consistent coding patterns across projects',
                'actionable_steps': [
                    'Create personal coding style guide',
                    'Set up automated linting tools',
                    'Regular code review sessions'
                ]
            })
        
        # Technology recommendations
        versatility = tech.get('technology_versatility', 0)
        if versatility < 3:
            recommendations.append({
                'type': 'technology_expansion',
                'priority': 'medium',
                'recommendation': 'Consider expanding technology stack for better versatility',
                'actionable_steps': [
                    'Identify complementary technologies',
                    'Start small learning projects',
                    'Find cross-technology patterns'
                ]
            })
        
        # Problem-solving recommendations
        if problem_solving.get('search_success_rate', 0) < 0.8:
            recommendations.append({
                'type': 'research_efficiency',
                'priority': 'medium',
                'recommendation': 'Improve research and search strategies',
                'actionable_steps': [
                    'Learn advanced search techniques',
                    'Build personal knowledge base',
                    'Practice formulating better questions'
                ]
            })
        
        return recommendations
    
    # Helper methods (simplified implementations)
    def _determine_coding_style(self, patterns: List[str]) -> str:
        if 'MVVM' in patterns or 'MVC' in patterns:
            return 'architecture-focused'
        elif 'Hooks' in patterns or 'Functional' in patterns:
            return 'functional'
        else:
            return 'pragmatic'
    
    def _calculate_consistency_score(self, sessions: List[Dict]) -> float:
        if not sessions:
            return 0.5
        
        productivities = [s['lines_written'] / s['duration_minutes'] for s in sessions if s['duration_minutes'] > 0]
        if not productivities:
            return 0.5
        
        # Lower standard deviation = higher consistency
        std_dev = np.std(productivities)
        mean_productivity = np.mean(productivities)
        
        if mean_productivity == 0:
            return 0.5
        
        coefficient_of_variation = std_dev / mean_productivity
        consistency = max(0, 1 - coefficient_of_variation)
        
        return min(1.0, consistency)
    
    def _calculate_cross_tech_correlation(self, proficiency: Dict[str, float]) -> float:
        if len(proficiency) < 2:
            return 0.0
        
        scores = list(proficiency.values())
        return 1.0 - (max(scores) - min(scores))  # Higher correlation = less variance
    
    def _analyze_search_types(self, searches: List[Dict]) -> Dict[str, int]:
        types = defaultdict(int)
        for search in searches:
            query = search['query'].lower()
            if 'best practice' in query or 'pattern' in query:
                types['best_practices'] += 1
            elif 'error' in query or 'fix' in query or 'debug' in query:
                types['debugging'] += 1
            elif 'how to' in query or 'tutorial' in query:
                types['learning'] += 1
            else:
                types['general'] += 1
        return dict(types)
    
    def _calculate_debugging_efficiency(self, activity_data: Dict) -> float:
        sessions = activity_data.get('code_sessions', [])
        if not sessions:
            return 0.5
        
        fix_rates = [s['bugs_fixed'] / s['duration_minutes'] for s in sessions if s['duration_minutes'] > 0]
        return np.mean(fix_rates) if fix_rates else 0.5
    
    def _determine_solution_approach(self, research_patterns: List[float], search_patterns: List[Dict]) -> str:
        avg_research_ratio = np.mean(research_patterns) if research_patterns else 0
        
        if avg_research_ratio > 0.3:
            return 'research-first'
        elif avg_research_ratio > 0.1:
            return 'balanced'
        else:
            return 'trial-and-error'
    
    def _calculate_pattern_adoption_rate(self, activity_data: Dict) -> float:
        # Simplified: count unique patterns used across projects
        all_patterns = set()
        for project in activity_data.get('projects', []):
            all_patterns.update(project.get('patterns_used', []))
        
        project_count = len(activity_data.get('projects', []))
        if project_count == 0:
            return 0.0
        
        return len(all_patterns) / project_count
    
    def _calculate_tech_exploration(self, activity_data: Dict) -> float:
        techs_used = set()
        for project in activity_data.get('projects', []):
            techs_used.add(project['technology'])
        
        # Normalize by expected exploration (assume 5 techs is high exploration)
        return min(1.0, len(techs_used) / 5.0)
    
    def _calculate_knowledge_retention(self, activity_data: Dict) -> float:
        # Simplified: measure pattern reuse across projects
        pattern_usage = defaultdict(int)
        for project in activity_data.get('projects', []):
            for pattern in project.get('patterns_used', []):
                pattern_usage[pattern] += 1
        
        if not pattern_usage:
            return 0.5
        
        reused_patterns = sum(1 for count in pattern_usage.values() if count > 1)
        total_patterns = len(pattern_usage)
        
        return reused_patterns / total_patterns if total_patterns > 0 else 0.5
    
    def _determine_learning_style(self, activity_data: Dict) -> str:
        # Simplified determination based on research patterns
        sessions = activity_data.get('code_sessions', [])
        if not sessions:
            return 'unknown'
        
        avg_research_time = np.mean([s.get('research_time_minutes', 0) for s in sessions])
        
        if avg_research_time > 45:
            return 'research-heavy'
        elif avg_research_time > 15:
            return 'balanced-learner'
        else:
            return 'hands-on'
    
    def _calculate_debug_ratio(self, sessions: List[Dict]) -> float:
        if not sessions:
            return 0.5
        
        debug_indicators = []
        for session in sessions:
            bugs_fixed = session.get('bugs_fixed', 0)
            lines_written = session.get('lines_written', 1)
            debug_ratio = bugs_fixed / lines_written if lines_written > 0 else 0
            debug_indicators.append(debug_ratio)
        
        return np.mean(debug_indicators)
    
    def _calculate_knowledge_reuse(self, activity_data: Dict) -> float:
        # Measure how often previous patterns/solutions are reused
        pattern_reuse = self._calculate_pattern_adoption_rate(activity_data)
        search_diversity = len(set(s['query'] for s in activity_data.get('search_history', [])))
        
        if search_diversity == 0:
            return pattern_reuse
        
        # Lower search diversity with high pattern reuse = good knowledge reuse
        reuse_efficiency = pattern_reuse / (1 + search_diversity / 10)
        return min(1.0, reuse_efficiency)
    
    def _calculate_overall_productivity(self, projects: List[Dict], sessions: List[Dict]) -> float:
        if not projects or not sessions:
            return 0.5
        
        project_efficiency = np.mean([p['completion_rate'] / p['duration_weeks'] for p in projects])
        session_efficiency = np.mean([s['lines_written'] / s['duration_minutes'] for s in sessions if s['duration_minutes'] > 0])
        
        # Normalize and combine
        normalized_project = min(1.0, project_efficiency / 0.2)  # Assume 0.2 is good efficiency
        normalized_session = min(1.0, session_efficiency / 2.0)   # Assume 2 lines/min is good
        
        return (normalized_project + normalized_session) / 2
    
    def _get_transferable_concepts(self, from_tech: str, to_tech: str) -> List[str]:
        """Get concepts that can transfer between technologies"""
        transfer_map = {
            ('swift', 'react'): ['Component architecture', 'State management', 'Property binding'],
            ('android', 'python'): ['Object-oriented patterns', 'Async programming', 'Data structures'],
            ('python', 'javascript'): ['Functions as first-class objects', 'Dynamic typing', 'List comprehensions']
        }
        
        return transfer_map.get((from_tech, to_tech), ['General programming concepts'])
    
    def _find_strongest_combination(self, proficiency: Dict[str, float]) -> Optional[Tuple[str, str]]:
        """Find the strongest technology combination"""
        if len(proficiency) < 2:
            return None
        
        sorted_techs = sorted(proficiency.items(), key=lambda x: x[1], reverse=True)
        return (sorted_techs[0][0], sorted_techs[1][0])
    
    def _identify_knowledge_gaps(self, proficiency: Dict[str, float]) -> List[str]:
        """Identify technologies with knowledge gaps"""
        gaps = []
        for tech, score in proficiency.items():
            if score < 0.6:
                gaps.append(tech)
        return gaps
    
    def _calculate_synergy_score(self, proficiency: Dict[str, float], similarity: Dict[Tuple[str, str], float]) -> float:
        """Calculate how well technologies work together"""
        if len(proficiency) < 2:
            return 0.0
        
        synergy_scores = []
        techs = list(proficiency.keys())
        
        for i, tech1 in enumerate(techs):
            for tech2 in techs[i+1:]:
                key = (tech1, tech2) if (tech1, tech2) in similarity else (tech2, tech1)
                if key in similarity:
                    combined_proficiency = (proficiency[tech1] + proficiency[tech2]) / 2
                    synergy = similarity[key] * combined_proficiency
                    synergy_scores.append(synergy)
        
        return np.mean(synergy_scores) if synergy_scores else 0.0

class AntiPatternDetector:
    """Detects anti-patterns and problematic code practices"""
    
    def __init__(self):
        self.anti_patterns = {
            'swift': [
                'retain_cycles',
                'force_unwrapping_abuse',
                'massive_view_controller',
                'singleton_overuse'
            ],
            'react': [
                'prop_drilling',
                'component_god_object',
                'useEffect_hell',
                'unnecessary_rerenders'
            ],
            'python': [
                'circular_imports',
                'global_variable_abuse',
                'exception_swallowing',
                'premature_optimization'
            ],
            'javascript': [
                'callback_hell',
                'global_pollution',
                'memory_leaks',
                'prototype_pollution'
            ],
            'android': [
                'memory_leaks',
                'blocking_main_thread',
                'context_leaks',
                'bitmap_overload'
            ]
        }
    
    async def detect_anti_patterns(
        self, 
        code_snippet: str, 
        technology: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Detect anti-patterns in code snippet"""
        
        detected_patterns = []
        tech_patterns = self.anti_patterns.get(technology, [])
        
        # Simplified pattern detection logic
        for pattern in tech_patterns:
            if self._check_pattern(code_snippet, pattern, technology):
                severity = self._calculate_severity(pattern, code_snippet, context)
                detected_patterns.append({
                    'pattern': pattern,
                    'severity': severity,
                    'description': self._get_pattern_description(pattern, technology),
                    'suggestion': self._get_pattern_suggestion(pattern, technology),
                    'confidence': self._calculate_confidence(pattern, code_snippet)
                })
        
        return {
            'technology': technology,
            'anti_patterns_detected': len(detected_patterns),
            'patterns': detected_patterns,
            'overall_risk_score': self._calculate_risk_score(detected_patterns),
            'recommendations': self._generate_anti_pattern_recommendations(detected_patterns)
        }
    
    def _check_pattern(self, code: str, pattern: str, technology: str) -> bool:
        """Check if specific anti-pattern exists in code"""
        # Simplified pattern detection
        pattern_indicators = {
            'force_unwrapping_abuse': ['!', 'force', 'unwrap'],
            'retain_cycles': ['weak', 'unowned', 'closure', 'self'],
            'prop_drilling': ['props.', 'prop'],
            'useEffect_hell': ['useEffect', 'dependency'],
            'callback_hell': ['callback', 'function(', ').function('],
            'global_pollution': ['var ', 'window.', 'global'],
            'memory_leaks': ['listener', 'timeout', 'interval'],
            'circular_imports': ['import', 'from']
        }
        
        indicators = pattern_indicators.get(pattern, [])
        return any(indicator in code.lower() for indicator in indicators)
    
    def _calculate_severity(self, pattern: str, code: str, context: Dict[str, Any] = None) -> str:
        """Calculate severity of detected anti-pattern"""
        high_severity_patterns = ['memory_leaks', 'retain_cycles', 'blocking_main_thread']
        
        if pattern in high_severity_patterns:
            return 'high'
        elif len(code) > 1000:  # Large code snippets with patterns are more concerning
            return 'medium'
        else:
            return 'low'
    
    def _get_pattern_description(self, pattern: str, technology: str) -> str:
        """Get description of the anti-pattern"""
        descriptions = {
            'retain_cycles': 'Strong reference cycles that prevent memory deallocation',
            'force_unwrapping_abuse': 'Excessive use of force unwrapping without proper nil checking',
            'prop_drilling': 'Passing props through multiple component layers unnecessarily',
            'useEffect_hell': 'Complex useEffect dependencies causing performance issues',
            'callback_hell': 'Nested callbacks making code difficult to read and maintain',
            'memory_leaks': 'References or listeners not properly cleaned up'
        }
        
        return descriptions.get(pattern, f'Anti-pattern detected in {technology} code')
    
    def _get_pattern_suggestion(self, pattern: str, technology: str) -> str:
        """Get suggestion to fix the anti-pattern"""
        suggestions = {
            'retain_cycles': 'Use weak references or break the cycle with proper cleanup',
            'force_unwrapping_abuse': 'Use optional binding (if let) or guard statements',
            'prop_drilling': 'Consider using Context API or state management library',
            'useEffect_hell': 'Split into multiple useEffect hooks with specific dependencies',
            'callback_hell': 'Use async/await or Promises to flatten the callback structure',
            'memory_leaks': 'Implement proper cleanup in componentWillUnmount or useEffect return'
        }
        
        return suggestions.get(pattern, 'Review code structure and apply best practices')
    
    def _calculate_confidence(self, pattern: str, code: str) -> float:
        """Calculate confidence in anti-pattern detection"""
        # Simplified confidence calculation
        base_confidence = 0.7
        
        # Increase confidence based on code length and pattern frequency
        pattern_count = code.lower().count(pattern.replace('_', ' '))
        confidence_boost = min(0.3, pattern_count * 0.1)
        
        return min(1.0, base_confidence + confidence_boost)
    
    def _calculate_risk_score(self, patterns: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score"""
        if not patterns:
            return 0.0
        
        severity_weights = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
        
        total_risk = sum(
            severity_weights.get(p['severity'], 0.5) * p['confidence']
            for p in patterns
        )
        
        # Normalize by number of patterns
        return min(1.0, total_risk / len(patterns))
    
    def _generate_anti_pattern_recommendations(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on detected anti-patterns"""
        if not patterns:
            return ["Code looks clean! Continue following best practices."]
        
        recommendations = []
        high_priority = [p for p in patterns if p['severity'] == 'high']
        
        if high_priority:
            recommendations.append("Address high-severity issues immediately to prevent potential crashes or memory issues")
        
        if len(patterns) > 3:
            recommendations.append("Consider a comprehensive code review to address multiple anti-patterns")
        
        recommendations.append("Set up automated linting tools to catch these patterns early")
        
        return recommendations

class IntelligenceEngineServer:
    """Main intelligence engine server class"""
    
    def __init__(self):
        self.profile_analyzer = DeveloperProfileAnalyzer()
        self.anti_pattern_detector = AntiPatternDetector()
        self.db_manager = self._init_database()
        
        # Register tools with global MCP server
        self._register_tools()
    
    def _init_database(self) -> sqlite3.Connection:
        """Initialize intelligence database"""
        db_path = "intelligence_engine.db"
        conn = sqlite3.connect(db_path)
        
        # Create tables for intelligence data
        conn.execute("""
            CREATE TABLE IF NOT EXISTS intelligence_profiles (
                user_id TEXT PRIMARY KEY,
                profile_data TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pattern_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                technology TEXT,
                detection_count INTEGER DEFAULT 1,
                last_detected DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        return conn
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @mcp.tool()
        async def analyze_developer_intelligence(
            user_id: str = "default",
            include_recommendations: bool = True,
            deep_analysis: bool = False
        ) -> Dict[str, Any]:
            """
            Perform comprehensive developer intelligence analysis.
            
            Args:
                user_id: Developer identifier
                include_recommendations: Whether to include improvement recommendations
                deep_analysis: Whether to perform deep pattern analysis
            """
            
            try:
                # Generate developer DNA profile
                developer_dna = await self.profile_analyzer.analyze_developer_dna(user_id)
                
                # Store profile in database
                profile_json = json.dumps(developer_dna)
                self.db_manager.execute(
                    "INSERT OR REPLACE INTO intelligence_profiles (user_id, profile_data) VALUES (?, ?)",
                    (user_id, profile_json)
                )
                self.db_manager.commit()
                
                # Add deep analysis if requested
                if deep_analysis:
                    developer_dna['deep_insights'] = await self._perform_deep_analysis(developer_dna)
                
                # Filter recommendations if not requested
                if not include_recommendations:
                    developer_dna.pop('recommendations', None)
                
                return {
                    'analysis_type': 'developer_intelligence',
                    'user_id': user_id,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'intelligence_data': developer_dna,
                    'analysis_quality_score': self._calculate_analysis_quality(developer_dna)
                }
                
            except Exception as e:
                logger.error(f"Intelligence analysis failed: {str(e)}")
                return {
                    'error': f"Intelligence analysis failed: {str(e)}",
                    'analysis_type': 'developer_intelligence',
                    'user_id': user_id
                }
        
        @mcp.tool()
        async def detect_code_anti_patterns(
            code_snippet: str,
            technology: str,
            context_info: str = "",
            severity_threshold: str = "low"
        ) -> Dict[str, Any]:
            """
            Detect anti-patterns and code quality issues.
            
            Args:
                code_snippet: Code to analyze
                technology: Technology stack (swift, react, python, javascript, android)
                context_info: Additional context about the code
                severity_threshold: Minimum severity to report (low, medium, high)
            """
            
            try:
                # Parse context info
                context = json.loads(context_info) if context_info else {}
                
                # Detect anti-patterns
                detection_result = await self.anti_pattern_detector.detect_anti_patterns(
                    code_snippet=code_snippet,
                    technology=technology,
                    context=context
                )
                
                # Filter by severity threshold
                severity_order = ['low', 'medium', 'high']
                min_severity_index = severity_order.index(severity_threshold)
                
                filtered_patterns = [
                    p for p in detection_result['patterns']
                    if severity_order.index(p['severity']) >= min_severity_index
                ]
                
                detection_result['patterns'] = filtered_patterns
                detection_result['anti_patterns_detected'] = len(filtered_patterns)
                
                # Log pattern detection for analytics
                for pattern in filtered_patterns:
                    self.db_manager.execute(
                        "INSERT OR IGNORE INTO pattern_analytics (pattern_type, technology) VALUES (?, ?)",
                        (pattern['pattern'], technology)
                    )
                
                self.db_manager.commit()
                
                return {
                    'analysis_type': 'anti_pattern_detection',
                    'technology': technology,
                    'severity_threshold': severity_threshold,
                    'detection_results': detection_result,
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Anti-pattern detection failed: {str(e)}")
                return {
                    'error': f"Anti-pattern detection failed: {str(e)}",
                    'analysis_type': 'anti_pattern_detection',
                    'technology': technology
                }
        
        @mcp.tool()
        async def generate_learning_insights(
            user_id: str = "default",
            focus_area: str = "general",
            timeframe_days: int = 30
        ) -> Dict[str, Any]:
            """
            Generate personalized learning insights and recommendations.
            
            Args:
                user_id: Developer identifier
                focus_area: Area to focus on (general, efficiency, quality, patterns)
                timeframe_days: Days to look back for analysis
            """
            
            try:
                # Get developer profile
                profile_data = self._get_stored_profile(user_id)
                if not profile_data:
                    return {
                        'error': 'No developer profile found. Run intelligence analysis first.',
                        'user_id': user_id
                    }
                
                # Generate focus-specific insights
                insights = await self._generate_focused_insights(profile_data, focus_area, timeframe_days)
                
                # Generate learning path recommendations
                learning_path = self._generate_learning_path(profile_data, focus_area)
                
                # Calculate progress metrics
                progress_metrics = self._calculate_learning_progress(profile_data, timeframe_days)
                
                return {
                    'analysis_type': 'learning_insights',
                    'user_id': user_id,
                    'focus_area': focus_area,
                    'timeframe_days': timeframe_days,
                    'insights': insights,
                    'learning_path': learning_path,
                    'progress_metrics': progress_metrics,
                    'next_milestones': self._generate_next_milestones(profile_data, focus_area),
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Learning insights generation failed: {str(e)}")
                return {
                    'error': f"Learning insights generation failed: {str(e)}",
                    'analysis_type': 'learning_insights',
                    'user_id': user_id
                }
        
        @mcp.tool()
        async def predict_development_outcomes(
            project_description: str,
            technology: str,
            estimated_duration_weeks: int,
            user_id: str = "default"
        ) -> Dict[str, Any]:
            """
            Predict development outcomes based on developer profile and project parameters.
            
            Args:
                project_description: Description of the project
                technology: Primary technology to be used
                estimated_duration_weeks: Estimated project duration
                user_id: Developer identifier
            """
            
            try:
                # Get developer profile
                profile_data = self._get_stored_profile(user_id)
                if not profile_data:
                    return {
                        'error': 'No developer profile found. Run intelligence analysis first.',
                        'user_id': user_id
                    }
                
                # Analyze project complexity
                complexity_score = self._analyze_project_complexity(project_description, technology)
                
                # Get developer's technology proficiency
                tech_proficiency = profile_data.get('technology_expertise', {}).get('proficiency_scores', {}).get(technology, 0.5)
                
                # Predict outcomes
                predictions = {
                    'completion_probability': self._predict_completion_probability(
                        complexity_score, tech_proficiency, estimated_duration_weeks, profile_data
                    ),
                    'quality_score_prediction': self._predict_quality_score(
                        complexity_score, tech_proficiency, profile_data
                    ),
                    'actual_duration_estimate': self._predict_actual_duration(
                        estimated_duration_weeks, complexity_score, tech_proficiency, profile_data
                    ),
                    'potential_challenges': self._predict_challenges(
                        project_description, technology, profile_data
                    ),
                    'success_factors': self._identify_success_factors(
                        technology, profile_data
                    )
                }
                
                # Generate recommendations for success
                recommendations = self._generate_project_recommendations(
                    predictions, complexity_score, tech_proficiency
                )
                
                return {
                    'analysis_type': 'outcome_prediction',
                    'project_description': project_description,
                    'technology': technology,
                    'estimated_duration_weeks': estimated_duration_weeks,
                    'user_id': user_id,
                    'complexity_analysis': {
                        'complexity_score': complexity_score,
                        'technology_proficiency': tech_proficiency
                    },
                    'predictions': predictions,
                    'recommendations': recommendations,
                    'confidence_score': self._calculate_prediction_confidence(predictions, profile_data),
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Outcome prediction failed: {str(e)}")
                return {
                    'error': f"Outcome prediction failed: {str(e)}",
                    'analysis_type': 'outcome_prediction',
                    'project_description': project_description
                }
    
    # Helper methods
    async def _perform_deep_analysis(self, developer_dna: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep analysis of developer patterns"""
        return {
            'cognitive_patterns': self._analyze_cognitive_patterns(developer_dna),
            'optimization_opportunities': self._identify_optimization_opportunities(developer_dna),
            'risk_factors': self._identify_risk_factors(developer_dna),
            'growth_potential': self._assess_growth_potential(developer_dna)
        }
    
    def _calculate_analysis_quality(self, developer_dna: Dict[str, Any]) -> float:
        """Calculate quality score of the analysis"""
        data_completeness = len([k for k, v in developer_dna.items() if v]) / len(developer_dna)
        intelligence_score = developer_dna.get('intelligence_score', 0.5)
        return (data_completeness + intelligence_score) / 2
    
    def _get_stored_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get stored developer profile"""
        cursor = self.db_manager.execute(
            "SELECT profile_data FROM intelligence_profiles WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if result:
            return json.loads(result[0])
        return None
    
    async def _generate_focused_insights(self, profile_data: Dict, focus_area: str, timeframe_days: int) -> Dict[str, Any]:
        """Generate insights for specific focus area"""
        insights = {
            'focus_area': focus_area,
            'key_strengths': [],
            'improvement_areas': [],
            'actionable_insights': []
        }
        
        if focus_area == 'efficiency':
            efficiency_metrics = profile_data.get('efficiency_metrics', {})
            insights['key_strengths'] = self._identify_efficiency_strengths(efficiency_metrics)
            insights['improvement_areas'] = self._identify_efficiency_improvements(efficiency_metrics)
        
        elif focus_area == 'quality':
            coding_patterns = profile_data.get('coding_patterns', {})
            insights['key_strengths'] = self._identify_quality_strengths(coding_patterns)
            insights['improvement_areas'] = self._identify_quality_improvements(coding_patterns)
        
        # Add more focus areas as needed
        
        return insights
    
    def _generate_learning_path(self, profile_data: Dict, focus_area: str) -> List[Dict[str, Any]]:
        """Generate personalized learning path"""
        tech_expertise = profile_data.get('technology_expertise', {})
        proficiency_scores = tech_expertise.get('proficiency_scores', {})
        
        learning_steps = []
        
        # Find technology with lowest proficiency for improvement
        if proficiency_scores:
            lowest_tech = min(proficiency_scores.items(), key=lambda x: x[1])
            if lowest_tech[1] < 0.7:  # Room for improvement
                learning_steps.append({
                    'step': 1,
                    'title': f'Improve {lowest_tech[0]} proficiency',
                    'description': f'Focus on strengthening {lowest_tech[0]} skills',
                    'estimated_weeks': 4,
                    'resources': self._get_learning_resources(lowest_tech[0])
                })
        
        return learning_steps
    
    def _calculate_learning_progress(self, profile_data: Dict, timeframe_days: int) -> Dict[str, Any]:
        """Calculate learning progress metrics"""
        # This would compare current profile with historical data
        return {
            'skill_improvement_rate': 0.15,  # Mock data
            'new_patterns_learned': 3,
            'consistency_improvement': 0.1,
            'overall_progress_score': 0.75
        }
    
    def _generate_next_milestones(self, profile_data: Dict, focus_area: str) -> List[Dict[str, Any]]:
        """Generate next learning milestones"""
        return [
            {
                'milestone': 'Achieve 80% consistency in coding patterns',
                'target_date': (datetime.now() + timedelta(weeks=4)).isoformat(),
                'progress': 0.6
            }
        ]
    
    def _analyze_project_complexity(self, description: str, technology: str) -> float:
        """Analyze project complexity based on description"""
        complexity_keywords = {
            'simple': ['crud', 'basic', 'simple', 'straightforward'],
            'medium': ['api', 'database', 'authentication', 'integration'],
            'complex': ['machine learning', 'real-time', 'distributed', 'scalable', 'microservices']
        }
        
        description_lower = description.lower()
        complexity_score = 0.3  # Base complexity
        
        for keyword in complexity_keywords['simple']:
            if keyword in description_lower:
                complexity_score -= 0.1
        
        for keyword in complexity_keywords['medium']:
            if keyword in description_lower:
                complexity_score += 0.2
        
        for keyword in complexity_keywords['complex']:
            if keyword in description_lower:
                complexity_score += 0.4
        
        return min(1.0, max(0.1, complexity_score))
    
    def _predict_completion_probability(self, complexity: float, proficiency: float, duration: int, profile: Dict) -> float:
        """Predict project completion probability"""
        base_success_rate = profile.get('efficiency_metrics', {}).get('project_completion_efficiency', 0.7)
        
        # Adjust based on complexity and proficiency
        complexity_factor = 1.0 - (complexity * 0.3)
        proficiency_factor = proficiency
        duration_factor = max(0.5, 1.0 - (duration / 20))  # Longer projects are riskier
        
        probability = base_success_rate * complexity_factor * proficiency_factor * duration_factor
        return min(1.0, max(0.1, probability))
    
    def _predict_quality_score(self, complexity: float, proficiency: float, profile: Dict) -> float:
        """Predict code quality score"""
        base_quality = profile.get('coding_patterns', {}).get('consistency_score', 0.7)
        
        # Higher proficiency = better quality, higher complexity = lower quality
        quality_prediction = base_quality * proficiency * (1.0 - complexity * 0.2)
        return min(1.0, max(0.3, quality_prediction))
    
    def _predict_actual_duration(self, estimated: int, complexity: float, proficiency: float, profile: Dict) -> int:
        """Predict actual project duration"""
        efficiency = profile.get('efficiency_metrics', {}).get('overall_productivity_score', 0.7)
        
        # Lower efficiency and proficiency = longer duration
        duration_multiplier = (2.0 - efficiency) * (1.5 - proficiency) * (1.0 + complexity)
        actual_duration = int(estimated * duration_multiplier)
        
        return max(estimated, actual_duration)
    
    def _predict_challenges(self, description: str, technology: str, profile: Dict) -> List[str]:
        """Predict potential project challenges"""
        challenges = []
        
        tech_proficiency = profile.get('technology_expertise', {}).get('proficiency_scores', {}).get(technology, 0.5)
        
        if tech_proficiency < 0.6:
            challenges.append(f'Limited {technology} expertise may slow initial development')
        
        if 'database' in description.lower():
            challenges.append('Data modeling and migration complexities')
        
        if 'api' in description.lower():
            challenges.append('Third-party integration and error handling')
        
        return challenges
    
    def _identify_success_factors(self, technology: str, profile: Dict) -> List[str]:
        """Identify factors that will contribute to success"""
        factors = []
        
        tech_proficiency = profile.get('technology_expertise', {}).get('proficiency_scores', {}).get(technology, 0.5)
        
        if tech_proficiency > 0.7:
            factors.append(f'Strong {technology} expertise')
        
        consistency = profile.get('coding_patterns', {}).get('consistency_score', 0.5)
        if consistency > 0.7:
            factors.append('Consistent coding practices')
        
        problem_solving = profile.get('problem_solving_style', {}).get('search_success_rate', 0.5)
        if problem_solving > 0.8:
            factors.append('Effective problem-solving skills')
        
        return factors
    
    def _generate_project_recommendations(self, predictions: Dict, complexity: float, proficiency: float) -> List[str]:
        """Generate recommendations for project success"""
        recommendations = []
        
        if predictions['completion_probability'] < 0.7:
            recommendations.append('Consider breaking the project into smaller milestones')
        
        if proficiency < 0.6:
            recommendations.append('Allocate time for learning and skill development')
        
        if complexity > 0.7:
            recommendations.append('Plan for additional testing and code review phases')
        
        return recommendations
    
    def _calculate_prediction_confidence(self, predictions: Dict, profile: Dict) -> float:
        """Calculate confidence in predictions"""
        # Base confidence on amount of data available in profile
        data_points = len([v for v in profile.values() if v])
        confidence = min(1.0, data_points / 10)  # Assume 10 data points give high confidence
        
        return confidence
    
    # Additional helper methods for deep analysis
    def _analyze_cognitive_patterns(self, developer_dna: Dict) -> Dict[str, Any]:
        """Analyze cognitive patterns from developer behavior"""
        return {
            'learning_style': developer_dna.get('learning_preferences', {}).get('preferred_learning_style', 'unknown'),
            'problem_solving_approach': developer_dna.get('problem_solving_style', {}).get('solution_approach', 'unknown'),
            'cognitive_load_preference': 'moderate'  # Would be calculated from actual data
        }
    
    def _identify_optimization_opportunities(self, developer_dna: Dict) -> List[str]:
        """Identify areas for optimization"""
        opportunities = []
        
        efficiency = developer_dna.get('efficiency_metrics', {})
        if efficiency.get('overall_productivity_score', 0) < 0.7:
            opportunities.append('Improve overall productivity through better time management')
        
        consistency = developer_dna.get('coding_patterns', {}).get('consistency_score', 0)
        if consistency < 0.7:
            opportunities.append('Establish more consistent coding patterns')
        
        return opportunities
    
    def _identify_risk_factors(self, developer_dna: Dict) -> List[str]:
        """Identify potential risk factors"""
        risks = []
        
        bug_rate = developer_dna.get('coding_patterns', {}).get('productivity_metrics', {}).get('bug_introduction_rate', 0)
        if bug_rate > 0.1:  # More than 10% bug rate
            risks.append('High bug introduction rate may impact delivery quality')
        
        tech_versatility = developer_dna.get('technology_expertise', {}).get('technology_versatility', 0)
        if tech_versatility < 2:
            risks.append('Limited technology versatility may restrict project options')
        
        return risks
    
    def _assess_growth_potential(self, developer_dna: Dict) -> Dict[str, Any]:
        """Assess developer's growth potential"""
        learning_rate = developer_dna.get('learning_preferences', {}).get('new_pattern_adoption_rate', 0)
        exploration = developer_dna.get('learning_preferences', {}).get('technology_exploration_frequency', 0)
        
        growth_score = (learning_rate + exploration) / 2
        
        return {
            'growth_score': growth_score,
            'growth_trajectory': 'accelerating' if growth_score > 0.7 else 'steady' if growth_score > 0.4 else 'gradual',
            'potential_ceiling': 'high' if growth_score > 0.8 else 'medium' if growth_score > 0.5 else 'needs_support'
        }
    
    def _identify_efficiency_strengths(self, efficiency_metrics: Dict) -> List[str]:
        """Identify efficiency-related strengths"""
        strengths = []
        
        if efficiency_metrics.get('overall_productivity_score', 0) > 0.8:
            strengths.append('High overall productivity')
        
        if efficiency_metrics.get('debugging_to_development_ratio', 1) < 0.3:
            strengths.append('Efficient debugging skills')
        
        return strengths
    
    def _identify_efficiency_improvements(self, efficiency_metrics: Dict) -> List[str]:
        """Identify areas for efficiency improvement"""
        improvements = []
        
        if efficiency_metrics.get('knowledge_reuse_efficiency', 0) < 0.6:
            improvements.append('Improve knowledge reuse and pattern application')
        
        if efficiency_metrics.get('project_completion_efficiency', 0) < 0.7:
            improvements.append('Focus on project planning and scope management')
        
        return improvements
    
    def _identify_quality_strengths(self, coding_patterns: Dict) -> List[str]:
        """Identify code quality strengths"""
        strengths = []
        
        if coding_patterns.get('consistency_score', 0) > 0.8:
            strengths.append('Consistent coding style and patterns')
        
        bug_rate = coding_patterns.get('productivity_metrics', {}).get('bug_introduction_rate', 1)
        if bug_rate < 0.05:
            strengths.append('Low bug introduction rate')
        
        return strengths
    
    def _identify_quality_improvements(self, coding_patterns: Dict) -> List[str]:
        """Identify areas for quality improvement"""
        improvements = []
        
        if coding_patterns.get('consistency_score', 0) < 0.6:
            improvements.append('Establish consistent coding standards and patterns')
        
        productivity = coding_patterns.get('productivity_metrics', {})
        if productivity.get('bug_introduction_rate', 0) > 0.1:
            improvements.append('Focus on code quality practices to reduce bugs')
        
        return improvements
    
    def _get_learning_resources(self, technology: str) -> List[str]:
        """Get learning resources for specific technology"""
        resources = {
            'swift': ['Swift.org documentation', 'iOS App Dev with Swift course', 'SwiftUI tutorials'],
            'react': ['React official docs', 'React patterns guide', 'Modern React course'],
            'python': ['Python.org tutorial', 'Automate the Boring Stuff', 'Python best practices'],
            'javascript': ['MDN JavaScript guide', 'You Don\'t Know JS', 'JavaScript patterns'],
            'android': ['Android developer guides', 'Kotlin for Android', 'Material Design guidelines']
        }
        
        return resources.get(technology, ['General programming resources'])

async def main():
    """Main server function"""
    server = IntelligenceEngineServer()
    
    # Get port from environment or use default
    port = int(os.getenv('INTELLIGENCE_ENGINE_PORT', 8003))
    
    logger.info(f"Starting Intelligence Engine Server on port {port}")
    logger.info("Features: Developer intelligence analysis, Anti-pattern detection, Learning insights, Outcome prediction")
    
    await mcp.run(transport="stdio")

if __name__ == "__main__":
    asyncio.run(main())