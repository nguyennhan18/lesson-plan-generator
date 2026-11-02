"""Public entry points for content generation."""
from .lesson_plan import generate_lesson_plan
from .slides import generate_slide_deck
from .outline import generate_presentation_outline

__all__ = ["generate_lesson_plan", "generate_slide_deck", "generate_presentation_outline"]
