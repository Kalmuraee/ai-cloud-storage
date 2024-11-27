"""
Event system for handling asynchronous operations
"""
from typing import Any, Callable, Dict, List
from dataclasses import dataclass, field

@dataclass
class EventBus:
    """Simple event bus for handling asynchronous events"""
    subscribers: Dict[str, List[Callable]] = field(default_factory=dict)

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event to all subscribers"""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                await callback(data)

# Global event bus instance
event_bus = EventBus()
