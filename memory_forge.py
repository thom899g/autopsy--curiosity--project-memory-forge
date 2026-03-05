"""
Project Memory Forge - Robust Memory Management System
Core memory storage, retrieval, and management system with Firebase integration.
Architecture: Uses Firebase Firestore for persistent storage with in-memory caching.
"""

import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from firebase_admin.exceptions import FirebaseError
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("firebase-admin not available. Using local storage only.")

# Standard library imports for fallback
import os
import pickle


class MemoryPriority(Enum):
    """Priority levels for memory storage and retrieval."""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    ARCHIVAL = 0


class MemoryCategory(Enum):
    """Categories for organizing memories."""
    OBSERVATION = "observation"
    DECISION = "decision"
    FAILURE = "failure"
    SUCCESS = "success"
    LEARNED = "learned"
    ENVIRONMENT = "environment"
    SYSTEM = "system"


@dataclass
class MemoryRecord:
    """Data structure for individual memory records."""
    id: str
    content: str
    timestamp: datetime
    priority: MemoryPriority
    category: MemoryCategory
    tags: List[str]
    metadata: Dict[str, Any]
    last_accessed: datetime
    access_count: int
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory record to dictionary for storage."""
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.value,
            'category': self.category.value,
            'tags': self.tags,
            'metadata': self.metadata,
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryRecord':
        """Create memory record from dictionary."""
        return cls(
            id=data['id'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            priority=MemoryPriority(data['priority']),
            category=MemoryCategory(data['category']),
            tags=data['tags'],
            metadata=data['metadata'],
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            access_count=data['access_count'],
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )


class MemoryForge:
    """
    Main memory management system with Firebase integration.
    Handles storage, retrieval, similarity search, and cleanup of memories.
    """
    
    def __init__(self, 
                 firebase_config_path: Optional[str] = None,
                 collection_name: str = "agent_memories",
                 cache_size: int = 1000):
        """
        Initialize