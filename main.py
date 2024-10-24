import yaml
from collections import defaultdict
from models import Group, Subject, Tutor, Classroom, SubjectType, Lesson


def load_config(path):
    with open(path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        return data


class InitData:
    def __init__(self) -> None:
        self.groups: dict[str, Group] = {}
        self.subjects: dict[str, list[Subject]] = defaultdict(list)
        self.tutors: dict[str, Tutor] = {}
        self.classrooms: dict[int, Classroom] = {}

    def load_data(self, path: str = 'config.yaml'):
        data = load_config(path)
        for group_name, group_par in data['groups'].items():
            self.groups[group_name] = Group(group_name, **group_par)
        for group_name, subjects in data['subjects'].items():
            for subject in subjects:
                self.subjects[group_name].append(Subject(**subject))
        for tutor_name, tutor_par in data['tutors'].items():
            self.tutors[tutor_name] = Tutor(tutor_name, **tutor_par)
        for classroom_par in data['classrooms']:
            self.classrooms[classroom_par['num']] = Classroom(**classroom_par)

    def get_tutors_by_subject(self, subject, subject_type: SubjectType):
        tutor_names = []
        for tutor_name, tutor in self.tutors.items():
            if subject in tutor.subjects \
                and (tutor.can_lecture or subject_type == SubjectType.PRACTICE) \
                    and (tutor.can_practice or subject_type == SubjectType.LECTURE):
                tutor_names.append(tutor_name)
        return tutor_names


class Timetable:
    def __init__(self, init_data) -> None:
        self.init_data: InitData = init_data
        self.timetable: list[dict[str, list[list[Lesson]]]]

    def validate_restrictions(self):
        for slot in self.timetable:
            busy_tutors = set()
            busy_classrooms = set()
            for parity in [0, 1]:
                for group_name, lessons in slot.items():
                    if not lessons:
                        continue
                    assert len(lessons) <= 2
                    local_parity = parity if len(lessons) == 2 else 0
                    assert len(lessons[local_parity]) <= 2
                    for lesson in lessons[local_parity]:
                        assert not (not lesson.subgroup and len(lessons[local_parity]) > 1)
                        assert not (lesson.subgroup and len(lesson.groups) > 1)
                        if len(lesson.groups) == 1:
                            assert lesson.tutor_name not in busy_tutors
                            assert lesson.classroom not in busy_classrooms
                            assert self.init_data.classrooms[lesson.classroom].capacity\
                                >= self.init_data.groups[lesson.groups[0]].students_count
                        else:
                            total_students_num = 0
                            for group in lesson.groups:
                                assert slot[group][local_parity][0].classroom == lesson.classroom
                                assert slot[group][local_parity][0].tutor_name == lesson.tutor_name
                                assert slot[group][local_parity][0].groups == lesson.groups
                                assert slot[group][local_parity][0].name == lesson.name
                                total_students_num += self.init_data.groups[group].students_count
                            assert self.init_data.classrooms[lesson.classroom].capacity >= total_students_num
                            if group_name == next((group for group, value in slot.items()
                                                   if value[local_parity][0].name in lesson.groups), None):
                                assert lesson.tutor_name not in busy_tutors
                                assert lesson.classroom not in busy_classrooms

                        busy_tutors.add(lesson.tutor_name)
                        busy_classrooms.add(lesson.classroom)

    def validate_requirements(self):
        pass

    def validate_timetable(self):
        self.validate_restrictions()
        self.validate_requirements()

def main():
    data = InitData()
    data.load_data()
    print(data.tutors)


if __name__ == '__main__':
    main()
