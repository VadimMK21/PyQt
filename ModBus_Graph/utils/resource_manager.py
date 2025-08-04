from typing import List, Callable
import logging

logger = logging.getLogger(__name__)

class ResourceManager:
    """
    Manager for handling application resources and cleanup
    """
    def __init__(self):
        self._resources: List[tuple] = []  # List of (resource, cleanup_func)
        
    def register(self, resource: object, cleanup_func: Callable) -> None:
        """
        Register a resource and its cleanup function
        """
        self._resources.append((resource, cleanup_func))
        
    def cleanup(self) -> None:
        """
        Clean up all registered resources
        """
        while self._resources:
            resource, cleanup_func = self._resources.pop()
            try:
                cleanup_func(resource)
            except Exception as e:
                logger.error(f"Error cleaning up resource {resource}: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()