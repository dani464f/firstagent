from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Process(str, Enum):
    sequential = "sequential"


@dataclass
class Agent:
    role: str
    goal: str
    backstory: str
    allow_delegation: bool = False
    verbose: bool = False


@dataclass
class Task:
    description: str
    expected_output: str
    agent: Agent
    context: list["Task"] = field(default_factory=list)
    output: str = ""

    def run(self) -> str:
        # lightweight deterministic task execution placeholder for local MVP.
        content = self.description
        if "SUBJECT:" in content and "BODY:" in content:
            self.output = (
                "SUBJECT: Payment reminder\n"
                "BODY:\n"
                "Hello, this is your reminder."
            )
        else:
            self.output = content[:400]
        return self.output


@dataclass
class Crew:
    agents: list[Agent]
    tasks: list[Task]
    process: Process = Process.sequential
    verbose: bool = False

    def kickoff(self) -> str:
        result = ""
        for task in self.tasks:
            result = task.run()
        return result
