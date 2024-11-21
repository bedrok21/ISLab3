import random
import pandas as pd
from tabulate import tabulate
import warnings
from collections import defaultdict
warnings.filterwarnings("ignore")


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = 4
WEEKS = 2
POPULATION_SIZE = 20
MAX_ITERATIONS = 10
MUTATION_RATE = 1
GROUP_NUM = 4


def generate_data():
    subjects = [{"name": f"Subject {i}", "hours": random.randint(3, 4), "is_divided": random.choice([True, False])} for i in range(1, 10)]
    groups = [
        {
            "name": f"Group {i}",
            "students": random.randint(20, 30),
            "program": random.sample(subjects, k=random.randint(3, 4))
        }
        for i in range(1, GROUP_NUM + 1)
    ]
    lecturers = [{"name": f"Lecturer {i}", "subjects": random.sample([s["name"] for s in subjects], k=4)} for i in range(1, 7)]
    rooms = [{"name": f"Room {i}", "capacity": random.randint(40, 50)} for i in range(1, 7)]
    return groups, subjects, lecturers, rooms


groups, subjects, lecturers, rooms = generate_data()
# print(f"{groups}\n\n{subjects}\n\n{lecturers}\n\n{rooms}")


def is_valid_schedule(schedule):
    g = 0
    l = 0
    r = 0
    res = True
    used_slots = {}
    for idx, entry in enumerate(schedule):
        key_group = (entry["group"], entry["week"], entry["day"], entry["time_slot"])
        key_lecturer = (entry["lecturer"], entry["week"], entry["day"], entry["time_slot"])
        key_room = (entry["room"], entry["week"], entry["day"], entry["time_slot"])

        if key_group in used_slots:
            g -= 1
            # return False, idx
        if key_lecturer in used_slots:
            l -= 1
            # return False, idx
        if key_room in used_slots:
            r -= 1
            # return False, idx

        group = next(g for g in groups if g["name"] == entry["group"])
        room = next(r for r in rooms if r["name"] == entry["room"])
        if group["students"] > room["capacity"]:
            return False, idx

        used_slots[key_group] = True
        used_slots[key_lecturer] = True
        used_slots[key_room] = True
    if g < 0 or l < 0 or r < 0:
        res = False
    return res, g, l, r


def initialize_population():
    population = []
    while len(population) < POPULATION_SIZE:
        schedule = []
        for group in groups:
            for subject in group["program"]:
                total_hours = subject["hours"] // 1
                for _ in range(total_hours):
                    week = random.randint(0, WEEKS - 1)
                    day = random.choice(DAYS)
                    time_slot = random.randint(0, TIME_SLOTS - 1)
                    schedule.append({
                        "group": group["name"],
                        "subject": subject["name"],
                        "lecturer": random.choice(lecturers)["name"],
                        "room": random.choice(rooms)["name"],
                        "day": day,
                        "time_slot": time_slot,
                        "week": week
                    })
        population.append(schedule)
    return population


def fitness(schedule):
    _, g, l, r = is_valid_schedule(schedule)
    return g + l + r


def selection(population):
    population.sort(key=fitness, reverse=True)
    return population[:POPULATION_SIZE // 2]


def crossover(parent1, parent2):
    child = []
    for idx, paren1_gen in enumerate(parent1):
        if random.random() > 0.5:
            child.append(paren1_gen)
        else:
            child.append(parent2[idx])
    child.sort(key=lambda x: (x["group"], x["week"], x["day"], x["time_slot"]))
    return child


def get_empty_slots_for_group(schedule, group_name):
    all_slots = set()
    busy_slots = set()

    for entry in schedule:
        day = entry['day']
        time_slot = entry['time_slot']
        all_slots.add((day, time_slot))
        if entry.get(group_name):
            busy_slots.add((day, time_slot))
    free_slots = all_slots - busy_slots
    return list(free_slots)


def find_empty_rooms(schedule, day, time_slot):
    all_rooms = set()
    occupied_rooms = set()
    for entry in schedule:
        all_rooms.add(entry['room'])
        if entry['day'] == day and entry['time_slot'] == time_slot and entry.get('room'):
            occupied_rooms.add(entry['room'])
    empty_rooms = all_rooms - occupied_rooms
    return list(empty_rooms)


def find_free_lecturers(schedule, day, time_slot, subject):
    all_lecturers = set()
    occupied_lecturers = set()
    for entry in schedule:
        for lecturer in lecturers:
            if lecturer['name'] == entry['lecturer'] and subject in lecturer['subjects']:
                all_lecturers.add(entry['lecturer'])
                break
        if entry['day'] == day and entry['time_slot'] == time_slot:
            occupied_lecturers.add(entry['lecturer'])
    free_lecturers = all_lecturers - occupied_lecturers
    return list(free_lecturers)


def find_group_entries_with_shared_slot(schedule):
    slot_map = defaultdict(list)

    for entry in schedule:
        day = entry['day']
        time_slot = entry['time_slot']
        week = entry['week']
        group = entry['group']
        slot = (week, day, time_slot, group)
        slot_map[slot].append(entry)

    shared_entries = []
    for slot, entries in slot_map.items():
        if len(entries) > 1:
            shared_entries.extend(entries)
    # print(len(shared_entries))
    return shared_entries


def find_slots_entries_with_shared_room_and_time(schedule):
    room_time_map = {}

    for entry in schedule:
        room = entry['room']
        day = entry['day']
        time_slot = entry['time_slot']
        week = entry['week']
        if room and day and time_slot:
            key = (room, day, time_slot, week) 
            if key not in room_time_map:
                room_time_map[key] = []
            room_time_map[key].append(entry)

    shared_entries = [
        entry
        for entries in room_time_map.values()
        if len(entries) > 1
        for entry in entries
    ]
    # print(shared_entries)
    return shared_entries


def find_slots_entries_with_shared_lecturers(schedule):
    lecturer_time_map = {}

    for entry in schedule:
        lecturer = entry['lecturer']
        day = entry['day']
        time_slot = entry['time_slot']
        week = entry['week']
        key = (lecturer, day, time_slot, week)
        if key not in lecturer_time_map:
            lecturer_time_map[key] = []
        lecturer_time_map[key].append(entry)

    shared_entries = [
        entry
        for entries in lecturer_time_map.values()
        if len(entries) > 1
        for entry in entries
    ]
    # print(shared_entries)
    return shared_entries


def mutate(schedule):
    for entry in find_group_entries_with_shared_slot(schedule):
        empty_slots = get_empty_slots_for_group(schedule, entry['group'])
        if empty_slots:
            entry["day"], entry["time_slot"] = random.choice(empty_slots)
        else:
            if random.random() < MUTATION_RATE:
                entry = random.choice(schedule)
                empty_slots = get_empty_slots_for_group(schedule, entry['group'])
                if empty_slots:
                    entry["day"], entry["time_slot"] = random.choice(empty_slots)
    for entry in find_slots_entries_with_shared_room_and_time(schedule):
        empty_rooms = find_empty_rooms(schedule, entry['day'], entry['time_slot'])
        if empty_rooms:
            entry["room"] = random.choice(empty_rooms)
    for entry in find_slots_entries_with_shared_lecturers(schedule):
        free_lecturers = find_free_lecturers(schedule, entry['day'], entry['time_slot'], entry['subject'])
        if free_lecturers:
            entry["lecturer"] = random.choice(free_lecturers)
    return schedule


def print_table(data_frame):
    for i in range(1000):
        week_1 = data_frame[data_frame['week'] == i]
        if week_1.empty:
            break

        week_1["combined"] = week_1["subject"] + "\n" + week_1["room"] + "\n" + week_1["lecturer"]
        pivot_table = week_1.pivot_table(
            index=['day', 'time_slot'],
            columns='group',
            values='combined',
            aggfunc=lambda x: ', '.join(x)
        ).fillna('')

        pivot_table = pivot_table.reset_index()

        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_table['day'] = pd.Categorical(pivot_table['day'], categories=day_order, ordered=True)
        pivot_table = pivot_table.sort_values(by=['day', 'time_slot']).reset_index(drop=True)
        table = tabulate(pivot_table, headers='keys', tablefmt='grid')

        print(table)


def genetic_algorithm():
    for i in range(20):
        print(f'TRY № {i}')
        population = initialize_population()
        valid = False
        for _ in range(MAX_ITERATIONS):
            new_population = []
            for _ in range(POPULATION_SIZE // 2):
                parent1, parent2 = random.sample(selection(population), 2)
                child = crossover(parent1, parent2)
                child = mutate(child)
                new_population.append(child)
            population.extend(new_population)
            best_schedule = max(population, key=fitness)
            valid, *score = is_valid_schedule(best_schedule)
            print(score)
            # print_table(pd.DataFrame(best_schedule))
            if valid:
                break
        else:
            continue

    print('VALID' if valid else 'NOT VALID')

    return best_schedule


best_schedule = genetic_algorithm()


df = pd.DataFrame(best_schedule)
df.sort_values(by=["group", "week", "day", "time_slot"], inplace=True)
df.to_csv("schedule.csv", index=False)
print_table(df)
