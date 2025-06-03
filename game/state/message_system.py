"""
Message system for combat feedback and game notifications.

Handles priority-based message display, message aging, and UI integration.
Extracted from the monolithic GameState class for better testability.
"""
from typing import List, Tuple
import pygame


class MessageSystem:
    """Manages combat messages and notifications with priority-based display."""
    
    def __init__(self, max_messages: int = 10):
        self.messages: List[Tuple[str, int, int]] = []  # (message, priority, age)
        self.max_messages = max_messages
        
    def add_message(self, message: str, priority: int = 0):
        """Add a message with given priority (higher = more important)."""
        self.messages.append((message, priority, 0))
        
        # Keep only the most recent/important messages
        if len(self.messages) > self.max_messages:
            # Sort by priority (desc) then age (asc), keep the best
            self.messages.sort(key=lambda x: (-x[1], x[2]))
            self.messages = self.messages[:self.max_messages]
    
    def update(self, dt: float):
        """Update message ages and remove old messages."""
        # Age all messages
        self.messages = [(msg, priority, age + dt) for msg, priority, age in self.messages]
        
        # Remove messages older than 5 seconds (5000ms)
        self.messages = [(msg, priority, age) for msg, priority, age in self.messages if age < 5000]
    
    def get_recent_messages(self, count: int = 5) -> List[str]:
        """Get the most recent important messages for display."""
        # Sort by priority then by recency
        sorted_messages = sorted(self.messages, key=lambda x: (-x[1], x[2]))
        return [msg for msg, _, _ in sorted_messages[:count]]
    
    def clear_messages(self):
        """Clear all messages."""
        self.messages.clear()
    
    def has_messages(self) -> bool:
        """Check if there are any messages."""
        return len(self.messages) > 0