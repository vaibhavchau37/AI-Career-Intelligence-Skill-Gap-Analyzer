"""Learning resources catalog.

Provides clickable resources for skills from:
- Coursera
- Udemy
- YouTube

Where a stable direct course URL is known, we provide it.
Otherwise, we provide platform search URLs (still a direct learning action).
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class ResourceLink:
    platform: str
    title: str
    url: str


def _coursera_search(skill: str) -> ResourceLink:
    q = quote_plus(skill)
    return ResourceLink("Coursera", f"Search '{skill}' on Coursera", f"https://www.coursera.org/search?query={q}")


def _udemy_search(skill: str) -> ResourceLink:
    q = quote_plus(skill)
    return ResourceLink("Udemy", f"Search '{skill}' on Udemy", f"https://www.udemy.com/courses/search/?q={q}")


def _youtube_search(skill: str) -> ResourceLink:
    q = quote_plus(skill)
    return ResourceLink("YouTube", f"Search '{skill}' tutorials on YouTube", f"https://www.youtube.com/results?search_query={q}")


# Curated, stable-ish links for common skills.
# Keep this list short and high-signal.
_CURATED: dict[str, list[ResourceLink]] = {
    "tensorflow": [
        ResourceLink(
            "Coursera",
            "TensorFlow in Practice Specialization (deeplearning.ai)",
            "https://www.coursera.org/specializations/tensorflow-in-practice",
        ),
        ResourceLink(
            "YouTube",
            "TensorFlow Official YouTube Channel",
            "https://www.youtube.com/@TensorFlow",
        ),
        ResourceLink(
            "Udemy",
            "Udemy TensorFlow courses (search)",
            "https://www.udemy.com/courses/search/?q=tensorflow",
        ),
    ],
    "sql": [
        ResourceLink(
            "Coursera",
            "SQL for Data Science (UC Davis)",
            "https://www.coursera.org/learn/sql-for-data-science",
        ),
        ResourceLink(
            "YouTube",
            "SQL tutorial (YouTube search)",
            "https://www.youtube.com/results?search_query=sql+tutorial",
        ),
        ResourceLink(
            "Udemy",
            "Udemy SQL courses (search)",
            "https://www.udemy.com/courses/search/?q=sql",
        ),
    ],
    "python": [
        ResourceLink(
            "Coursera",
            "Python for Everybody (University of Michigan)",
            "https://www.coursera.org/specializations/python",
        ),
        ResourceLink(
            "YouTube",
            "Python tutorial (YouTube search)",
            "https://www.youtube.com/results?search_query=python+tutorial",
        ),
        ResourceLink(
            "Udemy",
            "Udemy Python courses (search)",
            "https://www.udemy.com/courses/search/?q=python",
        ),
    ],
}


def get_resource_links(skill: str) -> list[ResourceLink]:
    """Return resource links for a skill.

    Always includes Coursera/Udemy/YouTube options.
    """
    key = (skill or "").strip().lower()
    curated = _CURATED.get(key)
    if curated:
        return curated

    # Default to platform searches (real, not fake, works for any skill)
    return [_coursera_search(skill), _udemy_search(skill), _youtube_search(skill)]
