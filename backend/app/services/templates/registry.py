from typing import Dict, Type
from .base import BaseTemplate

class TemplateRegistry:
    _instance = None
    _templates: Dict[str, Type[BaseTemplate]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TemplateRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str, template_cls: Type[BaseTemplate]):
        """Register a new template class."""
        cls._templates[name.lower()] = template_cls

    @classmethod
    def get(cls, name: str) -> BaseTemplate:
        """Get a template instance by name. Defaults to 'generic' if not found."""
        template_cls = cls._templates.get(name.lower(), cls._templates.get("generic"))
        if not template_cls:
             # Fallback if generic isn't registered yet (bootstrapping issue usually avoided by imports)
             raise ValueError(f"Template '{name}' not found and no generic fallback available.")
        return template_cls()
