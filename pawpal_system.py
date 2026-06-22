from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class Owner:
    name: str
    available_minutes: int
    requested_services: str = ""


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    is_complete: bool = False

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    breed: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, _task: Task) -> None:
        pass

    def remove_task(self, _task: Task) -> None:
        pass

    def sort_tasks(self) -> None:
        pass


@dataclass
class Scheduler:
    pet: Pet
    owner: Owner

    def generate_plan(self) -> List[Task]:
        pass

    def fit_tasks_by_time(self) -> List[Task]:
        pass

    def sort_by_priority(self) -> List[Task]:
        pass

    def mark_task_done(self, task: Task) -> None:
        pass
