"""Helpers for resolving subjects, faculty, students and class schedules."""

import re
from typing import Any, Dict, List

from classroom_bot.knowledge_base import KNOWLEDGE_BASE


# Subject keys in knowledge_base.py are lowercase abbreviations.
SUBJECT_ALIASES = {
    "nlp": "nlp",
    "natural language processing": "nlp",
    "dl": "dl",
    "deep learning": "dl",
    "dip": "dip",
    "digital image processing": "dip",
    "pe": "pe",
    "professional elective": "pe",
    "sir": "sir",
    "slp": "slp",
    "speech and language processing": "slp",
    "aec": "aec",
    "ability enhancement course": "aec",
}


def _normalise(value: Any) -> str:
    """Convert text to a lowercase, whitespace-normalised search string."""
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def resolve_subject(query: str) -> str:
    """Return the canonical subject key, or an empty string if not found."""
    q = _normalise(query)
    if not q:
        return ""

    if q in SUBJECT_ALIASES:
        return SUBJECT_ALIASES[q]

    # Use the supplied knowledge base so full subject names also resolve.
    subjects = KNOWLEDGE_BASE.get("subjects", {})
    for key, details in subjects.items():
        key_norm = _normalise(key)
        full_name = _normalise(details.get("full_name", ""))
        code = _normalise(details.get("code", ""))

        if q in {key_norm, full_name, code}:
            return key

    # Allow a query containing a subject name, e.g. "NLP class".
    for key, details in subjects.items():
        candidates = (
            key,
            details.get("full_name", ""),
            details.get("code", ""),
        )
        if any(_normalise(candidate) and _normalise(candidate) in q
               for candidate in candidates):
            return key

    return ""


def find_faculty(query: str, kb: Dict[str, Any]) -> List[Dict[str, str]]:
    """Find faculty by name across subject and leadership records."""
    q = _normalise(query)
    if not q:
        return []

    results: List[Dict[str, str]] = []
    seen = set()

    def add_faculty(name: Any, role: str = "Faculty",
                    location: str = "Faculty Room, GF-B3") -> None:
        name_text = str(name or "").strip()
        name_key = _normalise(name_text)

        if not name_key or name_key in seen:
            return

        if q in name_key or name_key in q:
            results.append({
                "name": name_text,
                "role": role,
                "location": location,
            })
            seen.add(name_key)

    # Faculty listed under subjects.
    for subject in kb.get("subjects", {}).values():
        faculty = subject.get("faculty", "")
        if isinstance(faculty, list):
            for person in faculty:
                add_faculty(person)
        else:
            # Some records may contain multiple names separated by '/'.
            for person in str(faculty).split("/"):
                add_faculty(person.strip())

    # Faculty listed under leadership roles.
    leadership = kb.get("leadership", {})
    for role_key, record in leadership.items():
        if isinstance(record, dict):
            name = record.get("name", "")
            role = record.get("role", role_key.replace("_", " ").title())
            location = (
                record.get("cabin")
                or record.get("location")
                or "Faculty Room, GF-B3"
            )
            add_faculty(name, role, location)

    department = leadership.get("department", {})
    if isinstance(department, dict):
        for role_key in ("hod", "program_coordinator"):
            add_faculty(
                department.get(role_key, ""),
                role_key.replace("_", " ").title(),
            )

    return results


def find_student(query: str, kb: Dict[str, Any]) -> List[Dict[str, str]]:
    """Find students by registration number, name or elective."""
    q = _normalise(query)
    if not q:
        return []

    students = kb.get("students", {})
    results: List[Dict[str, str]] = []

    if isinstance(students, dict):
        records = students.items()
    elif isinstance(students, list):
        records = enumerate(students)
    else:
        return []

    for regno, data in records:
        if not isinstance(data, dict):
            continue

        name = str(data.get("name", "")).strip()
        actual_regno = str(data.get("regno", regno)).strip()
        elective = str(data.get("open_elective", "")).strip()

        searchable = " ".join((name, actual_regno, elective))
        if q in _normalise(searchable):
            results.append({
                "name": name,
                "regno": actual_regno,
                "open_elective": elective or "Not recorded",
            })

    return results


def find_schedule_for_subject(query: str, kb: Dict[str, Any]) -> List[str]:
    """Find schedule entries for a subject from both subject and weekly data."""
    q = _normalise(query)
    if not q:
        return []

    canonical = resolve_subject(query)
    subjects = kb.get("subjects", {})
    results: List[str] = []

    # Subject-specific schedule records, when present.
    if canonical and canonical in subjects:
        schedule = subjects[canonical].get("schedule", [])
        if isinstance(schedule, list):
            results.extend(str(item) for item in schedule if item)
        elif schedule:
            results.append(str(schedule))

    # Weekly timetable entries are stored as strings by weekday.
    timetable = kb.get("schedules", {}).get("timetable", {})
    if isinstance(timetable, dict):
        for day, entry in timetable.items():
            entry_text = str(entry or "")
            if q in _normalise(entry_text) or (
                canonical and canonical in _normalise(entry_text)
            ):
                results.append(f"{str(day).title()}: {entry_text}")

    # Remove duplicates while preserving order.
    unique_results = []
    seen = set()
    for item in results:
        key = _normalise(item)
        if key not in seen:
            unique_results.append(item)
            seen.add(key)

    return unique_results