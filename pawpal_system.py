from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from enum import Enum
from typing import List, Optional, Tuple


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Recurrence(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}

# How far ahead the next occurrence of a recurring task falls.
RECURRENCE_STEP = {Recurrence.DAILY: timedelta(days=1), Recurrence.WEEKLY: timedelta(weeks=1)}


def parse_hhmm(value: str) -> int:
    """Convert a 'HH:MM' string to minutes from midnight."""
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def format_minutes(minutes: int) -> str:
    """Format minutes-from-midnight as a 24-hour HH:MM string."""
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def tasks_overlap(a: Task, b: Task) -> bool:
    """True if two tasks' time spans intersect (touching ends don't count)."""
    return a.start_minutes < b.end_minutes and b.start_minutes < a.end_minutes


@dataclass
class Owner:
    name: str
    available_minutes: int
    requested_services: str = ""


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    start_time: str = "08:00"  # 24-hour "HH:MM"
    is_complete: bool = False
    recurrence: Recurrence = Recurrence.NONE
    due_date: Optional[date] = None  # the day this occurrence is scheduled for

    @property
    def start_minutes(self) -> int:
        """Start time as minutes from midnight (parsed from the HH:MM string)."""
        return parse_hhmm(self.start_time)

    @property
    def end_minutes(self) -> int:
        """Minute-of-day at which this task finishes."""
        return self.start_minutes + self.duration_minutes

    @property
    def is_recurring(self) -> bool:
        return self.recurrence != Recurrence.NONE

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_complete = True

    def next_occurrence(self, today: Optional[date] = None) -> Optional["Task"]:
        """Build the next pending instance of a recurring task.

        Returns a fresh, incomplete copy with its due_date advanced by one day
        (daily) or one week (weekly). Returns None for non-recurring tasks.
        """
        step = RECURRENCE_STEP.get(self.recurrence)
        if step is None:
            return None
        base = self.due_date or today or date.today()
        return replace(self, is_complete=False, due_date=base + step)


@dataclass
class Pet:
    name: str
    breed: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        self.tasks.remove(task)

    def complete_task(self, task: Task, today: Optional[date] = None) -> Optional[Task]:
        """Mark a task complete and, if it recurs, queue its next occurrence.

        Returns the newly created next-occurrence task, or None if the task
        does not recur.
        """
        task.mark_complete()
        next_task = task.next_occurrence(today=today)
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    def filter_tasks(
        self,
        *,
        complete: bool | None = None,
        priority: Priority | None = None,
    ) -> List[Task]:
        """Return tasks matching the given criteria, preserving current order.

        Any argument left as None is ignored, so callers can filter by
        completion status, priority, or both.
        """
        return [
            t
            for t in self.tasks
            if (complete is None or t.is_complete == complete)
            and (priority is None or t.priority == priority)
        ]

    def pending(self) -> List[Task]:
        """Convenience: tasks that are not yet complete."""
        return self.filter_tasks(complete=False)

    def sort_tasks(self) -> None:
        """Sort tasks in-place by start time, then priority, then duration.

        Same-slot ties break toward higher priority, and equal-priority ties
        toward the shorter task. Python's sort is stable, so this single
        multi-key pass is deterministic and runs in O(n log n).
        """
        self.tasks.sort(
            key=lambda t: (
                tuple(map(int, t.start_time.split(":"))),
                PRIORITY_ORDER.get(t.priority, 99),
                t.duration_minutes,
            )
        )


@dataclass
class Scheduler:
    pet: Pet
    owner: Owner

    def sort_by_priority(self) -> List[Task]:
        """Return tasks sorted from highest to lowest priority without mutating the list."""
        return sorted(self.pet.tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    def sort_by_time(self) -> List[Task]:
        """Return tasks ordered by start time (earliest first) without mutating the list.

        Same-slot ties break toward higher priority, then the shorter task.
        """
        return sorted(
            self.pet.tasks,
            key=lambda t: (
                tuple(map(int, t.start_time.split(":"))),
                PRIORITY_ORDER.get(t.priority, 99),
                t.duration_minutes,
            ),
        )

    def find_conflicts(self) -> List[Tuple[Task, Task]]:
        """Return pairs of this pet's pending tasks whose time spans overlap.

        Tasks are swept in start-time order, so once a later task starts after
        the current one ends we stop comparing — close to O(n) for the typical
        sparse day rather than O(n^2).
        """
        ordered = sorted(self.pet.pending(), key=lambda t: t.start_minutes)
        conflicts: List[Tuple[Task, Task]] = []
        for i, earlier in enumerate(ordered):
            for later in ordered[i + 1 :]:
                if later.start_minutes >= earlier.end_minutes:
                    break  # sorted by start: nothing after this can overlap `earlier`
                if tasks_overlap(earlier, later):
                    conflicts.append((earlier, later))
        return conflicts

    @staticmethod
    def find_conflicts_among(pets: List[Pet]) -> List[Tuple[Pet, Task, Pet, Task]]:
        """Return overlapping pending tasks across pets (the owner can't be in two
        places at once). Pairs from the same pet are included too.

        Each result is (pet_a, task_a, pet_b, task_b) ordered by start time.
        """
        items: List[Tuple[Pet, Task]] = [
            (pet, task) for pet in pets for task in pet.pending()
        ]
        items.sort(key=lambda pt: pt[1].start_minutes)
        conflicts: List[Tuple[Pet, Task, Pet, Task]] = []
        for i, (pet_a, task_a) in enumerate(items):
            for pet_b, task_b in items[i + 1 :]:
                if task_b.start_minutes >= task_a.end_minutes:
                    break
                if tasks_overlap(task_a, task_b):
                    conflicts.append((pet_a, task_a, pet_b, task_b))
        return conflicts

    def fit_tasks_by_time(self) -> List[Task]:
        """Return the highest-priority pending tasks that fit within the owner's available time."""
        plan: List[Task] = []
        time_remaining = self.owner.available_minutes
        pending = self.pet.pending()
        for task in sorted(pending, key=lambda t: PRIORITY_ORDER.get(t.priority, 99)):
            if task.duration_minutes <= time_remaining:
                plan.append(task)
                time_remaining -= task.duration_minutes
        return plan

    def generate_plan(self) -> List[Task]:
        """Generate the recommended task plan for the current pet and owner."""
        return self.fit_tasks_by_time()

    def mark_task_done(self, task: Task) -> Optional[Task]:
        """Mark the given task complete, queuing its next occurrence if recurring."""
        return self.pet.complete_task(task)
