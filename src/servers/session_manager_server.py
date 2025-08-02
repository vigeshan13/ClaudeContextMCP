#!/usr/bin/env python3
"""
AI Agent Context Management System - Session Manager Server

This MCP server handles session continuity, state management, bug fix context preservation,
and intelligent session restoration for solo developers working across multiple projects
and technology stacks.

Port: 8004
"""

import asyncio
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import pickle
import zlib
from collections import defaultdict, deque
import os
from dotenv import load_dotenv

from fastmcp import FastMCP

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionStateManager:
    """Manages session state and context preservation"""
    
    def __init__(self, db_path: str = "session_management.db"):
        self.db_path = db_path
        self.active_sessions = {}
        self.session_snapshots = defaultdict(deque)
        self.bug_fix_contexts = defaultdict(list)
        self.init_database()
    
    def init_database(self):
        """Initialize session management database"""
        with sqlite3.connect(self.db_path) as conn:
            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    technology TEXT NOT NULL,
                    user_id TEXT DEFAULT 'default',
                    session_type TEXT DEFAULT 'development',
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    status TEXT DEFAULT 'active',
                    context_data TEXT,
                    metadata TEXT
                )
            """)
            
            # Session snapshots for rollback functionality
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    snapshot_type TEXT NOT NULL,
                    state_data TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Bug fix contexts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bug_fix_contexts (
                    context_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    bug_description TEXT NOT NULL,
                    pre_fix_state TEXT,
                    fix_attempts TEXT,
                    solution_state TEXT,
                    lessons_learned TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved_at DATETIME,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Session continuity data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_continuity (
                    continuity_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    previous_session_id TEXT,
                    context_bridge TEXT,
                    restoration_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
            
            # Session analytics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                )
            """)
    
    async def create_session(
        self, 
        project_id: str, 
        technology: str,
        session_type: str = "development",
        previous_session_id: Optional[str] = None,
        context_data: Dict[str, Any] = None
    ) -> str:
        """Create a new development session"""
        
        session_id = self._generate_session_id(project_id, technology)
        
        # Prepare context data
        context_json = json.dumps(context_data or {})
        metadata = {
            'creation_method': 'api',
            'technology': technology,
            'session_type': session_type
        }
        
        # Store session in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions 
                (session_id, project_id, technology, session_type, context_data, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, project_id, technology, session_type, context_json, json.dumps(metadata)))
        
        # Handle session continuity
        if previous_session_id:
            await self._create_session_bridge(session_id, previous_session_id)
        
        # Initialize active session state
        self.active_sessions[session_id] = {
            'project_id': project_id,
            'technology': technology,
            'session_type': session_type,
            'start_time': datetime.now(),
            'context': context_data or {},
            'snapshots': deque(maxlen=50),  # Keep last 50 snapshots
            'bug_fixes': [],
            'activity_log': []
        }
        
        # Create initial snapshot
        await self.create_snapshot(session_id, 'initial', 'Session started')
        
        logger.info(f"Created session {session_id} for project {project_id}")
        return session_id
    
    async def create_snapshot(
        self, 
        session_id: str, 
        snapshot_type: str, 
        description: str = "",
        state_data: Dict[str, Any] = None
    ) -> str:
        """Create a session snapshot for rollback capability"""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        snapshot_id = f"snap_{session_id}_{int(datetime.now().timestamp())}"
        
        # Get current session state
        session_state = self.active_sessions[session_id].copy()
        if state_data:
            session_state.update(state_data)
        
        # Compress state data for storage
        state_json = json.dumps(session_state, default=str)
        compressed_state = zlib.compress(state_json.encode())
        
        # Store snapshot
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO session_snapshots 
                (snapshot_id, session_id, snapshot_type, state_data, description)
                VALUES (?, ?, ?, ?, ?)
            """, (snapshot_id, session_id, snapshot_type, compressed_state, description))
        
        # Update in-memory snapshots
        self.active_sessions[session_id]['snapshots'].append({
            'snapshot_id': snapshot_id,
            'timestamp': datetime.now(),
            'type': snapshot_type,
            'description': description
        })
        
        logger.info(f"Created snapshot {snapshot_id} for session {session_id}")
        return snapshot_id
    
    async def restore_snapshot(self, session_id: str, snapshot_id: str) -> Dict[str, Any]:
        """Restore session to a previous snapshot"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT state_data FROM session_snapshots 
                WHERE snapshot_id = ? AND session_id = ?
            """, (snapshot_id, session_id))
            result = cursor.fetchone()
        
        if not result:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        # Decompress and restore state
        compressed_state = result[0]
        state_json = zlib.decompress(compressed_state).decode()
        restored_state = json.loads(state_json)
        
        # Update active session
        if session_id in self.active_sessions:
            self.active_sessions[session_id].update(restored_state)
            
            # Create restoration snapshot
            await self.create_snapshot(
                session_id, 
                'restoration', 
                f'Restored from snapshot {snapshot_id}'
            )
        
        logger.info(f"Restored session {session_id} from snapshot {snapshot_id}")
        return restored_state
    
    async def start_bug_fix_context(
        self, 
        session_id: str, 
        bug_description: str,
        pre_fix_state: Dict[str, Any] = None
    ) -> str:
        """Start a bug fix context to track debugging process"""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        context_id = f"bugfix_{session_id}_{int(datetime.now().timestamp())}"
        
        # Capture pre-fix state
        current_state = self.active_sessions[session_id].copy()
        if pre_fix_state:
            current_state.update(pre_fix_state)
        
        # Create bug fix context
        bug_context = {
            'context_id': context_id,
            'bug_description': bug_description,
            'pre_fix_state': current_state,
            'fix_attempts': [],
            'start_time': datetime.now(),
            'status': 'active'
        }
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO bug_fix_contexts 
                (context_id, session_id, bug_description, pre_fix_state, fix_attempts)
                VALUES (?, ?, ?, ?, ?)
            """, (
                context_id, 
                session_id, 
                bug_description, 
                json.dumps(current_state, default=str),
                json.dumps([])
            ))
        
        # Update session state
        self.active_sessions[session_id]['bug_fixes'].append(bug_context)
        
        # Create snapshot before bug fix
        await self.create_snapshot(
            session_id, 
            'pre_bug_fix', 
            f'Before fixing: {bug_description[:50]}...'
        )
        
        logger.info(f"Started bug fix context {context_id} for session {session_id}")
        return context_id
    
    async def log_bug_fix_attempt(
        self, 
        context_id: str, 
        attempt_description: str,
        code_changes: Dict[str, Any] = None,
        outcome: str = "in_progress"
    ):
        """Log a bug fix attempt"""
        
        attempt = {
            'timestamp': datetime.now().isoformat(),
            'description': attempt_description,
            'code_changes': code_changes or {},
            'outcome': outcome
        }
        
        # Update database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT fix_attempts FROM bug_fix_contexts WHERE context_id = ?
            """, (context_id,))
            result = cursor.fetchone()
            
            if result:
                attempts = json.loads(result[0]) if result[0] else []
                attempts.append(attempt)
                
                conn.execute("""
                    UPDATE bug_fix_contexts SET fix_attempts = ? WHERE context_id = ?
                """, (json.dumps(attempts), context_id))
        
        logger.info(f"Logged bug fix attempt for context {context_id}")
    
    async def resolve_bug_fix_context(
        self, 
        context_id: str, 
        solution_description: str,
        lessons_learned: List[str] = None
    ):
        """Mark bug fix context as resolved and capture learnings"""
        
        solution_state = None
        session_id = None
        
        # Find the session and capture solution state
        for sid, session in self.active_sessions.items():
            for bug_fix in session['bug_fixes']:
                if bug_fix['context_id'] == context_id:
                    solution_state = session.copy()
                    session_id = sid
                    bug_fix['status'] = 'resolved'
                    bug_fix['resolution_time'] = datetime.now()
                    break
        
        # Update database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE bug_fix_contexts 
                SET solution_state = ?, lessons_learned = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE context_id = ?
            """, (
                json.dumps(solution_state, default=str),
                json.dumps(lessons_learned or []),
                context_id
            ))
        
        # Create post-fix snapshot
        if session_id:
            await self.create_snapshot(
                session_id, 
                'post_bug_fix', 
                f'After fixing: {solution_description[:50]}...'
            )
        
        logger.info(f"Resolved bug fix context {context_id}")
    
    async def end_session(self, session_id: str, summary: str = "") -> Dict[str, Any]:
        """End a development session and create summary"""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session_data = self.active_sessions[session_id]
        
        # Calculate session metrics
        metrics = await self._calculate_session_metrics(session_id, session_data)
        
        # Create final snapshot
        await self.create_snapshot(session_id, 'final', f'Session ended: {summary}')
        
        # Update database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sessions 
                SET end_time = CURRENT_TIMESTAMP, status = 'completed',
                    context_data = ?
                WHERE session_id = ?
            """, (json.dumps(session_data, default=str), session_id))
            
            # Store session metrics
            for metric_type, value in metrics.items():
                conn.execute("""
                    INSERT INTO session_analytics (session_id, metric_type, metric_value)
                    VALUES (?, ?, ?)
                """, (session_id, metric_type, value))
        
        # Clean up active session
        completed_session = self.active_sessions.pop(session_id)
        
        logger.info(f"Ended session {session_id}")
        return {
            'session_id': session_id,
            'duration': (datetime.now() - session_data['start_time']).total_seconds(),
            'metrics': metrics,
            'summary': summary
        }
    
    def _generate_session_id(self, project_id: str, technology: str) -> str:
        """Generate unique session ID"""
        timestamp = str(int(datetime.now().timestamp()))
        unique_str = f"{project_id}_{technology}_{timestamp}"
        return f"sess_{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"
    
    async def _create_session_bridge(self, new_session_id: str, previous_session_id: str):
        """Create bridge between sessions for continuity"""
        
        # Get previous session context
        previous_context = await self._get_session_context(previous_session_id)
        
        if previous_context:
            # Create continuity bridge
            bridge_data = {
                'previous_session_summary': previous_context.get('summary', ''),
                'carried_forward_context': previous_context.get('context', {}),
                'unresolved_issues': previous_context.get('unresolved_issues', []),
                'learned_patterns': previous_context.get('patterns_used', [])
            }
            
            # Store bridge data
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO session_continuity 
                    (continuity_id, session_id, previous_session_id, context_bridge, restoration_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    f"bridge_{new_session_id}_{previous_session_id}",
                    new_session_id,
                    previous_session_id,
                    json.dumps(bridge_data),
                    json.dumps({})
                ))
    
    async def _get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session context from database"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT context_data FROM sessions WHERE session_id = ?
            """, (session_id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                return json.loads(result[0])
        
        return None
    
    async def _calculate_session_metrics(self, session_id: str, session_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate session performance metrics"""
        
        duration = (datetime.now() - session_data['start_time']).total_seconds() / 3600  # hours
        
        metrics = {
            'duration_hours': duration,
            'snapshots_created': len(session_data.get('snapshots', [])),
            'bug_fixes_attempted': len(session_data.get('bug_fixes', [])),
            'bug_fixes_resolved': len([bf for bf in session_data.get('bug_fixes', []) if bf.get('status') == 'resolved']),
            'productivity_score': self._calculate_productivity_score(session_data, duration)
        }
        
        # Calculate bug fix success rate
        if metrics['bug_fixes_attempted'] > 0:
            metrics['bug_fix_success_rate'] = metrics['bug_fixes_resolved'] / metrics['bug_fixes_attempted']
        else:
            metrics['bug_fix_success_rate'] = 1.0
        
        return metrics
    
    def _calculate_productivity_score(self, session_data: Dict[str, Any], duration_hours: float) -> float:
        """Calculate productivity score for the session"""
        
        if duration_hours == 0:
            return 0.0
        
        # Base productivity factors
        snapshots_per_hour = len(session_data.get('snapshots', [])) / duration_hours
        bug_fix_efficiency = 1.0
        
        bug_fixes = session_data.get('bug_fixes', [])
        if bug_fixes:
            resolved_fixes = [bf for bf in bug_fixes if bf.get('status') == 'resolved']
            bug_fix_efficiency = len(resolved_fixes) / len(bug_fixes)
        
        # Normalize and combine factors
        snapshot_score = min(1.0, snapshots_per_hour / 2.0)  # Assume 2 snapshots/hour is good
        productivity_score = (snapshot_score * 0.6) + (bug_fix_efficiency * 0.4)
        
        return min(1.0, max(0.0, productivity_score))

class SessionRecommendationEngine:
    """Provides intelligent session management recommendations"""
    
    def __init__(self, db_path: str = "session_management.db"):
        self.db_path = db_path
    
    async def recommend_session_actions(self, session_id: str) -> Dict[str, Any]:
        """Recommend actions based on current session state"""
        
        session_data = await self._get_session_data(session_id)
        if not session_data:
            return {'error': 'Session not found'}
        
        recommendations = {
            'immediate_actions': [],
            'session_health': self._assess_session_health(session_data),
            'productivity_tips': [],
            'risk_alerts': []
        }
        
        # Analyze session duration
        duration_hours = self._calculate_session_duration(session_data)
        
        if duration_hours > 4:
            recommendations['immediate_actions'].append('Consider taking a break - long sessions can reduce productivity')
            recommendations['risk_alerts'].append('Extended session detected - risk of fatigue-induced errors')
        
        # Analyze snapshot frequency
        snapshots = json.loads(session_data.get('context_data', '{}')).get('snapshots', [])
        if len(snapshots) < max(1, duration_hours // 2):
            recommendations['productivity_tips'].append('Create more frequent snapshots for better rollback capability')
        
        # Analyze bug fix patterns
        bug_fixes = self._get_session_bug_fixes(session_id)
        if len(bug_fixes) > 3:
            recommendations['risk_alerts'].append('Multiple bug fixes in session - consider code review')
        
        unresolved_bugs = [bf for bf in bug_fixes if not bf.get('resolved_at')]
        if unresolved_bugs:
            recommendations['immediate_actions'].append(f'{len(unresolved_bugs)} unresolved bugs need attention')
        
        return recommendations
    
    async def predict_session_outcome(self, session_id: str) -> Dict[str, Any]:
        """Predict likely session outcomes based on patterns"""
        
        session_data = await self._get_session_data(session_id)
        if not session_data:
            return {'error': 'Session not found'}
        
        # Analyze current session patterns
        duration_hours = self._calculate_session_duration(session_data)
        context_data = json.loads(session_data.get('context_data', '{}'))
        
        # Get historical session data for comparison
        historical_metrics = await self._get_historical_session_metrics(
            session_data['project_id'], 
            session_data['technology']
        )
        
        predictions = {
            'completion_probability': self._predict_completion_probability(duration_hours, context_data, historical_metrics),
            'quality_risk_score': self._predict_quality_risk(duration_hours, context_data, historical_metrics),
            'estimated_remaining_time': self._predict_remaining_time(duration_hours, context_data, historical_metrics),
            'recommended_actions': self._generate_predictive_recommendations(duration_hours, context_data)
        }
        
        return predictions
    
    def _assess_session_health(self, session_data: Dict[str, Any]) -> str:
        """Assess overall session health"""
        
        duration_hours = self._calculate_session_duration(session_data)
        context_data = json.loads(session_data.get('context_data', '{}'))
        
        health_score = 1.0
        
        # Penalize very long sessions
        if duration_hours > 6:
            health_score -= 0.3
        elif duration_hours > 4:
            health_score -= 0.1
        
        # Check bug fix ratio
        bug_fixes = context_data.get('bug_fixes', [])
        if len(bug_fixes) > duration_hours * 2:  # More than 2 bugs per hour
            health_score -= 0.2
        
        # Check snapshot frequency
        snapshots = context_data.get('snapshots', [])
        expected_snapshots = max(1, duration_hours // 0.5)  # Every 30 minutes
        if len(snapshots) < expected_snapshots * 0.5:
            health_score -= 0.1
        
        if health_score >= 0.8:
            return 'excellent'
        elif health_score >= 0.6:
            return 'good'
        elif health_score >= 0.4:
            return 'fair'
        else:
            return 'poor'
    
    def _calculate_session_duration(self, session_data: Dict[str, Any]) -> float:
        """Calculate session duration in hours"""
        
        start_time_str = session_data.get('start_time')
        if not start_time_str:
            return 0.0
        
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        duration = datetime.now() - start_time.replace(tzinfo=None)
        return duration.total_seconds() / 3600
    
    def _get_session_bug_fixes(self, session_id: str) -> List[Dict[str, Any]]:
        """Get bug fixes for a session"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT context_id, bug_description, created_at, resolved_at
                FROM bug_fix_contexts 
                WHERE session_id = ?
            """, (session_id,))
            
            return [
                {
                    'context_id': row[0],
                    'description': row[1], 
                    'created_at': row[2],
                    'resolved_at': row[3]
                }
                for row in cursor.fetchall()
            ]
    
    async def _get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from database"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT session_id, project_id, technology, session_type, 
                       start_time, end_time, status, context_data, metadata
                FROM sessions 
                WHERE session_id = ?
            """, (session_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'session_id': result[0],
                    'project_id': result[1],
                    'technology': result[2],
                    'session_type': result[3],
                    'start_time': result[4],
                    'end_time': result[5],
                    'status': result[6],
                    'context_data': result[7] or '{}',
                    'metadata': result[8] or '{}'
                }
        
        return None
    
    async def _get_historical_session_metrics(self, project_id: str, technology: str) -> Dict[str, Any]:
        """Get historical session metrics for prediction"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Get average session duration
            cursor = conn.execute("""
                SELECT AVG(JULIANDAY(end_time) - JULIANDAY(start_time)) * 24 as avg_duration_hours
                FROM sessions 
                WHERE project_id = ? AND technology = ? AND end_time IS NOT NULL
            """, (project_id, technology))
            
            avg_duration = cursor.fetchone()[0] or 2.0
            
            # Get average metrics
            cursor = conn.execute("""
                SELECT metric_type, AVG(metric_value) 
                FROM session_analytics sa
                JOIN sessions s ON sa.session_id = s.session_id
                WHERE s.project_id = ? AND s.technology = ?
                GROUP BY metric_type
            """, (project_id, technology))
            
            metrics = dict(cursor.fetchall())
        
        return {
            'avg_duration_hours': avg_duration,
            'avg_productivity_score': metrics.get('productivity_score', 0.7),
            'avg_bug_fix_success_rate': metrics.get('bug_fix_success_rate', 0.8),
            'avg_snapshots_per_session': metrics.get('snapshots_created', 5)
        }
    
    def _predict_completion_probability(self, duration_hours: float, context_data: Dict, historical: Dict) -> float:
        """Predict probability of successful session completion"""
        
        base_probability = 0.8
        
        # Adjust based on duration
        avg_duration = historical.get('avg_duration_hours', 2.0)
        if duration_hours > avg_duration * 1.5:
            base_probability -= 0.2
        elif duration_hours < avg_duration * 0.5:
            base_probability += 0.1
        
        # Adjust based on bug fixes
        bug_fixes = context_data.get('bug_fixes', [])
        unresolved_bugs = len([bf for bf in bug_fixes if bf.get('status') != 'resolved'])
        if unresolved_bugs > 2:
            base_probability -= 0.15 * unresolved_bugs
        
        return max(0.1, min(1.0, base_probability))
    
    def _predict_quality_risk(self, duration_hours: float, context_data: Dict, historical: Dict) -> float:
        """Predict risk of quality issues"""
        
        risk_score = 0.2  # Base risk
        
        # Higher risk for longer sessions
        if duration_hours > 4:
            risk_score += (duration_hours - 4) * 0.1
        
        # Higher risk with many bug fixes
        bug_fixes = context_data.get('bug_fixes', [])
        if len(bug_fixes) > 3:
            risk_score += (len(bug_fixes) - 3) * 0.1
        
        # Lower risk with frequent snapshots
        snapshots = context_data.get('snapshots', [])
        expected_snapshots = max(1, duration_hours * 2)  # 2 per hour
        if len(snapshots) >= expected_snapshots:
            risk_score -= 0.1
        
        return max(0.0, min(1.0, risk_score))
    
    def _predict_remaining_time(self, duration_hours: float, context_data: Dict, historical: Dict) -> float:
        """Predict remaining session time in hours"""
        
        avg_duration = historical.get('avg_duration_hours', 2.0)
        
        # Simple prediction based on current progress indicators
        bug_fixes = context_data.get('bug_fixes', [])
        unresolved_bugs = len([bf for bf in bug_fixes if bf.get('status') != 'resolved'])
        
        # Base remaining time
        remaining = max(0, avg_duration - duration_hours)
        
        # Add time for unresolved bugs
        remaining += unresolved_bugs * 0.5  # 30 minutes per bug
        
        return max(0.25, remaining)  # Minimum 15 minutes
    
    def _generate_predictive_recommendations(self, duration_hours: float, context_data: Dict) -> List[str]:
        """Generate recommendations based on predictions"""
        
        recommendations = []
        
        bug_fixes = context_data.get('bug_fixes', [])
        unresolved_bugs = [bf for bf in bug_fixes if bf.get('status') != 'resolved']
        
        if duration_hours > 3 and unresolved_bugs:
            recommendations.append('Consider taking a break before tackling remaining bugs')
        
        if len(bug_fixes) > 3:
            recommendations.append('High bug count detected - consider code review or refactoring')
        
        snapshots = context_data.get('snapshots', [])
        if len(snapshots) < duration_hours:
            recommendations.append('Create more snapshots to improve rollback capability')
        
        if duration_hours > 4:
            recommendations.append('Long session detected - plan to wrap up soon')
        
        return recommendations

# Initialize FastMCP
mcp = FastMCP("Session Manager Server")

class SessionManagerServer:
    """Main session manager server class"""
    
    def __init__(self):
        self.state_manager = SessionStateManager()
        self.recommendation_engine = SessionRecommendationEngine()
        
        # Use global MCP server
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @mcp.tool()
        async def create_development_session(
            project_id: str,
            technology: str,
            session_type: str = "development",
            previous_session_id: str = None,
            context_description: str = ""
        ) -> Dict[str, Any]:
            """
            Create a new development session with intelligent context management.
            
            Args:
                project_id: Project identifier
                technology: Primary technology (swift, react, python, javascript, android)
                session_type: Type of session (development, debugging, refactoring, learning)
                previous_session_id: Optional previous session for continuity
                context_description: Description of what you plan to work on
            """
            
            try:
                # Prepare context data
                context_data = {
                    'description': context_description,
                    'planned_activities': [],
                    'initial_state': {
                        'timestamp': datetime.now().isoformat(),
                        'context': context_description
                    }
                }
                
                # Create session
                session_id = await self.state_manager.create_session(
                    project_id=project_id,
                    technology=technology,
                    session_type=session_type,
                    previous_session_id=previous_session_id,
                    context_data=context_data
                )
                
                # Get initial recommendations
                recommendations = await self.recommendation_engine.recommend_session_actions(session_id)
                
                return {
                    'session_id': session_id,
                    'project_id': project_id,
                    'technology': technology,
                    'session_type': session_type,
                    'created_at': datetime.now().isoformat(),
                    'continuity_from': previous_session_id,
                    'initial_recommendations': recommendations,
                    'status': 'active'
                }
                
            except Exception as e:
                logger.error(f"Session creation failed: {str(e)}")
                return {
                    'error': f"Session creation failed: {str(e)}",
                    'project_id': project_id,
                    'technology': technology
                }
        
        @mcp.tool()
        async def create_session_snapshot(
            session_id: str,
            snapshot_type: str = "checkpoint",
            description: str = "",
            current_code_state: str = "",
            working_notes: str = ""
        ) -> Dict[str, Any]:
            """
            Create a session snapshot for rollback capability.
            
            Args:
                session_id: Session identifier
                snapshot_type: Type of snapshot (checkpoint, pre_fix, post_fix, milestone)
                description: Description of current state
                current_code_state: Current state of code being worked on
                working_notes: Notes about current progress
            """
            
            try:
                # Prepare state data
                state_data = {
                    'code_state': current_code_state,
                    'working_notes': working_notes,
                    'timestamp': datetime.now().isoformat(),
                    'snapshot_context': description
                }
                
                # Create snapshot
                snapshot_id = await self.state_manager.create_snapshot(
                    session_id=session_id,
                    snapshot_type=snapshot_type,
                    description=description,
                    state_data=state_data
                )
                
                return {
                    'snapshot_id': snapshot_id,
                    'session_id': session_id,
                    'snapshot_type': snapshot_type,
                    'description': description,
                    'created_at': datetime.now().isoformat(),
                    'status': 'created'
                }
                
            except Exception as e:
                logger.error(f"Snapshot creation failed: {str(e)}")
                return {
                    'error': f"Snapshot creation failed: {str(e)}",
                    'session_id': session_id
                }
        
        @mcp.tool()
        async def start_bug_fix_tracking(
            session_id: str,
            bug_description: str,
            error_message: str = "",
            reproduction_steps: str = "",
            initial_hypothesis: str = ""
        ) -> Dict[str, Any]:
            """
            Start tracking a bug fix process with full context preservation.
            
            Args:
                session_id: Session identifier
                bug_description: Description of the bug
                error_message: Error message if any
                reproduction_steps: Steps to reproduce the bug
                initial_hypothesis: Initial thoughts on the cause
            """
            
            try:
                # Prepare pre-fix state
                pre_fix_state = {
                    'bug_details': {
                        'description': bug_description,
                        'error_message': error_message,
                        'reproduction_steps': reproduction_steps,
                        'initial_hypothesis': initial_hypothesis
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                # Start bug fix context
                context_id = await self.state_manager.start_bug_fix_context(
                    session_id=session_id,
                    bug_description=bug_description,
                    pre_fix_state=pre_fix_state
                )
                
                return {
                    'bug_fix_context_id': context_id,
                    'session_id': session_id,
                    'bug_description': bug_description,
                    'tracking_started': datetime.now().isoformat(),
                    'pre_fix_snapshot_created': True,
                    'status': 'tracking_active'
                }
                
            except Exception as e:
                logger.error(f"Bug fix tracking failed: {str(e)}")
                return {
                    'error': f"Bug fix tracking failed: {str(e)}",
                    'session_id': session_id
                }
        
        @mcp.tool()
        async def log_bug_fix_attempt(
            bug_fix_context_id: str,
            attempt_description: str,
            changes_made: str = "",
            test_results: str = "",
            outcome: str = "in_progress"
        ) -> Dict[str, Any]:
            """
            Log a bug fix attempt with details.
            
            Args:
                bug_fix_context_id: Bug fix context identifier
                attempt_description: Description of what was attempted
                changes_made: Code or configuration changes made
                test_results: Results of testing the fix
                outcome: Outcome (in_progress, failed, success, partial_success)
            """
            
            try:
                # Prepare code changes data
                code_changes = {
                    'description': changes_made,
                    'test_results': test_results,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Log the attempt
                await self.state_manager.log_bug_fix_attempt(
                    context_id=bug_fix_context_id,
                    attempt_description=attempt_description,
                    code_changes=code_changes,
                    outcome=outcome
                )
                
                return {
                    'bug_fix_context_id': bug_fix_context_id,
                    'attempt_logged': True,
                    'outcome': outcome,
                    'logged_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Bug fix attempt logging failed: {str(e)}")
                return {
                    'error': f"Bug fix attempt logging failed: {str(e)}",
                    'bug_fix_context_id': bug_fix_context_id
                }
        
        @mcp.tool()
        async def resolve_bug_fix(
            bug_fix_context_id: str,
            solution_description: str,
            final_code_state: str = "",
            lessons_learned: str = "",
            prevention_strategies: str = ""
        ) -> Dict[str, Any]:
            """
            Mark bug fix as resolved and capture learnings.
            
            Args:
                bug_fix_context_id: Bug fix context identifier
                solution_description: Description of the final solution
                final_code_state: Final state of the code
                lessons_learned: What was learned from this bug fix
                prevention_strategies: How to prevent similar bugs
            """
            
            try:
                # Parse lessons learned
                lessons_list = [lesson.strip() for lesson in lessons_learned.split('\n') if lesson.strip()]
                if prevention_strategies:
                    lessons_list.extend([f"Prevention: {strategy.strip()}" for strategy in prevention_strategies.split('\n') if strategy.strip()])
                
                # Resolve the bug fix context
                await self.state_manager.resolve_bug_fix_context(
                    context_id=bug_fix_context_id,
                    solution_description=solution_description,
                    lessons_learned=lessons_list
                )
                
                return {
                    'bug_fix_context_id': bug_fix_context_id,
                    'resolved': True,
                    'solution_description': solution_description,
                    'lessons_captured': len(lessons_list),
                    'resolved_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Bug fix resolution failed: {str(e)}")
                return {
                    'error': f"Bug fix resolution failed: {str(e)}",
                    'bug_fix_context_id': bug_fix_context_id
                }
        
        @mcp.tool()
        async def restore_session_snapshot(
            session_id: str,
            snapshot_id: str,
            restoration_reason: str = ""
        ) -> Dict[str, Any]:
            """
            Restore session to a previous snapshot state.
            
            Args:
                session_id: Session identifier
                snapshot_id: Snapshot identifier to restore to
                restoration_reason: Reason for restoration
            """
            
            try:
                # Restore the snapshot
                restored_state = await self.state_manager.restore_snapshot(
                    session_id=session_id,
                    snapshot_id=snapshot_id
                )
                
                return {
                    'session_id': session_id,
                    'snapshot_id': snapshot_id,
                    'restored': True,
                    'restoration_reason': restoration_reason,
                    'restored_at': datetime.now().isoformat(),
                    'restored_state_summary': self._summarize_state(restored_state)
                }
                
            except Exception as e:
                logger.error(f"Snapshot restoration failed: {str(e)}")
                return {
                    'error': f"Snapshot restoration failed: {str(e)}",
                    'session_id': session_id,
                    'snapshot_id': snapshot_id
                }
        
        @mcp.tool()
        async def get_session_recommendations(
            session_id: str,
            include_predictions: bool = True
        ) -> Dict[str, Any]:
            """
            Get intelligent recommendations for the current session.
            
            Args:
                session_id: Session identifier
                include_predictions: Whether to include outcome predictions
            """
            
            try:
                # Get current recommendations
                recommendations = await self.recommendation_engine.recommend_session_actions(session_id)
                
                result = {
                    'session_id': session_id,
                    'recommendations': recommendations,
                    'generated_at': datetime.now().isoformat()
                }
                
                # Add predictions if requested
                if include_predictions:
                    predictions = await self.recommendation_engine.predict_session_outcome(session_id)
                    result['predictions'] = predictions
                
                return result
                
            except Exception as e:
                logger.error(f"Recommendation generation failed: {str(e)}")
                return {
                    'error': f"Recommendation generation failed: {str(e)}",
                    'session_id': session_id
                }
        
        @mcp.tool()
        async def end_development_session(
            session_id: str,
            session_summary: str = "",
            achievements: str = "",
            next_steps: str = "",
            unresolved_issues: str = ""
        ) -> Dict[str, Any]:
            """
            End a development session and create summary.
            
            Args:
                session_id: Session identifier
                session_summary: Summary of what was accomplished
                achievements: Key achievements in this session
                next_steps: Planned next steps for future sessions
                unresolved_issues: Issues that remain unresolved
            """
            
            try:
                # Prepare session summary
                full_summary = f"""
                Summary: {session_summary}
                Achievements: {achievements}
                Next Steps: {next_steps}
                Unresolved Issues: {unresolved_issues}
                """.strip()
                
                # End the session
                session_metrics = await self.state_manager.end_session(
                    session_id=session_id,
                    summary=full_summary
                )
                
                return {
                    'session_id': session_id,
                    'ended': True,
                    'ended_at': datetime.now().isoformat(),
                    'session_metrics': session_metrics,
                    'summary': {
                        'session_summary': session_summary,
                        'achievements': achievements,
                        'next_steps': next_steps,
                        'unresolved_issues': unresolved_issues
                    }
                }
                
            except Exception as e:
                logger.error(f"Session ending failed: {str(e)}")
                return {
                    'error': f"Session ending failed: {str(e)}",
                    'session_id': session_id
                }
    
    def _summarize_state(self, state: Dict[str, Any]) -> str:
        """Create a summary of the restored state"""
        
        summary_parts = []
        
        if 'context' in state and state['context']:
            summary_parts.append(f"Context: {str(state['context'])[:100]}...")
        
        if 'snapshots' in state:
            summary_parts.append(f"Snapshots: {len(state['snapshots'])}")
        
        if 'bug_fixes' in state:
            summary_parts.append(f"Bug fixes: {len(state['bug_fixes'])}")
        
        if 'start_time' in state:
            summary_parts.append(f"Session started: {state['start_time']}")
        
        return "; ".join(summary_parts) if summary_parts else "State restored successfully"

async def main():
    """Main server function"""
    server = SessionManagerServer()
    
    # Get port from environment or use default
    port = int(os.getenv('SESSION_MANAGER_PORT', 8004))
    
    logger.info(f"Starting Session Manager Server on port {port}")
    logger.info("Features: Session continuity, Bug fix tracking, Snapshot management, Intelligent recommendations")
    
    # Start the FastMCP server
    await mcp.run(transport="stdio")

if __name__ == "__main__":
    asyncio.run(main())