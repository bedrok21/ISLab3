from dataclasses import dataclass
from enum import Enum
from typing import List


@dataclass
class Group:
    name: str
    students_count: int
    subgroups: List[int]


@dataclass
class Subject:
    name: str
    total_hours: int
    lecture_hours: int
    practical_hours: int
    requires_subgroups: bool


@dataclass
class Tutor:
    name: str
    subjects: List[str]
    can_lecture: bool
    can_practice: bool
    hours_per_week: int


@dataclass
class Classroom:
    num: int
    capacity: int


@dataclass
class Semester:
    weeks: int
    max_pairs_per_week: int
    pair_duration_hours: float


class SubjectType(Enum):
    LECTURE = 'LECTURE'
    PRACTICE = 'PRACTICE'


@dataclass
class Lesson:
    name: str
    subject_type: SubjectType
    tutor_name: str
    classroom: int
    groups: list[str]
    subgroup: int | None = None
