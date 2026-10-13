# Coding Agent Harness

A small coding agent built from scratch in Python, without using an agent framework.

I built this project to better understand how coding agents work under the hood, from communicating with an LLM and executing tools to managing context, permissions, and subagents.

The goal was to explore the different components that make up a coding agent and how they work together.

## Features

- **Tool calling:** Read, create, and edit files, and execute shell commands.
- **Permissions:** Allow, deny, or request approval before executing certain operations.
- **Sandboxing:** Restrict shell command execution using Bubblewrap on Linux or Seatbelt on macOS.
- **Session management:** Save conversations locally, resume previous sessions, and rewind message history.
- **Task planning:** Track progress through a todo list.
- **Context management:** Summarize long conversations and trim large tool outputs to reduce context usage.
- **Subagents:** Delegate codebase exploration to a separate agent with its own context and restricted tools.
- **Skills:** Load reusable instructions to guide the agent through specific tasks.
- **CLI:** Interact with the agent directly from the terminal.

## Getting Started

### Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- An API key from an OpenAI-compatible model provider

For Linux sandboxing, Bubblewrap is also required.

### Installation

Clone the repository and navigate to the project directory.

Install the dependencies:

```bash
uv sync
```

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Configure your model provider in `.env`. For example, with OpenRouter:

```dotenv
BASE_URL=https://openrouter.ai/api/v1
API_KEY=your_api_key
MODEL=your_model
```

You can also configure `CONTEXT_WINDOW` to match the context capacity of your model.

The application loads `.env` automatically, so there is no need to export these variables manually. Environment variables already exported in your shell take precedence.

### Run

Start the agent:

```bash
uv run coding-agent-harness
```

To resume the most recently used session:

```bash
uv run coding-agent-harness --resume
```

For example, you can ask:

> Read the code in coding_agent_harness/ and explain how tool calls are handled.

## Usage

The agent provides an interactive terminal interface.

- **Enter:** Submit a prompt.
- **Alt + Enter:** Insert a newline.
- **Up Arrow:** Recall a previous input.
- **Ctrl + D:** Exit.

### Commands

| Command | Description |
|---|---|
| `/sessions` | List and switch between saved conversations |
| `/rewind` | Return to an earlier point in the conversation |
| `/compact` | Summarize older conversation history |
| `--resume` | Resume the most recently used session |
| `--debug` | Display raw model response information for debugging |

Sessions and prompt history are stored locally under `.agents/` in the working directory.

Rewinding only changes the conversation history; it does not undo file modifications. Task plans are kept in memory and are not restored when resuming a session.

## How It Works

The agent follows a simple loop:

1. The user provides a prompt.
2. The harness sends the conversation and available tool definitions to the LLM.
3. The model either produces a response or requests one or more tool calls.
4. The harness checks permissions and executes approved tools.
5. Tool results are returned to the model, allowing it to continue working.

This process repeats until the model produces a final response.

### Context Management

As conversations grow, the agent needs to manage the amount of information sent to the model.

Large tool outputs are trimmed, and older conversation history can be summarized when the context approaches a configured limit.

Compaction can happen automatically or be triggered manually with `/compact`.

### Subagents

The main agent can delegate codebase exploration through the `task` tool.

Each subagent runs with its own conversation context and a restricted set of tools. It can inspect files, search through code, and report its findings without carrying its entire exploration history into the main conversation.

Only the final report is returned to the main agent.

## Permissions and Sandboxing

Before executing tools, the harness checks whether an operation should be allowed, denied, or require user approval.

Shell commands can run inside an OS-level sandbox. On Ubuntu or Debian, install Bubblewrap using:

```bash
sudo apt-get install bubblewrap
```

When the sandbox is active, shell commands have restricted filesystem access, with writes limited to the project directory and network access disabled.

The terminal displays the active sandbox mode. If it shows `Sandbox: none`, shell commands are not isolated at the operating-system level.

Python-based file tools are controlled separately through the permission system.

These protections are useful for experimentation but should not be considered a complete security boundary.

## Skills

Skills provide reusable instructions for specific tasks.

They are defined in `SKILL.md` files and can be placed in:

- `.agents/skills/<name>/SKILL.md`
- `~/.agents/skills/<name>/SKILL.md`

Each skill contains a name, description, and instructions that guide the agent.

A code-review skill is included. For example:

> Use the code-review skill to review coding_agent_harness/tools.py without changing files.

Restart the agent after adding a new skill.

## Installing the CLI

To make the command available outside the repository, run:

```bash
uv tool install --editable .
```

You can then launch the agent from another project directory:

```bash
coding-agent-harness
```

If the command is not found, run `uv tool update-shell` and restart your terminal.

Configuration can be loaded from the current working directory's `.env`, the source checkout's `.env`, or `~/.agents/env`.