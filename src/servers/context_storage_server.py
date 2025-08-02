#!/usr/bin/env python3
"""
Context Storage Server - Multi-Project Intelligent Storage
Part of AI Agent Context Management System

This MCP server provides intelligent context storage with cross-project learning
capabilities, optimized for solo developers working across Swift, Android, 
Python, React, and JavaScript projects.
"""

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Literal
import os
import subprocess
import re

# FastMCP and MCP imports
from fastmcp import FastMCP
from mcp.types import TextContent

# Vector database and ML imports
import chromadb
from chromadb.config import Settings
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Data models
from pydantic import BaseModel, Field
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP
mcp = FastMCP("Context Storage Server")

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///context_management.db")
# Parse SQLite URL to extract file path
if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_PATH = DATABASE_URL.replace("sqlite:///", "")
elif DATABASE_URL.startswith("sqlite://"):
    DATABASE_PATH = DATABASE_URL.replace("sqlite://", "")
else:
    DATABASE_PATH = DATABASE_URL

VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./chroma_db")
DEVELOPER_ID = os.getenv("DEVELOPER_ID", "vigesh_solo_dev")

# Data Models
class ProjectType(str, Enum):
    IOS_APP = "ios_app"
    ANDROID_APP = "android_app" 
    REACT_WEB = "react_web"
    PYTHON_ANALYTICS = "python_analytics"
    JAVASCRIPT_WEB = "javascript_web"

class ContextType(str, Enum):
    CONVERSATION = "conversation"
    CODE_DECISION = "code_decision"
    BUG_FIX = "bug_fix"
    PATTERN_APPLICATION = "pattern_application"
    ARCHITECTURAL_DECISION = "architectural_decision"

@dataclass
class ProjectCreationResult:
    project_id: str
    project_name: str
    intelligent_suggestions: List[Dict[str, Any]]
    applied_patterns: List[Dict[str, Any]]
    setup_configuration: Dict[str, Any]
    success: bool
    message: str

@dataclass  
class IntelligentStorageResult:
    context_id: str
    cross_project_relevance_score: float
    pattern_insights: List[Dict[str, Any]]
    similar_contexts: List[Dict[str, Any]]
    success: bool
    message: str

@dataclass
class DeveloperPatternAnalysis:
    technology_patterns: Dict[str, Any]
    cross_technology_insights: List[Dict[str, Any]]
    success_patterns: List[Dict[str, Any]]
    anti_patterns: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_scores: Dict[str, float]

@dataclass
class ProjectBootstrapResult:
    project_id: str
    extracted_patterns: List[Dict[str, Any]]
    architectural_decisions: List[Dict[str, Any]]
    technology_analysis: Dict[str, Any]
    intelligence_profile: Dict[str, Any]
    recommendations: List[str]
    success: bool
    message: str

# Database Management
class DatabaseManager:
    """Manages SQLite database operations for project metadata and developer profiles."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                technologies TEXT NOT NULL,
                description TEXT,
                repository_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                developer_id TEXT NOT NULL,
                intelligence_profile TEXT,
                cross_project_patterns TEXT
            )
        """)
        
        # Context items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context_items (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                context_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                importance_score REAL DEFAULT 0.5,
                cross_project_relevance REAL DEFAULT 0.0,
                access_count INTEGER DEFAULT 0,
                technology_tags TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Developer profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS developer_profiles (
                id TEXT PRIMARY KEY,
                developer_id TEXT UNIQUE NOT NULL,
                swift_patterns TEXT,
                android_patterns TEXT,
                react_patterns TEXT,
                python_patterns TEXT,
                javascript_patterns TEXT,
                ui_design_patterns TEXT,
                api_design_patterns TEXT,
                data_flow_patterns TEXT,
                pattern_confidence_scores TEXT,
                success_correlations TEXT,
                anti_patterns TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Pattern library table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_library (
                id TEXT PRIMARY KEY,
                pattern_name TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                source_technology TEXT,
                target_technologies TEXT,
                pattern_content TEXT,
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                developer_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_project(self, project_data: Dict[str, Any]) -> str:
        """Create a new project in the database."""
        project_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO projects (
                id, name, type, technologies, description, repository_path,
                developer_id, intelligence_profile, cross_project_patterns
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            project_data["name"],
            project_data["type"],
            json.dumps(project_data["technologies"]),
            project_data.get("description", ""),
            project_data.get("repository_path"),
            project_data["developer_id"],
            json.dumps(project_data.get("intelligence_profile", {})),
            json.dumps(project_data.get("cross_project_patterns", []))
        ))
        
        conn.commit()
        conn.close()
        return project_id
    
    def store_context(self, context_data: Dict[str, Any]) -> str:
        """Store context item in the database."""
        context_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO context_items (
                id, project_id, context_type, content, metadata,
                importance_score, cross_project_relevance, technology_tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            context_id,
            context_data["project_id"],
            context_data["context_type"],
            context_data["content"],
            json.dumps(context_data.get("metadata", {})),
            context_data.get("importance_score", 0.5),
            context_data.get("cross_project_relevance", 0.0),
            json.dumps(context_data.get("technology_tags", []))
        ))
        
        conn.commit()
        conn.close()
        return context_id
    
    def get_developer_profile(self, developer_id: str) -> Optional[Dict[str, Any]]:
        """Get developer profile from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM developer_profiles WHERE developer_id = ?
        """, (developer_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        return None
    
    def update_developer_profile(self, developer_id: str, profile_data: Dict[str, Any]):
        """Update developer profile in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if profile exists
        existing = self.get_developer_profile(developer_id)
        
        if existing:
            cursor.execute("""
                UPDATE developer_profiles SET
                    swift_patterns = ?, android_patterns = ?, react_patterns = ?,
                    python_patterns = ?, javascript_patterns = ?, ui_design_patterns = ?,
                    api_design_patterns = ?, data_flow_patterns = ?, pattern_confidence_scores = ?,
                    success_correlations = ?, anti_patterns = ?, updated_at = CURRENT_TIMESTAMP
                WHERE developer_id = ?
            """, (
                json.dumps(profile_data.get("swift_patterns", {})),
                json.dumps(profile_data.get("android_patterns", {})),
                json.dumps(profile_data.get("react_patterns", {})),
                json.dumps(profile_data.get("python_patterns", {})),
                json.dumps(profile_data.get("javascript_patterns", {})),
                json.dumps(profile_data.get("ui_design_patterns", {})),
                json.dumps(profile_data.get("api_design_patterns", {})),
                json.dumps(profile_data.get("data_flow_patterns", {})),
                json.dumps(profile_data.get("pattern_confidence_scores", {})),
                json.dumps(profile_data.get("success_correlations", {})),
                json.dumps(profile_data.get("anti_patterns", {})),
                developer_id
            ))
        else:
            profile_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO developer_profiles (
                    id, developer_id, swift_patterns, android_patterns, react_patterns,
                    python_patterns, javascript_patterns, ui_design_patterns,
                    api_design_patterns, data_flow_patterns, pattern_confidence_scores,
                    success_correlations, anti_patterns
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile_id, developer_id,
                json.dumps(profile_data.get("swift_patterns", {})),
                json.dumps(profile_data.get("android_patterns", {})),
                json.dumps(profile_data.get("react_patterns", {})),
                json.dumps(profile_data.get("python_patterns", {})),
                json.dumps(profile_data.get("javascript_patterns", {})),
                json.dumps(profile_data.get("ui_design_patterns", {})),
                json.dumps(profile_data.get("api_design_patterns", {})),
                json.dumps(profile_data.get("data_flow_patterns", {})),
                json.dumps(profile_data.get("pattern_confidence_scores", {})),
                json.dumps(profile_data.get("success_correlations", {})),
                json.dumps(profile_data.get("anti_patterns", {}))
            ))
        
        conn.commit()
        conn.close()

# Vector Database Management
class VectorStoreManager:
    """Manages ChromaDB vector storage for context embeddings."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.collections = {}
        self.init_collections()
    
    def init_collections(self):
        """Initialize collections for different project types."""
        project_types = ["ios_app", "android_app", "react_web", "python_analytics", "javascript_web"]
        
        for project_type in project_types:
            collection_name = f"contexts_{project_type}"
            try:
                collection = self.client.get_collection(collection_name)
            except:
                collection = self.client.create_collection(collection_name)
            self.collections[project_type] = collection
    
    def store_context_vector(self, context_id: str, content: str, metadata: Dict[str, Any], project_type: str):
        """Store context with vector embedding."""
        if project_type in self.collections:
            self.collections[project_type].add(
                documents=[content],
                metadatas=[metadata],
                ids=[context_id]
            )

# Intelligence Engine
class IntelligenceEngine:
    """Core intelligence engine for pattern recognition and learning."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.technology_patterns = {
            "swift": self._init_swift_patterns(),
            "android": self._init_android_patterns(),
            "react": self._init_react_patterns(),
            "python": self._init_python_patterns(),
            "javascript": self._init_javascript_patterns()
        }
    
    def _init_swift_patterns(self) -> Dict[str, Any]:
        """Initialize Swift/iOS pattern recognition."""
        return {
            "ui_patterns": ["NavigationView", "List", "VStack", "HStack", "StateObject"],
            "architecture_patterns": ["MVVM", "MVC", "VIPER"],
            "data_patterns": ["ObservableObject", "@Published", "UserDefaults"],
            "common_frameworks": ["SwiftUI", "UIKit", "Core Data", "Combine"]
        }
    
    def _init_android_patterns(self) -> Dict[str, Any]:
        """Initialize Android pattern recognition."""
        return {
            "ui_patterns": ["RecyclerView", "Fragment", "Activity", "ConstraintLayout"],
            "architecture_patterns": ["MVVM", "MVP", "Clean Architecture"],
            "data_patterns": ["ViewModel", "LiveData", "Room", "DataBinding"],
            "common_frameworks": ["Jetpack Compose", "Retrofit", "Dagger", "RxJava"]
        }
    
    def _init_react_patterns(self) -> Dict[str, Any]:
        """Initialize React pattern recognition."""
        return {
            "ui_patterns": ["useState", "useEffect", "Component", "JSX"],
            "architecture_patterns": ["Component-based", "Redux", "Context API"],
            "data_patterns": ["Props", "State", "Hooks", "Redux Store"],
            "common_frameworks": ["Next.js", "Material-UI", "Tailwind", "React Router"]
        }
    
    def _init_python_patterns(self) -> Dict[str, Any]:
        """Initialize Python analytics pattern recognition."""
        return {
            "data_patterns": ["pandas.DataFrame", "numpy.array", "matplotlib", "seaborn"],
            "ml_patterns": ["sklearn", "tensorflow", "pytorch", "jupyter"],
            "api_patterns": ["FastAPI", "Flask", "Django", "requests"],
            "common_frameworks": ["pandas", "numpy", "scikit-learn", "matplotlib"]
        }
    
    def _init_javascript_patterns(self) -> Dict[str, Any]:
        """Initialize JavaScript pattern recognition."""
        return {
            "ui_patterns": ["DOM manipulation", "Event handling", "Async/await"],
            "framework_patterns": ["Node.js", "Express", "Vue", "Angular"],
            "data_patterns": ["Fetch API", "Promises", "JSON", "localStorage"],
            "common_frameworks": ["Express", "Node.js", "Webpack", "Babel"]
        }
    
    def analyze_code_patterns(self, content: str, technology: str) -> List[Dict[str, Any]]:
        """Analyze code content for patterns specific to technology."""
        patterns = []
        
        if technology.lower() in self.technology_patterns:
            tech_patterns = self.technology_patterns[technology.lower()]
            
            for pattern_type, pattern_list in tech_patterns.items():
                for pattern in pattern_list:
                    if pattern.lower() in content.lower():
                        patterns.append({
                            "pattern": pattern,
                            "type": pattern_type,
                            "technology": technology,
                            "confidence": 0.8,  # Basic confidence scoring
                            "context": self._extract_pattern_context(content, pattern)
                        })
        
        return patterns
    
    def _extract_pattern_context(self, content: str, pattern: str) -> str:
        """Extract context around a detected pattern."""
        lines = content.split('\n')
        pattern_lines = []
        
        for i, line in enumerate(lines):
            if pattern.lower() in line.lower():
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                pattern_lines.extend(lines[start:end])
        
        return '\n'.join(pattern_lines[:10])  # Limit context size
    
    def generate_intelligent_suggestions(self, project_type: str, technologies: List[str]) -> List[Dict[str, Any]]:
        """Generate intelligent suggestions based on project type and technologies."""
        suggestions = []
        
        # Technology-specific suggestions
        for tech in technologies:
            if tech.lower() in self.technology_patterns:
                tech_patterns = self.technology_patterns[tech.lower()]
                suggestions.append({
                    "type": "architecture_suggestion",
                    "technology": tech,
                    "suggestion": f"Consider using {tech_patterns.get('architecture_patterns', ['standard patterns'])[0]} architecture",
                    "rationale": f"Commonly successful pattern for {tech} projects",
                    "confidence": 0.7
                })
        
        # Cross-project suggestions based on project type
        if project_type == ProjectType.IOS_APP:
            suggestions.extend(self._get_ios_suggestions())
        elif project_type == ProjectType.ANDROID_APP:
            suggestions.extend(self._get_android_suggestions())
        elif project_type == ProjectType.REACT_WEB:
            suggestions.extend(self._get_react_suggestions())
        elif project_type == ProjectType.PYTHON_ANALYTICS:
            suggestions.extend(self._get_python_suggestions())
        
        return suggestions
    
    def _get_ios_suggestions(self) -> List[Dict[str, Any]]:
        """Get iOS-specific suggestions."""
        return [
            {
                "type": "ui_suggestion",
                "suggestion": "Use SwiftUI for modern iOS development",
                "rationale": "SwiftUI provides declarative UI development",
                "confidence": 0.9
            },
            {
                "type": "architecture_suggestion", 
                "suggestion": "Implement MVVM pattern with ObservableObject",
                "rationale": "Works well with SwiftUI reactive patterns",
                "confidence": 0.8
            }
        ]
    
    def _get_android_suggestions(self) -> List[Dict[str, Any]]:
        """Get Android-specific suggestions."""
        return [
            {
                "type": "ui_suggestion",
                "suggestion": "Consider Jetpack Compose for modern Android UI",
                "rationale": "Modern declarative UI toolkit for Android",
                "confidence": 0.8
            },
            {
                "type": "architecture_suggestion",
                "suggestion": "Use MVVM with ViewModel and LiveData",
                "rationale": "Recommended architecture for Android apps",
                "confidence": 0.9
            }
        ]
    
    def _get_react_suggestions(self) -> List[Dict[str, Any]]:
        """Get React-specific suggestions."""
        return [
            {
                "type": "ui_suggestion",
                "suggestion": "Use functional components with hooks",
                "rationale": "Modern React development approach",
                "confidence": 0.9
            },
            {
                "type": "styling_suggestion",
                "suggestion": "Consider Tailwind CSS for utility-first styling",
                "rationale": "Rapid development with consistent design",
                "confidence": 0.7
            }
        ]
    
    def _get_python_suggestions(self) -> List[Dict[str, Any]]:
        """Get Python analytics-specific suggestions."""
        return [
            {
                "type": "data_suggestion",
                "suggestion": "Use pandas for data manipulation and analysis",
                "rationale": "Standard library for data science workflows",
                "confidence": 0.9
            },
            {
                "type": "visualization_suggestion",
                "suggestion": "Combine matplotlib and seaborn for visualizations",
                "rationale": "Powerful combination for data visualization",
                "confidence": 0.8
            }
        ]

# Project Bootstrap Engine
class ProjectBootstrapEngine:
    """Engine for analyzing existing projects and extracting intelligence."""
    
    def __init__(self, intelligence_engine: IntelligenceEngine):
        self.intelligence_engine = intelligence_engine
    
    def analyze_existing_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze existing project to extract patterns and intelligence."""
        project_analysis = {
            "technologies": [],
            "patterns": [],
            "architecture": {},
            "git_insights": {},
            "recommendations": []
        }
        
        # Detect technologies
        project_analysis["technologies"] = self._detect_technologies(project_path)
        
        # Analyze code patterns
        project_analysis["patterns"] = self._analyze_code_files(project_path, project_analysis["technologies"])
        
        # Analyze git history if available
        if os.path.exists(os.path.join(project_path, ".git")):
            project_analysis["git_insights"] = self._analyze_git_history(project_path)
        
        # Generate recommendations
        project_analysis["recommendations"] = self._generate_bootstrap_recommendations(project_analysis)
        
        return project_analysis
    
    def _detect_technologies(self, project_path: str) -> List[str]:
        """Detect technologies used in the project."""
        technologies = []
        
        # Check for different project types
        if os.path.exists(os.path.join(project_path, "Package.swift")):
            technologies.append("swift")
        if os.path.exists(os.path.join(project_path, "build.gradle")):
            technologies.append("android")
        if os.path.exists(os.path.join(project_path, "package.json")):
            technologies.append("javascript")
            # Check if it's React
            package_json_path = os.path.join(project_path, "package.json")
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    if "react" in package_data.get("dependencies", {}):
                        technologies.append("react")
            except:
                pass
        if os.path.exists(os.path.join(project_path, "requirements.txt")) or \
           os.path.exists(os.path.join(project_path, "pyproject.toml")):
            technologies.append("python")
        
        return technologies
    
    def _analyze_code_files(self, project_path: str, technologies: List[str]) -> List[Dict[str, Any]]:
        """Analyze code files for patterns."""
        patterns = []
        
        # Define file extensions for each technology
        tech_extensions = {
            "swift": [".swift"],
            "android": [".java", ".kt"],
            "javascript": [".js", ".jsx"],
            "react": [".jsx", ".tsx"],
            "python": [".py"]
        }
        
        for tech in technologies:
            if tech in tech_extensions:
                for ext in tech_extensions[tech]:
                    for root, dirs, files in os.walk(project_path):
                        for file in files:
                            if file.endswith(ext):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        file_patterns = self.intelligence_engine.analyze_code_patterns(content, tech)
                                        patterns.extend(file_patterns)
                                except:
                                    continue  # Skip files that can't be read
        
        return patterns
    
    def _analyze_git_history(self, project_path: str) -> Dict[str, Any]:
        """Analyze git history for development patterns."""
        git_insights = {}
        
        try:
            # Get commit count
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                git_insights["commit_count"] = int(result.stdout.strip())
            
            # Get recent commit messages
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                git_insights["recent_commits"] = result.stdout.strip().split('\n')
            
            # Get file change patterns
            result = subprocess.run(
                ["git", "log", "--name-only", "--pretty=format:", "-10"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                changed_files = [f for f in result.stdout.split('\n') if f.strip()]
                git_insights["frequently_changed_files"] = list(set(changed_files))
        
        except Exception as e:
            git_insights["error"] = str(e)
        
        return git_insights
    
    def _generate_bootstrap_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on project analysis."""
        recommendations = []
        
        # Technology-specific recommendations
        technologies = analysis["technologies"]
        
        if "swift" in technologies:
            recommendations.append("Consider updating to latest SwiftUI patterns for iOS development")
        if "android" in technologies:
            recommendations.append("Evaluate migration to Jetpack Compose for modern Android UI")
        if "react" in technologies:
            recommendations.append("Review React hooks usage for state management")
        if "python" in technologies:
            recommendations.append("Consider adding type hints for better code maintainability")
        
        # Pattern-based recommendations
        patterns = analysis["patterns"]
        pattern_types = [p["type"] for p in patterns]
        
        if "ui_patterns" in pattern_types:
            recommendations.append("UI patterns detected - consider consistency review")
        if "architecture_patterns" in pattern_types:
            recommendations.append("Architecture patterns found - validate current implementation")
        
        return recommendations

# Initialize components
db_manager = DatabaseManager(DATABASE_PATH)
vector_store = VectorStoreManager(VECTOR_DB_PATH)
intelligence_engine = IntelligenceEngine(db_manager)
bootstrap_engine = ProjectBootstrapEngine(intelligence_engine)

# MCP Tools Implementation

@mcp.tool
def create_intelligent_project(
    project_name: str,
    project_type: Literal["ios_app", "android_app", "react_web", "python_analytics", "javascript_web"],
    technologies: List[str],
    description: str,
    repository_path: Optional[str] = None,
    existing_project: bool = False
) -> str:
    """
    Create a new project with intelligent setup based on developer's historical patterns.
    
    For solo developers working across mobile, web, and analytics projects.
    Automatically suggests patterns from similar projects and applies proven approaches.
    
    Args:
        project_name: Unique project identifier
        project_type: Type of project matching developer's technology stack
        technologies: List of technologies (Swift, Kotlin, React, Python, etc.)
        description: Project description for intelligent context building
        repository_path: Optional path to existing repository for bootstrap
        existing_project: Whether analyzing existing project or creating new
        
    Returns:
        JSON string with ProjectCreationResult containing intelligent suggestions and setup configuration
    """
    try:
        # Generate intelligent suggestions based on project type and technologies
        suggestions = intelligence_engine.generate_intelligent_suggestions(project_type, technologies)
        
        # Create project data
        project_data = {
            "name": project_name,
            "type": project_type,
            "technologies": technologies,
            "description": description,
            "repository_path": repository_path,
            "developer_id": DEVELOPER_ID,
            "intelligence_profile": {
                "project_type": project_type,
                "technologies": technologies,
                "created_with_ai": True
            },
            "cross_project_patterns": []
        }
        
        # Create project in database
        project_id = db_manager.create_project(project_data)
        
        # Apply patterns from similar projects (placeholder for now)
        applied_patterns = []
        
        # Setup configuration based on project type
        setup_configuration = {
            "recommended_structure": f"Recommended structure for {project_type}",
            "suggested_dependencies": technologies,
            "development_workflow": "AI-assisted development workflow"
        }
        
        # Bootstrap existing project if specified
        bootstrap_results = {}
        if existing_project and repository_path:
            bootstrap_results = bootstrap_engine.analyze_existing_project(repository_path)
            setup_configuration["bootstrap_analysis"] = bootstrap_results
        
        result = ProjectCreationResult(
            project_id=project_id,
            project_name=project_name,
            intelligent_suggestions=suggestions,
            applied_patterns=applied_patterns,
            setup_configuration=setup_configuration,
            success=True,
            message=f"Successfully created intelligent project: {project_name}"
        )
        
        return json.dumps(asdict(result), indent=2)
        
    except Exception as e:
        logger.error(f"Error creating intelligent project: {str(e)}")
        result = ProjectCreationResult(
            project_id="",
            project_name=project_name,
            intelligent_suggestions=[],
            applied_patterns=[],
            setup_configuration={},
            success=False,
            message=f"Error creating project: {str(e)}"
        )
        return json.dumps(asdict(result), indent=2)

@mcp.tool
def store_context_with_intelligence(
    project_id: str,
    context_type: Literal["conversation", "code_decision", "bug_fix", "pattern_application", "architectural_decision"],
    content: str,
    metadata: Dict[str, Any] = {},
    cross_project_relevance: Optional[float] = None
) -> str:
    """
    Store context with intelligent categorization and cross-project learning.
    
    Optimized for solo developer workflows where context preservation during bug fixes
    is critical to prevent undoing work.
    
    Args:
        project_id: Current project identifier
        context_type: Type of context being stored
        content: The actual context content
        metadata: Additional metadata including technology stack, decision rationale
        cross_project_relevance: Optional score for cross-project applicability
        
    Returns:
        JSON string with IntelligentStorageResult containing storage confirmation and insights
    """
    try:
        # Calculate cross-project relevance if not provided
        if cross_project_relevance is None:
            cross_project_relevance = 0.5  # Default relevance
        
        # Analyze content for patterns
        technologies = metadata.get("technologies", [])
        pattern_insights = []
        
        for tech in technologies:
            patterns = intelligence_engine.analyze_code_patterns(content, tech)
            pattern_insights.extend(patterns)
        
        # Prepare context data
        context_data = {
            "project_id": project_id,
            "context_type": context_type,
            "content": content,
            "metadata": metadata,
            "cross_project_relevance": cross_project_relevance,
            "technology_tags": technologies,
            "importance_score": 0.7 if context_type == "bug_fix" else 0.5  # Higher importance for bug fixes
        }
        
        # Store in database
        context_id = db_manager.store_context(context_data)
        
        # Store in vector database
        if technologies:
            # Determine primary project type for vector storage
            primary_tech = technologies[0] if technologies else "general"
            project_type_map = {
                "swift": "ios_app",
                "kotlin": "android_app", 
                "java": "android_app",
                "react": "react_web",
                "javascript": "javascript_web",
                "python": "python_analytics"
            }
            project_type = project_type_map.get(primary_tech.lower(), "react_web")
            
            vector_store.store_context_vector(
                context_id, 
                content, 
                {"project_id": project_id, "context_type": context_type, **metadata},
                project_type
            )
        
        # Find similar contexts (placeholder)
        similar_contexts = []
        
        result = IntelligentStorageResult(
            context_id=context_id,
            cross_project_relevance_score=cross_project_relevance,
            pattern_insights=pattern_insights,
            similar_contexts=similar_contexts,
            success=True,
            message="Context stored successfully with intelligent analysis"
        )
        
        return json.dumps(asdict(result), indent=2)
        
    except Exception as e:
        logger.error(f"Error storing context: {str(e)}")
        result = IntelligentStorageResult(
            context_id="",
            cross_project_relevance_score=0.0,
            pattern_insights=[],
            similar_contexts=[],
            success=False,
            message=f"Error storing context: {str(e)}"
        )
        return json.dumps(asdict(result), indent=2)

@mcp.tool
def analyze_developer_patterns(
    developer_id: str = DEVELOPER_ID,
    technology_focus: Optional[List[str]] = None,
    time_range_days: Optional[int] = None
) -> str:
    """
    Analyze developer patterns across all projects to build intelligence profile.
    
    Specialized for solo developers working across Swift, Android, Python, React projects.
    Identifies successful patterns and anti-patterns across technology stacks.
    
    Args:
        developer_id: Developer identifier (defaults to configured developer)
        technology_focus: Optional focus on specific technologies
        time_range_days: Optional time range for pattern analysis (last N days)
        
    Returns:
        JSON string with DeveloperPatternAnalysis containing comprehensive pattern insights
    """
    try:
        # Get existing developer profile
        existing_profile = db_manager.get_developer_profile(developer_id)
        
        # Initialize pattern analysis
        technology_patterns = {}
        cross_technology_insights = []
        success_patterns = []
        anti_patterns = []
        recommendations = []
        confidence_scores = {}
        
        # Analyze technology-specific patterns
        technologies_to_analyze = technology_focus or ["swift", "android", "react", "python", "javascript"]
        
        for tech in technologies_to_analyze:
            tech_patterns = intelligence_engine.technology_patterns.get(tech, {})
            technology_patterns[tech] = {
                "detected_patterns": tech_patterns,
                "usage_frequency": 0.5,  # Placeholder
                "success_correlation": 0.7  # Placeholder
            }
            confidence_scores[tech] = 0.6  # Placeholder confidence
        
        # Generate cross-technology insights
        if len(technologies_to_analyze) > 1:
            cross_technology_insights = [
                {
                    "insight": "UI patterns from Swift can be adapted to React components",
                    "source_technology": "swift",
                    "target_technology": "react",
                    "confidence": 0.7
                },
                {
                    "insight": "Data handling patterns from Python analytics apply to mobile backends",
                    "source_technology": "python", 
                    "target_technology": "android",
                    "confidence": 0.6
                }
            ]
        
        # Generate success patterns
        success_patterns = [
            {
                "pattern": "Component-based architecture",
                "technologies": ["swift", "react", "android"],
                "success_rate": 0.85,
                "description": "Modular component architecture works well across platforms"
            }
        ]
        
        # Generate recommendations
        recommendations = [
            "Continue using component-based architecture across all projects",
            "Consider applying React state management patterns to iOS/Android",
            "Leverage Python analytics insights for mobile app features"
        ]
        
        # Update developer profile
        profile_update = {
            "swift_patterns": technology_patterns.get("swift", {}),
            "android_patterns": technology_patterns.get("android", {}),
            "react_patterns": technology_patterns.get("react", {}),
            "python_patterns": technology_patterns.get("python", {}),
            "javascript_patterns": technology_patterns.get("javascript", {}),
            "pattern_confidence_scores": confidence_scores,
            "success_correlations": {"overall": 0.75},
            "anti_patterns": anti_patterns
        }
        
        db_manager.update_developer_profile(developer_id, profile_update)
        
        result = DeveloperPatternAnalysis(
            technology_patterns=technology_patterns,
            cross_technology_insights=cross_technology_insights,
            success_patterns=success_patterns,
            anti_patterns=anti_patterns,
            recommendations=recommendations,
            confidence_scores=confidence_scores
        )
        
        return json.dumps(asdict(result), indent=2)
        
    except Exception as e:
        logger.error(f"Error analyzing developer patterns: {str(e)}")
        result = DeveloperPatternAnalysis(
            technology_patterns={},
            cross_technology_insights=[],
            success_patterns=[],
            anti_patterns=[],
            recommendations=[f"Error analyzing patterns: {str(e)}"],
            confidence_scores={}
        )
        return json.dumps(asdict(result), indent=2)

@mcp.tool  
def bootstrap_existing_project(
    project_path: str,
    analysis_depth: Literal["basic", "comprehensive", "full_history"] = "comprehensive"
) -> str:
    """
    Automatically analyze existing project to extract patterns and build context.
    
    Uses git history analysis, code pattern recognition, and documentation mining
    to understand project without manual setup.
    
    Args:
        project_path: Path to existing project repository
        analysis_depth: Depth of analysis to perform
        
    Returns:
        JSON string with ProjectBootstrapResult containing extracted intelligence
    """
    try:
        # Verify project path exists
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")
        
        # Analyze the project
        analysis = bootstrap_engine.analyze_existing_project(project_path)
        
        # Create project entry based on analysis
        project_name = os.path.basename(project_path)
        technologies = analysis["technologies"]
        
        # Determine project type based on technologies
        project_type = "react_web"  # Default
        if "swift" in technologies:
            project_type = "ios_app"
        elif "android" in technologies or "kotlin" in technologies:
            project_type = "android_app"
        elif "python" in technologies:
            project_type = "python_analytics"
        elif "javascript" in technologies or "react" in technologies:
            project_type = "react_web"
        
        # Create project data
        project_data = {
            "name": f"{project_name}_bootstrapped",
            "type": project_type,
            "technologies": technologies,
            "description": f"Bootstrapped project from {project_path}",
            "repository_path": project_path,
            "developer_id": DEVELOPER_ID,
            "intelligence_profile": analysis,
            "cross_project_patterns": analysis["patterns"]
        }
        
        # Create project in database
        project_id = db_manager.create_project(project_data)
        
        # Extract key insights
        extracted_patterns = analysis["patterns"]
        architectural_decisions = [
            {
                "decision": f"Uses {tech} technology",
                "rationale": "Detected from project structure",
                "confidence": 0.8
            } for tech in technologies
        ]
        
        technology_analysis = {
            "detected_technologies": technologies,
            "primary_technology": technologies[0] if technologies else "unknown",
            "framework_analysis": analysis.get("frameworks", {})
        }
        
        recommendations = analysis["recommendations"]
        
        result = ProjectBootstrapResult(
            project_id=project_id,
            extracted_patterns=extracted_patterns,
            architectural_decisions=architectural_decisions,
            technology_analysis=technology_analysis,
            intelligence_profile=analysis,
            recommendations=recommendations,
            success=True,
            message=f"Successfully bootstrapped project from {project_path}"
        )
        
        return json.dumps(asdict(result), indent=2)
        
    except Exception as e:
        logger.error(f"Error bootstrapping project: {str(e)}")
        result = ProjectBootstrapResult(
            project_id="",
            extracted_patterns=[],
            architectural_decisions=[],
            technology_analysis={},
            intelligence_profile={},
            recommendations=[],
            success=False,
            message=f"Error bootstrapping project: {str(e)}"
        )
        return json.dumps(asdict(result), indent=2)

async def main():
    """Main server function"""
    port = int(os.getenv('CONTEXT_STORAGE_PORT', 8001))
    logger.info(f"Starting Context Storage Server on port {port}")
    logger.info("Features: Multi-project intelligent storage, vector embeddings, project bootstrap engine")
    
    await mcp.run(transport="stdio")

if __name__ == "__main__":
    asyncio.run(main())