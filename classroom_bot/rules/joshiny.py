
"""Joshiny's 5 Questions & Intent Handlers."""

import re
from typing import Optional, Dict, Any

from classroom_bot.resolver import find_faculty


# --------------------------------------------------
# Q2: Class Teacher / Co-Class Teacher
# --------------------------------------------------

def handle_class_teacher(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    role = (match.groupdict().get("role") or "").lower()
    leadership = kb.get("leadership", {})

    if "co" in role:
        teacher = leadership.get("co_class_teacher", {})
        heading = "Co-Class Teacher"
    else:
        teacher = leadership.get("class_teacher", {})
        heading = "Class Teacher"

    if not teacher:
        return f"{heading} information is not available."

    return (
        f"[{heading}]\n"
        f"Name: {teacher.get('name', 'Not specified')}\n"
        f"Location: {teacher.get('cabin', 'Not specified')}\n"
        f"Email: {teacher.get('email', 'Not specified')}\n"
        f"Phone Ext: {teacher.get('phone_ext', 'Not specified')}"
    )


# --------------------------------------------------
# Q6: Faculty Location and Contact
# --------------------------------------------------

def handle_faculty_location(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    faculty_query = (
        match.groupdict().get("faculty") or ""
    ).strip()

    results = find_faculty(faculty_query, kb)

    if results:
        lines = []

        for faculty in results:
            lines.append(
                f"[Faculty Contact: {faculty.get('name', 'Unknown')}]"
            )

            if faculty.get("role"):
                lines.append(f"  - Role: {faculty['role']}")

            location = (
                faculty.get("location")
                or faculty.get("cabin")
                or "Not specified in the knowledge base"
            )

            lines.append(f"  - Cabin / Location: {location}")

            if faculty.get("email"):
                lines.append(f"  - Email: {faculty['email']}")

            extension = faculty.get("ext") or faculty.get("phone_ext")

            if extension and extension != "N/A":
                lines.append(f"  - Extension: {extension}")

        return "\n".join(lines)

    return (
        f"Faculty '{faculty_query.title()}' not found "
        "in the current faculty directory."
    )


# --------------------------------------------------
# Q9: Global Elective Enrollment
# --------------------------------------------------

def handle_global_elective_enrollment(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    elective = (
        match.groupdict().get("elective") or ""
    ).strip().lower()

    global_electives = (
        kb.get("electives", {}).get("global", {})
    )

    if not global_electives:
        return "Global elective information is not available."

    matched_elective = None

    if elective:
        for name, data in global_electives.items():
            normalized_name = name.lower().strip()

            if (
                elective == normalized_name
                or elective in normalized_name
                or normalized_name in elective
            ):
                matched_elective = (name, data)
                break

    # One particular global elective
    if matched_elective:
        name, data = matched_elective

        lines = [
            f"[Global Elective Enrollment: {name.title()}]",
            f"Total Enrolled: {data.get('enrolled_count', 'Not specified')} students"
        ]

        if data.get("code"):
            lines.append(f"Course Code: {data['code']}")

        if data.get("dept"):
            lines.append(f"Offering Department: {data['dept']}")

        students = data.get(
            "students",
            data.get("sample_students", [])
        )

        if students:
            lines.append("Enrolled Students:")

            for student in students:
                lines.append(f"  - {student}")

        return "\n".join(lines)

    # Overall global elective summary
    lines = ["[Global Electives Enrollment Summary]"]

    for name, data in global_electives.items():
        count = data.get("enrolled_count", "Not specified")

        lines.append(
            f"  - {name.title()}: {count} students enrolled"
        )

    return "\n".join(lines)


# --------------------------------------------------
# Q15: Sports Representatives
# --------------------------------------------------

def handle_sports_cr(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    sports = kb.get("leadership", {}).get("sports_cr", [])

    if not sports:
        return "Sports representative information is not available."

    # The knowledge base stores sports representatives as a list.
    if isinstance(sports, dict):
        sports = [sports]

    lines = ["[Sports Representatives]"]

    for person in sports:
        name = person.get("name", "Name not specified")
        lines.append(f"\nName: {name}")

        roll = person.get("roll") or person.get("regno")

        if roll:
            lines.append(f"Roll: {roll}")

        email = (
            person.get("email")
            or person.get("contact")
        )

        if email:
            lines.append(f"Email: {email}")

        role = person.get("role")

        if role:
            lines.append(f"Role: {role}")

    return "\n".join(lines)


# --------------------------------------------------
# Q20: Department Information
# --------------------------------------------------

def handle_department_info(
    match: re.Match,
    kb: Dict[str, Any]
) -> str:

    title = (
        match.groupdict().get("title") or ""
    ).lower()

    department = (
        kb.get("leadership", {}).get("department", {})
    )

    if "hod" in title or "head" in title:
        value = department.get("hod")

        if value:
            return f"[Head of Department]\n{value}"

        return "Head of Department information is not available."

    if "program" in title:
        value = department.get("program_coordinator")

        if value:
            return f"[Program Coordinator]\n{value}"

        return "Program Coordinator information is not available."

    if "year" in title:
        value = department.get("year_coordinator")

        if value:
            return f"[Year Coordinator]\n{value}"

        return "Year Coordinator information is not available."

    if "office" in title:
        value = department.get("office")

        if value:
            return f"[Department Office]\nLocation: {value}"

        return "Department office location is not specified in the knowledge base."

    return "Department information is not available."


# --------------------------------------------------
# Joshiny's Rules
# --------------------------------------------------

JOSHINY_RULES = [

    # Q2: Class Teacher
    {
        "id": 2,
        "name": "Class Teacher and Co-Class Teacher Identification",
        "member": "Joshiny",
        "pattern": (
            r"\b(?:who\s+(?:is|handles|takes)\s+"
            r"(?:our\s+)?(?:section(?:\s*c)?|class)?\s*)?"
            r"(?P<role>co[- ]class\s+teacher|co[- ]ct|"
            r"class\s+teacher|ct)\b"
            r"|\bwho\s+handles\s+(?:our\s+)?section(?:\s*c)?\b"
        ),
        "handler": handle_class_teacher,
        "description": "Identifies the class teacher or co-class teacher."
    },

    # Q6: Faculty Location
    {
        "id": 6,
        "name": "Faculty Location and Contact Information Retrieval",
        "member": "Joshiny",
        "pattern": (
            r"\b(?:where\s+is|cabin\s+of|contact|reach|find|"
            r"where\s+can\s+i\s+find)\s+"
            r"(?:prof(?:essor)?|dr\.?)?\s*"
            r"(?P<faculty>[a-zA-Z][a-zA-Z\s]*?)"
            r"(?:'s|\s+cabin|\s+contact|\s+office|[?.!]|$)"
        ),
        "handler": handle_faculty_location,
        "description": "Retrieves faculty location and contact information."
    },

    # Q9: Global Elective Enrollment
    {
        "id": 9,
        "name": "Global Elective Subject and Student Enrollment Retrieval",
        "member": "Joshiny",
        "pattern": (
            r"\b(?:"
            r"(?:enrollment|enrolment)(?:\s+in)?"
            r"|(?:who\s+has\s+)?enrolled(?:\s+in)?"
            r"|(?:how\s+many\s+)?students?\s+"
            r"(?:(?:are\s+)?(?:enrolled|taking|in)|take)"
            r")\s+(?:the\s+|this\s+)?global\s+electives?"
            r"(?:\s+(?P<elective>[a-zA-Z][a-zA-Z\s]*?))?"
            r"[?.!]*$"
            r"|"
            r"\bglobal\s+electives?\s+"
            r"(?:enrollment|enrolment|students?)\b"
            r"(?:\s+(?P<elective2>[a-zA-Z][a-zA-Z\s]*?))?"
            r"[?.!]*$"
        ),
        "handler": handle_global_elective_enrollment,
        "description": "Retrieves global elective enrollment counts."
    },

    # Q15: Sports Representatives
    {
        "id": 15,
        "name": "Sports Representative Identification",
        "member": "Joshiny",
        "pattern": (
            r"\b(?:who\s+(?:is|are|handles)\s+(?:our\s+)?)?"
            r"(?:sports\s+(?:representatives?|reps?|cr)|"
            r"sports\s+for\s+our\s+class)\b"
        ),
        "handler": handle_sports_cr,
        "description": "Retrieves the sports representatives."
    },

    # Q20: Department Information
    {
        "id": 20,
        "name": "Department Information Retrieval",
        "member": "Joshiny",
        "pattern": (
            r"\b(?:who\s+is\s+(?:our|the)\s+)?"
            r"(?P<title>hod|head\s+of\s+department|"
            r"program\s+coordinator|year\s+coordinator|"
            r"department\s+office)\b"
        ),
        "handler": handle_department_info,
        "description": "Retrieves department leadership information."
    },
]


# --------------------------------------------------
# Rule Matcher
# --------------------------------------------------

def match_joshiny_rule(
    query: str,
    kb: Dict[str, Any]
) -> Optional[str]:

    for rule in JOSHINY_RULES:
        match = re.search(
            rule["pattern"],
            query.strip(),
            re.IGNORECASE
        )

        if match:
            # Support either named group used for elective title.
            if rule["id"] == 9 and not match.groupdict().get("elective"):
                elective2 = match.groupdict().get("elective2")

                if elective2:
                    match = re.match(
                        r"(?P<elective>.*)",
                        elective2
                    )

            return rule["handler"](match, kb)

    return None
