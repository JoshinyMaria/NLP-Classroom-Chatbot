
"""Sasmita's 5 Questions & Intent Handlers."""

import re
from typing import Optional, Dict, Any

from classroom_bot.resolver import resolve_subject, find_schedule_for_subject


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def get_open_electives(kb: Dict[str, Any]) -> Dict[str, Any]:
    return (
        kb.get("electives", {}).get("open", {})
        or kb.get("open", {})
    )


def format_day_schedule(day_name: str, raw_sched: str) -> str:
    periods = [p.strip() for p in raw_sched.split("|") if p.strip()]
    lines = [
        f"[Timetable for {day_name.capitalize()} - 6 B.Tech CS AIML-C]"
    ]

    for period in periods:
        match = re.match(
            r"^(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})\s*(.*)$",
            period
        )

        if match:
            time_slot, description = match.groups()
            lines.append(f"  - {time_slot} : {description.strip()}")
        else:
            lines.append(f"  - {period}")

    return "\n".join(lines)


# --------------------------------------------------
# Q1: Classroom Location
# --------------------------------------------------

def handle_classroom_location(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    info = kb.get("class_info", {})

    return (
        "[Classroom Location]\n"
        f"Class: {info.get('section', 'Not specified')}\n"
        f"Room: {info.get('room', 'Not specified')}\n"
        f"Floor: {info.get('floor', 'Not specified')}\n"
        f"Block: {info.get('block', 'Not specified')}\n"
        f"Department: {info.get('department', 'Not specified')}"
    )


# --------------------------------------------------
# Q5: Timetable
# --------------------------------------------------

def handle_timetable(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    gd = match.groupdict()

    sched_subj = (gd.get("sched_subj") or "").strip()
    day = gd.get("day_pre") or gd.get("day_post") or gd.get("day")

    timetable = kb.get("schedules", {}).get("timetable", {})

    # Subject-specific timetable
    if sched_subj:
        slots = find_schedule_for_subject(sched_subj, kb)
        canon = resolve_subject(sched_subj)

        if canon and canon in kb.get("subjects", {}):
            subject_name = kb["subjects"][canon].get(
                "full_name", sched_subj
            )
        else:
            subject_name = sched_subj.title()

        if slots:
            lines = [f"[Class Schedule for {subject_name}]"]

            for slot in slots:
                lines.append(f"  - {slot}")

            return "\n".join(lines)

        return (
            f"Could not find scheduled slots for "
            f"'{sched_subj.title()}'. "
            "Type 'timetable' to see the full schedule."
        )

    # Day-specific timetable
    if day:
        day_key = day.lower()

        if day_key == "today":
            return (
                "Please specify the weekday to retrieve "
                "the correct timetable."
            )

        if day_key in timetable:
            return format_day_schedule(day_key, timetable[day_key])

        return f"No classes scheduled for {day_key.capitalize()}."

    # Complete weekly timetable
    if not timetable:
        return "Timetable information is not available."

    lines = ["[Weekly Timetable for 6 B.Tech CS AIML-C]"]

    for day_name, raw_schedule in timetable.items():
        lines.append(f"\n{day_name.capitalize()}:")

        periods = [
            p.strip()
            for p in raw_schedule.split("|")
            if p.strip()
        ]

        for period in periods:
            period_match = re.match(
                r"^(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})\s*(.*)$",
                period
            )

            if period_match:
                time_slot, description = period_match.groups()
                lines.append(
                    f"  - {time_slot} : {description.strip()}"
                )
            else:
                lines.append(f"  - {period}")

    return "\n".join(lines)


# --------------------------------------------------
# Q8: Open Electives
# --------------------------------------------------

def handle_open_electives(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    electives = get_open_electives(kb)

    if not electives:
        return "Open elective information is not available."

    lines = ["[Available Open Electives - 6th Semester]"]

    for name, data in electives.items():
        count = data.get("enrolled_count", "Not specified")

        lines.append(f"  - {name.title()}")

        if data.get("code"):
            lines.append(f"      Course Code: {data['code']}")

        if data.get("faculty"):
            lines.append(f"      Faculty: {data['faculty']}")

        lines.append(f"      Students Enrolled: {count}")

        if data.get("credits") is not None:
            lines.append(f"      Credits: {data['credits']}")

    return "\n".join(lines)


# --------------------------------------------------
# Q14: CIA Schedule
# --------------------------------------------------

def handle_cia_schedule(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    cia_num = match.groupdict().get("cia_num")
    cias = kb.get("schedules", {}).get("cia", {})

    if not cias:
        return "CIA schedule information is not available."

    if cia_num and cia_num in cias:
        return f"[CIA {cia_num} Schedule]\n{cias[cia_num]}"

    lines = ["[Continuous Internal Assessment (CIA) Schedule]"]

    for number, details in cias.items():
        lines.append(f"  - CIA {number}: {details}")

    return "\n".join(lines)


# --------------------------------------------------
# Q17: Subject Syllabus
# --------------------------------------------------

def handle_syllabus(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    raw_subject = (match.groupdict().get("subject") or "").strip()
    unit = match.groupdict().get("unit")

    subjects = kb.get("subjects", {})
    canon = resolve_subject(raw_subject)

    # Check actual subjects first
    if canon and canon in subjects:
        subject_data = subjects[canon]
        units = subject_data.get("units", [])

        if unit:
            unit_index = int(unit) - 1

            if 0 <= unit_index < len(units):
                return (
                    f"[{subject_data.get('full_name', canon)} "
                    f"({canon.upper()}) - Unit {unit}]\n"
                    f"{units[unit_index]}"
                )

            return (
                f"Unit {unit} does not exist for {canon.upper()}. "
                f"Total units: {len(units)}."
            )

        lines = [
            f"[Syllabus: {subject_data.get('full_name', canon)} "
            f"({canon.upper()})]"
        ]

        for index, unit_content in enumerate(units, start=1):
            lines.append(f"  - Unit {index}: {unit_content}")

        return "\n".join(lines)

    # Check open electives without assuming their location
    open_electives = get_open_electives(kb)
    search_name = raw_subject.lower()

    for elective_name, elective_data in open_electives.items():
        if search_name == elective_name.lower():
            lines = [f"[Open Elective: {elective_name.title()}]"]

            if elective_data.get("code"):
                lines.append(f"Course Code: {elective_data['code']}")

            if elective_data.get("faculty"):
                lines.append(f"Faculty: {elective_data['faculty']}")

            if elective_data.get("credits") is not None:
                lines.append(f"Credits: {elective_data['credits']}")

            return "\n".join(lines)

    # Do not create an AI subject or map it to DL
    available = ", ".join(
        subject.upper() for subject in subjects.keys()
    )

    return (
        f"Subject '{raw_subject.upper()}' not found. "
        f"Available subjects: {available}."
    )


# --------------------------------------------------
# Sasmita's Rules
# --------------------------------------------------

SASMITA_RULES = [

    {
        "id": 1,
        "name": "Classroom Location Retrieval",
        "member": "Sasmita",
        "pattern": (
            r"\b(?:where\s+(?:is|are|do\s+we\s+have)\s+"
            r"(?:our\s+)?(?:classroom|class\s*room|class|"
            r"section\s*c|lectures?)|which\s+room|what\s+room|"
            r"class\s+location|classroom|class\s*room)\b"
        ),
        "handler": handle_classroom_location,
        "description": "Retrieves the classroom location."
    },

    {
        "id": 14,
        "name": "CIA Schedule Information Retrieval",
        "member": "Sasmita",
        "pattern": (
            r"\b(?:when\s+(?:are|is)|what\s+is)?\s*"
            r"(?:the\s*)?cias?\s*(?P<cia_num>[1-3])?"
            r"\s*(?:schedule|dates?|exam)?\b"
        ),
        "handler": handle_cia_schedule,
        "description": "Retrieves CIA examination dates."
    },

    {
        "id": 17,
        "name": "Subject Syllabus Retrieval",
        "member": "Sasmita",
        "pattern": (
            r"\b(?:what\s+are\s+)?(?:the\s+)?"
            r"(?:units?|syllabus)"
            r"(?:\s+(?P<unit>\d+))?"
            r"\s+(?:of|for|in)\s+"
            r"(?P<subject>[a-zA-Z][a-zA-Z0-9\s&-]*?)"
            r"(?:\s+syllabus)?[?.!]*$"
        ),
        "handler": handle_syllabus,
        "description": "Retrieves a subject syllabus or a specific unit."
    },

    {
        "id": 8,
        "name": "Open Elective Information Retrieval",
        "member": "Sasmita",
        "pattern": (
            r"\b(?:what\s+are|which|explain|tell\s+me\s+about|"
            r"list|show|available)\s+(?:the\s+)?open\s+electives?\b"
            r"|^\s*(?:the\s+)?open\s+electives?\s*[?.!]*$"
        ),
        "handler": handle_open_electives,
        "description": "Lists available open electives."
    },

    {
        "id": 5,
        "name": "Class Timetable Retrieval",
        "member": "Sasmita",
        "pattern": (
            r"\bwhen\s+(?:do\s+we\s+have|is|are)\s+"
            r"(?P<sched_subj>[a-zA-Z][a-zA-Z\s&-]*?)"
            r"(?:\s+(?:class|lecture))?[?.!]*$"
            r"|"
            r"\b(?P<day_pre>monday|tuesday|wednesday|"
            r"thursday|friday|saturday|today)\s+"
            r"(?:timetable|schedule|routine)\b"
            r"|"
            r"\b(?:(?:daywise|day\s+wise|weekly|class)\s+)?"
            r"(?:timetable|schedule|routine)"
            r"(?:\s+(?:for|on)?\s*"
            r"(?P<day_post>monday|tuesday|wednesday|"
            r"thursday|friday|saturday|today))?\b"
        ),
        "handler": handle_timetable,
        "description": "Retrieves subject-wise, day-wise or weekly timetable."
    },
]


# --------------------------------------------------
# Rule Matcher
# --------------------------------------------------

def match_sasmita_rule(
    query: str,
    kb: Dict[str, Any]
) -> Optional[str]:

    for rule in SASMITA_RULES:
        match = re.search(
            rule["pattern"],
            query.strip(),
            re.IGNORECASE
        )

        if match:
            return rule["handler"](match, kb)

    return None
