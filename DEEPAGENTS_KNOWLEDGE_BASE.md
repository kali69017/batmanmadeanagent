# Deep Agents Knowledge Base

> Compiled from https://docs.langchain.com/oss/python/deepagents/
> Date: 2026-07-23

---

## 1. Overview

Deep Agents is a standalone Python library (built on LangChain + LangGraph) for building LLM-powered agents with built-in task planning, virtual filesystem, subagent spawning, context management, and memory.

**Key capabilities:**
- **Execution environment**: Tools, virtual filesystem, optional sandbox, REPL (interpreter)
- **Context management**: Skills, memory, summarization, context offloading, prompt caching
- **Delegation**: Subagent spawning and task planning
- **Steering**: Human-in-the-loop approval and interrupts

Install: `pip install deepagents`

**Model format:** `provider:model` (e.g. `"anthropic:claude-sonnet-4-6"`, `"openai:gpt-5.5"`, `"google_genai:gemini-3.5-flash"`, `"openrouter:z-ai/glm-5.2"`, `"ollama:north-mini-code-1.0"`).

---

## 2. Quickstart

```python
from deepagents import create_deep_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

agent.invoke({"messages": [{"role": "user", "content": "what is the weather in sf"}]})
```

**LangSmith tracing:** Set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`.

---

## 3. Full create_deep_agent Signature

```python
create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    *,
    system_prompt: str | SystemMessage | SystemPromptConfig | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: Sequence[SubAgent | CompiledSubAgent | AsyncSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    permissions: list[FilesystemPermission] | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    response_format: ResponseFormat[ResponseT] | type[ResponseT] | dict[str, Any] | None = None,
    state_schema: type[DeepAgentState] | None = None,
    context_schema: type[ContextT] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None
) -> CompiledStateGraph
```

---

## 4. Model Configuration

Pass a string in `provider:model` format or an initialized model instance.

Examples:
```python
# Provider:model string (auto-resolves)
agent = create_deep_agent(model="openai:gpt-5.5")

# init_chat_model
from langchain.chat_models import init_chat_model
model = init_chat_model("openai:gpt-5.5")
agent = create_deep_agent(model=model)

# Direct class
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-5.5")
agent = create_deep_agent(model=model)
```

**Supported providers:** OpenAI, Anthropic, Google Gemini, AWS Bedrock, Azure, HuggingFace, OpenRouter, Fireworks, Baseten, Ollama, and any LangChain-compatible model.

---

## 5. System Prompt

Deep Agents ship with a built-in base system prompt (planning, filesystem, subagents guidance). Pass `system_prompt=` to prepend.

For full control, use `SystemPromptConfig` dict:
```python
create_deep_agent(..., system_prompt={
    "prefix": "text before base prompt",
    "base": "replaces built-in base prompt (omit to keep, None to drop)",
    "suffix": "text after base prompt",
})
```

---

## 6. Tools

Custom functions, LangChain tools, or MCP tools passed via `tools=`. Built-in harness tools are always available:

| Tool | Description |
|------|-------------|
| `ls` | List files in a directory |
| `read_file` | Read file contents (with pagination, multimodal support) |
| `write_file` | Create or overwrite a file |
| `edit_file` | Exact string replacements in files |
| `delete` | Delete file or directory recursively (0.7.a1+) |
| `glob` | Find files matching a glob pattern |
| `grep` | Search file contents |
| `execute` | Run shell commands (sandbox backends only) |
| `task` | Spawn a subagent for delegated work |
| `write_todos` | Manage a structured todo list |

**MCP Tools:** Full support via `langchain-mcp-adapters`:
```python
from langchain_mcp_adapters.client import MultiServerMCPClient
async with MultiServerMCPClient({"my_server": {"transport": "http", "url": "..."}}) as client:
    tools = await client.get_tools()
    agent = create_deep_agent(model="...", tools=tools)
```

---

## 7. Backends (Virtual Filesystem)

Pluggable backends for filesystem operations.

| Backend | Description |
|---------|-------------|
| `StateBackend()` | Default. Thread-scoped, stored in LangGraph state, persists across turns via checkpointer |
| `FilesystemBackend(root_dir=".", virtual_mode=True)` | Real local disk access |
| `LocalShellBackend(root_dir=".", virtual_mode=True)` | Filesystem + shell execution on host (no isolation) |
| `StoreBackend(namespace=lambda rt: (...))` | LangGraph store, cross-thread durable |
| `ContextHubBackend("my-agent")` | LangSmith Context Hub repo |
| `CompositeBackend(default=..., routes={...})` | Route paths to different backends |

**CompositeBackend pattern (recommended):**
```python
agent = create_deep_agent(
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/workspace/": FilesystemBackend(root_dir="/path/to/project", virtual_mode=True),
            "/memories/": StoreBackend(namespace=lambda rt: (rt.server_info.user.identity,)),
        },
    )
)
```

---

## 8. Permissions

Declarative path-based access control for built-in filesystem tools.

```python
from deepagents import FilesystemPermission, create_deep_agent

agent = create_deep_agent(
    model="...",
    permissions=[
        FilesystemPermission(operations=["read", "write"], paths=["/workspace/**"], mode="allow"),
        FilesystemPermission(operations=["read", "write"], paths=["/workspace/.env"], mode="deny"),
        FilesystemPermission(operations=["read", "write"], paths=["/**"], mode="deny"),
    ],
)
```

**Fields:** `operations` (`["read"]` | `["write"]` | both), `paths` (glob patterns), `mode` (`"allow"` | `"deny"` | `"interrupt"`).

First-match-wins. Subagents inherit parent permissions by default; can override with their own `permissions` field.

---

## 9. Sandboxes

Sandbox backends provide filesystem tools + `execute` tool in isolated environments.

**Supported providers:** LangSmith, Daytona, E2B, Modal, Runloop, Vercel, AgentCore, Deno.

**Two architecture patterns:**
1. **Agent in sandbox**: Agent runs inside the sandbox
2. **Sandbox as tool**: Agent runs on host, calls sandbox tools remotely

```python
from deepagents.backends import LangSmithSandbox
from langsmith.sandbox import SandboxClient

client = SandboxClient()
ls_sandbox = client.create_sandbox()
backend = LangSmithSandbox(sandbox=ls_sandbox)

agent = create_deep_agent(model="...", backend=backend)
```

---

## 10. Subagents

Subagents isolate heavy work from the main agent's context. Two types:

**Dictionary-based SubAgent:**
```python
research_subagent = {
    "name": "research-agent",
    "description": "Researches topics in depth",
    "system_prompt": "You are a researcher. Return concise summaries.",
    "tools": [web_search],
    "model": "openai:gpt-5.5",  # Optional override
}
agent = create_deep_agent(model="...", subagents=[research_subagent])
```

**CompiledSubAgent** (for custom LangGraph graphs):
```python
from deepagents import CompiledSubAgent
custom_graph = create_agent(model=..., tools=..., system_prompt=...)
subagent = CompiledSubAgent(name="data-analyzer", description="...", runnable=custom_graph)
```

**Dynamic subagents** (via CodeInterpreterMiddleware): Dispatch subagents from JavaScript code using `task()` global for fan-out, verification, recursive workflows.

The `general-purpose` subagent is auto-added by default. Disable with `general_purpose_subagent.enabled = False` on harness profile.

---

## 11. Human-in-the-Loop

Pause execution before sensitive tool calls for human approval.

```python
agent = create_deep_agent(
    model="...",
    interrupt_on={
        "delete_file": True,  # approve, edit, reject, respond
        "write_file": {"allowed_decisions": ["approve", "reject"]},
        "read_file": False,  # No interrupt
    },
    checkpointer=MemorySaver(),  # Required!
)
```

**Decision types:** `approve`, `edit`, `reject`, `respond`.
**Conditional interrupts:** Add a `when` predicate to interrupt only specific calls.
**Resume:** Use `Command(resume={"decisions": [...]})` with same `config`.

Filesystem permission interrupts: Use `mode="interrupt"` in `FilesystemPermission` rules.

---

## 12. Context Engineering

| Context Type | Scope | Description |
|-------------|-------|-------------|
| Input context | Static, per run | System prompt, memory (AGENTS.md), skills, tool prompts |
| Runtime context | Per invoke | User metadata, API keys via `context_schema` + `context=` arg |
| Context compression | Automatic | Offloading (>20K tokens → filesystem), summarization (85% context limit) |
| Context isolation | Per subagent | Subagents quarantine heavy work, return only results |
| Long-term memory | Cross-thread | StoreBackend + CompositeBackend for `/memories/` persistence |

**Custom state schema:** Subclass `DeepAgentState` for extra fields that survive checkpointing:
```python
from deepagents import DeepAgentState
class ResearchState(DeepAgentState):
    page_url: str
    file_urls: list[str]
```

---

## 13. Skills

Skills are reusable directories with a `SKILL.md` (YAML frontmatter + instructions) and optional `scripts/`, `references/`, `assets/` directories.

**Progressive disclosure:** At startup, only skill name + description from frontmatter is loaded. Full content loads when the skill is activated. Supporting files load on demand.

```python
agent = create_deep_agent(model="...", skills=["./skills/"])
```

**SKILL.md structure:**
```yaml
---
name: skill-name
description: When to use this skill (be specific)
---
# Instructions
Step-by-step guidance for the agent.
```

Subagents can have their own `skills` (don't inherit from parent). Use `FilesystemPermission` to enforce read-only skills.

---

## 14. Event Streaming

Deep Agents add subagent streaming on top of LangGraph streaming:

```python
stream = agent.stream_events(input, version="v3")

# Top-level messages
for message in stream.messages:
    print("[coordinator]", message.text)

# Subagent streams
for subagent in stream.subagents:
    print(subagent.name, subagent.status)
    for message in subagent.messages:
        print(f"[{subagent.name}]", message.text)
    for call in subagent.tool_calls:
        print(call.tool_name, call.input)
```

**Stream fields:** `messages`, `tool_calls`, `values`, `subagents`, `output`.
**Concurrent consumption:** Use `stream.interleave("messages", "subagents")` or `asyncio.gather()`.

---

## 15. Interpreters

QuickJS-based in-memory JavaScript runtime inside the agent loop. Adds an `eval` tool.

```python
from langchain_quickjs import CodeInterpreterMiddleware

agent = create_deep_agent(
    model="...",
    middleware=[CodeInterpreterMiddleware()],
)
```

**Programmatic Tool Calling (PTC):** Expose tools inside interpreter code via allowlist:
```python
CodeInterpreterMiddleware(ptc=["web_search"])
```
Then in JavaScript: `await tools.webSearch({query: "..."})`

**Persistence modes:** `"thread"` (default, across turns), `"turn"` (within one turn), `"call"` (fresh per eval).
**Dynamic subagents:** `task()` global available when subagents configured.

---

## 16. Middleware Stack (Default)

**Main agent** (first to last):
1. `TodoListMiddleware` — Todo list tracking
2. `SkillsMiddleware` — Skill discovery (only when `skills` passed)
3. `FilesystemMiddleware` — File operations
4. `SubAgentMiddleware` — Subagent spawning
5. `SummarizationMiddleware` — Context compression
6. `PatchToolCallsMiddleware` — Repair dangling tool calls
7. `AsyncSubAgentMiddleware` — Async subagents (only when configured)
8. Your middleware (merged after Patch)
9. Harness profile extras
10. Excluded-tool filtering
11. Prompt caching (Anthropic/Bedrock)
12. `MemoryMiddleware` (only when `memory` passed)
13. `HumanInTheLoopMiddleware` (only when `interrupt_on` passed)

Custom middleware replaces a default if `.name` matches; otherwise lands after Patch.

---

## 17. Key Links

- **PyPI:** https://pypi.org/project/deepagents/
- **GitHub:** https://github.com/langchain-ai/deepagents
- **API Reference:** https://reference.langchain.com/python/deepagents/
- **LangChain Skills:** https://github.com/langchain-ai/langchain-skills
- **LangSmith:** https://smith.langchain.com
