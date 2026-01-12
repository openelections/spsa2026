#!/usr/bin/env python3
"""
Parse SPSA 2026 conference program into structured JSON files by day.
"""

import re
import json
from collections import defaultdict
from typing import Dict, List, Any


def parse_person(text: str) -> Dict[str, str]:
    """
    Parse a person's name and affiliation from text.
    Format: "Name, Affiliation" or just "Name"
    """
    if not text or text.strip() == "":
        return {"name": "", "affiliation": ""}

    text = text.strip()

    # Check if there's a comma separating name and affiliation
    if ',' in text:
        parts = text.split(',', 1)
        return {
            "name": parts[0].strip(),
            "affiliation": parts[1].strip() if len(parts) > 1 else ""
        }
    else:
        return {
            "name": text,
            "affiliation": ""
        }


def parse_time(time_str: str) -> tuple:
    """Parse time range like '8:00am-9:15am' into start and end times."""
    if not time_str or '-' not in time_str:
        return "", ""

    parts = time_str.split('-')
    return parts[0].strip(), parts[1].strip()


def parse_day_from_text(day_text: str) -> str:
    """Extract day name from text like 'Thursday'."""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in days:
        if day in day_text:
            return day
    return ""


def get_indent_level(line: str) -> int:
    """Return the number of leading spaces in a line."""
    return len(line) - len(line.lstrip())


def parse_sessions(filename: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parse the conference program file and return sessions organized by day.

    Format:
    SESSION_ID    SESSION_TITLE
       DAY        TOPIC
    TIME
    ROOM - BUILDING
                  Chair
                      Name, Affiliation
                  Participants
                      Paper Title
                          Author, Affiliation
                          Author, Affiliation
                      Paper Title
                          Author, Affiliation
                  Discussant
                      Name, Affiliation
    """
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    sessions_by_day = defaultdict(list)

    i = 0
    while i < len(lines):
        # Look for lines with session ID pattern (4 digits) on the left
        # The line format is: "     2100            Session Title"
        match = re.match(r'^(\s{0,10})(\d{4})(\s+)(.*)$', lines[i])

        if match and match.group(2) not in ['1100', '1400', '2900']:
            session_id = match.group(2)
            session_title = match.group(4).strip()

            # Start collecting session data
            session = {
                "session_id": session_id,
                "day": "",
                "start_time": "",
                "end_time": "",
                "room": "",
                "building": "",
                "topic": "",
                "session_title": session_title,
                "chair": {},
                "participants": [],
                "discussants": []
            }

            i += 1

            # Next line has day and topic
            if i < len(lines):
                # Format: "        Thursday     Undergraduate Research"
                day_topic_line = lines[i]
                # Extract day
                session["day"] = parse_day_from_text(day_topic_line)
                # Extract topic (everything after day)
                if session["day"]:
                    parts = day_topic_line.split(session["day"], 1)
                    if len(parts) > 1:
                        session["topic"] = parts[1].strip()
                i += 1

            # Next line has time
            if i < len(lines):
                time_line = lines[i].strip()
                start, end = parse_time(time_line)
                session["start_time"] = start
                session["end_time"] = end
                i += 1

            # Next line has room and building
            chair_on_room_line = False
            if i < len(lines):
                room_building = lines[i]
                # Extract room and building - look for dash separator
                if ' - ' in room_building or '-' in room_building:
                    # Split on first dash
                    dash_pos = room_building.find('-')
                    room_part = room_building[:dash_pos].strip()
                    building_part = room_building[dash_pos+1:].strip()

                    session["room"] = room_part

                    # Building might have extra text like "Chair" on same line
                    # Extract just the building portion
                    if 'Chair' in building_part:
                        session["building"] = building_part.split('Chair')[0].strip()
                        chair_on_room_line = True
                    elif 'Floor' in building_part:
                        # Get everything up to and including "Floor"
                        floor_match = re.search(r'^(.*?Floor)', building_part)
                        if floor_match:
                            session["building"] = floor_match.group(1).strip()
                        else:
                            session["building"] = building_part.strip()
                    else:
                        session["building"] = building_part.strip()
                else:
                    # No dash, just room
                    session["room"] = room_building.split('Chair')[0].strip()
                    if 'Chair' in room_building:
                        chair_on_room_line = True

                i += 1

            # If Chair was on the room line, next line might have chair info
            if chair_on_room_line and i < len(lines):
                next_line = lines[i]
                # Check if this line has "Building" or "Floor" followed by chair info
                if 'Building' in next_line or 'Floor' in next_line:
                    # Extract everything after "Building" or "Floor"
                    building_match = re.search(r'(?:Building|Floor)\s+(.+)', next_line)
                    if building_match:
                        chair_info = building_match.group(1).strip()
                        if chair_info and not chair_info.startswith('Participants'):
                            session["chair"] = parse_person(chair_info)
                    i += 1
                else:
                    # Next line might just be the chair name directly (heavily indented)
                    stripped_next = next_line.strip()
                    if stripped_next and not stripped_next in ['Chair', 'Participants', 'Discussant', 'Discussants']:
                        # Check if it looks like a name (has comma for affiliation or starts with capital)
                        if ',' in stripped_next or stripped_next[0].isupper():
                            session["chair"] = parse_person(stripped_next)
                            i += 1

            # Now parse Chair, Participants, and Discussants sections
            current_section = None
            current_paper_title = None
            current_paper_authors = []

            while i < len(lines):
                line = lines[i]
                stripped = line.strip()

                # Check if we've hit the next session (starts with session ID)
                if re.match(r'^(\s{0,10})(\d{4})(\s+)', line):
                    # Before breaking, add any pending paper
                    if current_paper_title and current_section == 'participants':
                        session["participants"].append({
                            "paper_title": current_paper_title,
                            "authors": current_paper_authors
                        })
                    break

                # Check for empty line
                if not stripped:
                    i += 1
                    continue

                # Check for section headers
                # Sometimes Chair appears standalone (when not caught earlier)
                if stripped == 'Chair' and not session["chair"]:
                    current_section = 'chair'
                    # Add any pending paper before switching sections
                    if current_paper_title and current_section == 'participants':
                        session["participants"].append({
                            "paper_title": current_paper_title,
                            "authors": current_paper_authors
                        })
                        current_paper_title = None
                        current_paper_authors = []
                    current_section = 'chair'
                    i += 1
                    continue
                elif stripped == 'Participants':
                    if current_paper_title:
                        session["participants"].append({
                            "paper_title": current_paper_title,
                            "authors": current_paper_authors
                        })
                        current_paper_title = None
                        current_paper_authors = []
                    current_section = 'participants'
                    i += 1
                    continue
                elif stripped in ['Discussant', 'Discussants']:
                    # Add any pending paper before switching sections
                    if current_paper_title:
                        session["participants"].append({
                            "paper_title": current_paper_title,
                            "authors": current_paper_authors
                        })
                        current_paper_title = None
                        current_paper_authors = []
                    current_section = 'discussants'
                    i += 1
                    continue

                # Parse content based on current section
                if current_section:
                    indent = get_indent_level(line)

                    if current_section == 'chair':
                        # Chair is just a name and affiliation
                        if stripped and not session["chair"]:
                            session["chair"] = parse_person(stripped)

                    elif current_section == 'participants':
                        # Less indented = paper title, more indented = author
                        # Typically paper titles are around 20 spaces, authors around 25+
                        if indent < 25 and stripped:
                            # This is likely a paper title
                            # Save previous paper if exists
                            if current_paper_title:
                                session["participants"].append({
                                    "paper_title": current_paper_title,
                                    "authors": current_paper_authors
                                })
                            current_paper_title = stripped
                            current_paper_authors = []
                        elif indent >= 25 and stripped:
                            # Check if this looks like a continuation of the paper title
                            # (doesn't have a comma, which most author lines do)
                            if current_paper_title and ',' not in stripped and len(current_paper_authors) == 0:
                                # Likely a continuation of the paper title
                                current_paper_title += " " + stripped
                            else:
                                # This is an author
                                current_paper_authors.append(parse_person(stripped))

                    elif current_section == 'discussants':
                        # Discussants are just names and affiliations
                        # Skip if it's just a number (likely a session ID)
                        # Skip if it looks like descriptive text (starts with lowercase or contains sentence-like structures)
                        if stripped and not re.match(r'^\d{4}$', stripped):
                            # Check if this looks like a panel description rather than a person
                            # Panel descriptions typically start with lowercase or have lots of connecting words
                            if stripped[0].isupper() and ',' in stripped:
                                # Likely a name with affiliation
                                session["discussants"].append(parse_person(stripped))
                            elif stripped[0].isupper() and not any(word in stripped.lower() for word in ['this panel', 'the panel', 'a panel', 'explores', 'discusses', 'focuses']):
                                # Might be a name without affiliation
                                session["discussants"].append(parse_person(stripped))

                i += 1

            # Add any remaining paper
            if current_paper_title and current_section == 'participants':
                session["participants"].append({
                    "paper_title": current_paper_title,
                    "authors": current_paper_authors
                })

            # Add session to appropriate day
            if session["day"]:
                sessions_by_day[session["day"]].append(session)
        else:
            i += 1

    return sessions_by_day


def main():
    """Main function to parse and save sessions."""
    input_file = '2026spsaprogramv7.0-1.txt'

    print(f"Parsing conference program from {input_file}...")
    sessions_by_day = parse_sessions(input_file)

    # Save each day to a separate JSON file
    for day, sessions in sessions_by_day.items():
        output_file = f"sessions_{day.lower()}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(sessions)} sessions for {day} to {output_file}")

    print("\nDone!")


if __name__ == '__main__':
    main()
