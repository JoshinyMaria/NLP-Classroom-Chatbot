
"""Vedant's 5 Questions & Intent Handlers."""

import re
from typing import Optional, Dict, Any

from classroom_bot.resolver import resolve_subject, find_student


# --------------------------------------------------
# Helper: Retrieve open electives safely
# --------------------------------------------------

def get_open_electives(kb: Dict[str, Any]) -> Dict[str, Any]:
    electives = kb.get("electives", {})

    return (
        electives.get("open", {})
        or kb.get("open", {})
    )


# --------------------------------------------------
# Q3: Class Representatives
# --------------------------------------------------

def handle_cr_info(match: re.Match, kb: Dict[str, Any]) -> str:
    crs = kb.get("leadership", {}).get("cr", [])

    if not crs:
        return "Class representative information is not available."

    lines = ["[Class Representatives (CR)]"]

    for cr in crs:
        lines.append(
            f"  - {cr.get('name', 'Name unavailable')} "
            f"(Roll: {cr.get('roll', 'N/A')}) "
            f"- {cr.get('contact', 'Contact unavailable')}"
        )

    return "\n".join(lines)


# --------------------------------------------------
# Q7: Global Electives
# --------------------------------------------------

def handle_global_electives(match: re.Match, kb: Dict[str, Any]) -> str:
    electives = kb.get("electives", {}).get("global", {})

    if not electives:
        return "Global elective information is not available."

    lines = ["[Offered Global Electives - 6th Semester]"]

    for name, data in electives.items():
        count = data.get("enrolled_count", "Not specified")

        lines.append(
            f"  - {name.title()}: {count} students enrolled"
        )

    return "\n".join(lines)


# --------------------------------------------------
# Q10: Open Elective Enrollment
# --------------------------------------------------

def handle_open_elective_enrollment(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    gd = match.groupdict()

    elective = (gd.get("elective") or "").strip().lower()
    student_query = (gd.get("student_query") or "").strip()

    # 1. Search using student name or registration number

    if student_query:
        students = find_student(student_query, kb)

        if students:
            lines = [
                f"[Open Elective Selection for '{student_query.title()}']"
            ]

            for student in students:
                lines.append(
                    f"  - {student['name']} "
                    f"(Reg No: {student['regno']}) "
                    f"-> {student.get('open_elective', 'Not specified')}"
                )

            return "\n".join(lines)

        return (
            f"Student '{student_query.title()}' "
            "not found in the class records."
        )

    open_electives = get_open_electives(kb)

    if not open_electives:
        return "Open elective enrollment information is not available."

    # 2. Search using elective title

    matched_elective = None

    if elective:
        search_name = elective.lower().strip()

        for name, data in open_electives.items():
            normalized_name = name.lower().strip()

            if (
                search_name == normalized_name
                or search_name in normalized_name
                or normalized_name in search_name
            ):
                matched_elective = (name, data)
                break

    if matched_elective:
        name, data = matched_elective

        student_list = data.get(
            "students",
            data.get("sample_students", [])
        )

        lines = [
            f"[Open Elective Enrollment: {name.title()}]",
            f"Total Enrolled: {data.get('enrolled_count', 'Not specified')} students"
        ]

        if data.get("code"):
            lines.append(f"Course Code: {data['code']}")

        if data.get("faculty"):
            lines.append(f"Faculty In-Charge: {data['faculty']}")

        if student_list:
            lines.append("Enrolled Students:")

            for student in student_list:
                lines.append(f"  - {student}")

        return "\n".join(lines)

    # 3. Display overall enrollment summary

    lines = ["[Open Electives Enrollment Summary - 6BTCS AIML C]"]

    for name, data in open_electives.items():
        count = data.get("enrolled_count", "Not specified")

        lines.append(
            f"  - {name.title()}: {count} students enrolled"
        )

    return "\n".join(lines)


# --------------------------------------------------
# Q11: Honours Program
# --------------------------------------------------

def handle_honours_program(match: re.Match, kb: Dict[str, Any]) -> str:
    honours = kb.get("programs", {}).get("honours", {})

    if not honours:
        return "Honours program information is not available."

    lines = ["[B.Tech Honours Program]"]

    if honours.get("extra_credits") is not None:
        lines.append(
            f"Requirement: {honours['extra_credits']} extra credits"
        )

    if honours.get("duration"):
        lines.append(f"Duration: {honours['duration']}")

    if honours.get("eligibility"):
        lines.append(f"Eligibility: {honours['eligibility']}")

    if honours.get("schedule"):
        lines.append(f"Timetable Slot: {honours['schedule']}")

    if honours.get("enrolled_count") is not None:
        lines.append(
            f"Total Enrolled: {honours['enrolled_count']} students"
        )

    # Display honours tracks

    tracks = honours.get("tracks", {})

    if tracks:
        lines.append("\nHonours Tracks:")

        for track_info in tracks.values():
            title = track_info.get("title", "Honours Track")
            count = track_info.get("count", "Not specified")

            lines.append(f"\n  [{title} - {count} students]")

            course = track_info.get("courses_6th_sem")

            if course:
                if isinstance(course, list):
                    for item in course:
                        lines.append(f"    Course: {item}")
                else:
                    lines.append(f"    Course: {course}")

            students = track_info.get("students", [])

            if students:
                lines.append("    Enrolled Students:")

                for student in students:
                    lines.append(f"      - {student}")

    # Display common sixth-semester courses if available

    courses = honours.get("courses_6th_sem", [])

    if courses:
        lines.append("\n6th Semester Honours Courses:")

        for course in courses:
            lines.append(f"  - {course}")

    if honours.get("registration"):
        lines.append(f"\nRegistration: {honours['registration']}")

    return "\n".join(lines)


# --------------------------------------------------
# Q16: Examination Schedule
# --------------------------------------------------

def handle_exam_schedule(match: re.Match, kb: Dict[str, Any]) -> str:
    exams = kb.get("schedules", {}).get("exam", {})

    if not exams:
        return "Examination schedule is not available."

    lines = ["[Examination Schedule]"]

    if exams.get("end_sem"):
        lines.append(
            f"- End Semester Theory Exams: {exams['end_sem']}"
        )

    if exams.get("practicals"):
        lines.append(
            f"- Practical / Lab Examinations: {exams['practicals']}"
        )

    return "\n".join(lines)


# --------------------------------------------------
# Vedant's Rules
# --------------------------------------------------

VEDANT_RULES = [

    # Q3: Class Representatives
    {
        "id": 3,
        "name": "Class Representative Information Retrieval",
        "member": "Vedant",
        "pattern": (
            r"\b(?:who\s+(?:is|are)\s+(?:our\s+)?)?"
            r"(?:class\s+representatives?|class\s+reps?|cr)\b"
            r"|\bwho\s+represents\s+(?:our\s+)?class\b"
        ),
        "handler": handle_cr_info,
        "description": "Retrieves class representative information."
    },

    # Q7: Global Electives
    {
        "id": 7,
        "name": "Global Elective Information Retrieval",
        "member": "Vedant",
        "pattern": (
            r"\b(?:what\s+are|which|explain|tell\s+me\s+about|"
            r"list|show|available)\s+(?:the\s+)?global\s+electives?\b"
            r"|^\s*(?:the\s+)?global\s+electives?\s*$"
        ),
        "handler": handle_global_electives,
        "description": "Lists available global electives and enrollment counts."
    },

    # Q10: Open Elective Enrollment
    {
        "id": 10,
        "name": "Open Elective Subject and Student Enrollment Retrieval",
        "member": "Vedant",
        "pattern": (
            r"\b(?:"
            # List or show open elective enrollments
            r"(?:(?:list|show)\s+)?open\s+electives?\s+enrollments?"
            r"|"
            # Questions about a particular open elective
            r"(?:enrollment|enrolled(?:\s+in)?|selected|"
            r"who\s+selected|who\s+chose|how\s+many\s+students?"
            r"(?:\s+are)?\s+(?:in|taking|take))"
            r"\s+(?:the\s+)?open\s+electives?"
            r"(?:\s+(?P<elective>[a-zA-Z][a-zA-Z\s]*?))?"
            r"|"
            # Questions about a student's selected elective
            r"(?:which|what)\s+open\s+elective\s+"
            r"(?:did|does|is)\s+"
            r"(?P<student_query>[a-zA-Z\s\d]+?)"
            r"(?:\s+take|\s+choose|\s+enrolled(?:\s+in)?)"
            r")\b"
            r"[?.!]*$"
        ),
        "handler": handle_open_elective_enrollment,
        "description": "Retrieves open elective enrollment and student selections."
    },

    # Q11: Honours Program
    {
        "id": 11,
        "name": "Honours Program Information Retrieval",
        "member": "Vedant",
        "pattern": (
            r"\b(?:what\s+is|how\s+(?:can\s+i\s+)?pursue|"
            r"tell\s+me\s+about|details\s+on|eligibility\s+for|"
            r"list|who\s+(?:is|are)\s+(?:in|taking))?\s*"
            r"(?:the\s+)?(?:honours?|honors?)"
            r"(?:\s+(?:program|courses?|subjects?|students?|list))?\b"
        ),
        "handler": handle_honours_program,
        "description": "Provides information about the honours program and tracks."
    },

    # Q16: Examination Schedule
    {
        "id": 16,
        "name": "Examination Schedule Retrieval",
        "member": "Vedant",
        "pattern": (
            r"\b(?:when\s+(?:are|is)|what\s+is|"
            r"give\s+me|show\s+me|tell\s+me)\s+"
            r"(?:the\s+|our\s+)?(?:next\s+)?"
            r"(?P<exam_type>end\s+sem(?:ester)?|final|"
            r"mid\s+sem(?:ester)?|examination|exam)s?"
            r"(?:\s+(?:schedule|timetable|dates?))?\b"
        ),
        "handler": handle_exam_schedule,
        "description": "Retrieves end-semester and practical examination dates."
    },
]


# --------------------------------------------------
# Rule Matcher
# --------------------------------------------------

def match_vedant_rule(
    query: str,
    kb: Dict[str, Any]
) -> Optional[str]:

    for rule in VEDANT_RULES:
        match = re.search(
            rule["pattern"],
            query,
            re.IGNORECASE
        )

        if match:
            return rule["handler"](match, kb)

    return None
