"""Three-level planning modes."""

LEVEL_DIRECT = 0
LEVEL_ORGANIZE = 1
LEVEL_FULL = 2

MODE_BY_LEVEL = {
    LEVEL_DIRECT: "direct_execute",
    LEVEL_ORGANIZE: "task_organization",
    LEVEL_FULL: "full_workflow",
}

WORKFLOW_BY_LEVEL = {
    LEVEL_DIRECT: "direct",
    LEVEL_ORGANIZE: "organize",
    LEVEL_FULL: "developer",
}

AGENTS_BY_LEVEL = {
    LEVEL_DIRECT: ["coder", "tester", "git"],
    LEVEL_ORGANIZE: ["organizer", "coder"],
    LEVEL_FULL: ["architect", "planner", "coder", "tester", "reviewer"],
}
