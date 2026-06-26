from dataclasses import dataclass, field
from typing import Literal


@dataclass
class LoopTemplate:
    id: str
    name: str
    description: str
    loop_type: str
    task: str
    goal: str
    generator_cli: str = "devin"
    judge_cli: str = "devin"


@dataclass
class SkillTemplate:
    id: str
    name: str
    description: str
    category: str
    description_goal: str
    generator_cli: str = "devin"
    judge_cli: str = "devin"


@dataclass
class PromptTemplate:
    id: str
    name: str
    description: str
    description_goal: str
    variables: list[str] = field(default_factory=list)
    generator_cli: str = "devin"
    judge_cli: str = "devin"


LOOP_TEMPLATES: list[LoopTemplate] = [
    LoopTemplate(
        id="coding-react-component",
        name="React Component",
        description="Evolve a React component to meet a design spec",
        loop_type="coding",
        task="Write a React component that implements the described UI",
        goal="Component is clean, typed, accessible, and matches the spec exactly",
    ),
    LoopTemplate(
        id="coding-api-endpoint",
        name="API Endpoint",
        description="Evolve a REST endpoint implementation",
        loop_type="coding",
        task="Implement the described API endpoint with validation and error handling",
        goal="Endpoint handles all edge cases, returns correct status codes, is well-tested",
    ),
    LoopTemplate(
        id="debugging-stack-trace",
        name="Stack Trace Analysis",
        description="Evolve a root-cause analysis and fix for a bug",
        loop_type="debugging",
        task="Analyze the stack trace and produce a diagnosis with a concrete fix",
        goal="Fix is correct, minimal, and explains the root cause clearly",
    ),
    LoopTemplate(
        id="docs-readme",
        name="README Generator",
        description="Evolve a README for a project",
        loop_type="docs",
        task="Write a README for the project that covers setup, usage, and architecture",
        goal="README is clear, complete, scannable, and a developer can start from it in under 5 minutes",
    ),
    LoopTemplate(
        id="prompt-system-prompt",
        name="System Prompt Optimizer",
        description="Evolve a system prompt for an LLM assistant",
        loop_type="prompt",
        task="Write a system prompt that makes the assistant behave as described",
        goal="Prompt produces consistent, correct, and well-formatted responses on varied inputs",
    ),
    LoopTemplate(
        id="design-adr",
        name="Architecture Decision Record",
        description="Evolve an ADR for a technical decision",
        loop_type="design",
        task="Write an Architecture Decision Record for the described technical choice",
        goal="ADR is concise, covers context/decision/consequences, and is understandable by a new engineer",
    ),
    LoopTemplate(
        id="rfc-feature",
        name="Feature RFC",
        description="Evolve an RFC for a new feature",
        loop_type="rfc",
        task="Write an RFC proposing the described feature including motivation, design, and trade-offs",
        goal="RFC is thorough, anticipates objections, and gives enough detail to implement from",
    ),
]

SKILL_TEMPLATES: list[SkillTemplate] = [
    SkillTemplate(
        id="skill-code-review",
        name="Code Reviewer",
        description="Reviews code for bugs, style, and architecture",
        category="code-review",
        description_goal="A skill that reviews code diffs or files and produces actionable, prioritized feedback with file:line references",
    ),
    SkillTemplate(
        id="skill-unit-test-writer",
        name="Unit Test Writer",
        description="Generates unit tests for a given function or module",
        category="testing",
        description_goal="A skill that reads source code and produces comprehensive unit tests covering happy paths, edge cases, and error conditions",
    ),
    SkillTemplate(
        id="skill-docstring-generator",
        name="Docstring Generator",
        description="Writes docstrings for functions and classes",
        category="documentation",
        description_goal="A skill that reads a function or class and produces a clear, concise docstring following the project's style",
    ),
    SkillTemplate(
        id="skill-dockerfile-reviewer",
        name="Dockerfile Reviewer",
        description="Reviews Dockerfiles for best practices and security",
        category="devops",
        description_goal="A skill that reviews a Dockerfile and identifies security issues, inefficiencies, and deviations from best practices with concrete fixes",
    ),
    SkillTemplate(
        id="skill-data-pipeline-reviewer",
        name="Data Pipeline Reviewer",
        description="Reviews data pipelines for correctness and efficiency",
        category="data-analysis",
        description_goal="A skill that reviews a data pipeline definition and flags data quality issues, performance bottlenecks, and missing error handling",
    ),
    SkillTemplate(
        id="skill-custom",
        name="Custom Skill",
        description="Start from scratch",
        category="custom",
        description_goal="",
    ),
]

PROMPT_TEMPLATES: list[PromptTemplate] = [
    PromptTemplate(
        id="prompt-explain-code",
        name="Code Explainer",
        description="Explains code in plain language",
        description_goal="A prompt that takes code and a language and explains what it does, why each part exists, and any non-obvious patterns",
        variables=["language", "code"],
    ),
    PromptTemplate(
        id="prompt-fix-bug",
        name="Bug Fix Request",
        description="Asks an LLM to diagnose and fix a bug",
        description_goal="A prompt that takes an error message and the surrounding code and produces a diagnosis plus a minimal, correct fix",
        variables=["error", "code"],
    ),
    PromptTemplate(
        id="prompt-commit-message",
        name="Commit Message Writer",
        description="Generates a git commit message from a diff",
        description_goal="A prompt that takes a git diff and writes a conventional commit message: short subject, optional body explaining the why",
        variables=["diff"],
    ),
    PromptTemplate(
        id="prompt-email-draft",
        name="Email Drafter",
        description="Drafts a professional email",
        description_goal="A prompt that takes a topic, recipient, and tone and drafts a concise professional email",
        variables=["topic", "recipient", "tone"],
    ),
    PromptTemplate(
        id="prompt-docs-from-code",
        name="Docs from Code",
        description="Generates documentation from source code",
        description_goal="A prompt that reads source code and produces structured documentation in the specified format",
        variables=["code", "format"],
    ),
    PromptTemplate(
        id="prompt-custom",
        name="Custom Prompt",
        description="Start from scratch",
        description_goal="",
        variables=[],
    ),
]
