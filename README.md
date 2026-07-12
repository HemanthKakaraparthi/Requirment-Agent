# Requirement Agent

**SDLC Pipeline — Agent 1**

Converts any form of input (raw idea, PDF, Word doc, CSV, Teams conversation) into a
complete, organisation-grade PRD (Product Requirements Document). Output feeds directly
into the Planning Agent (Agent 2).

---

## Pipeline Position

```
  [You]
    │
    │  raw idea / file / Teams export
    ▼
┌─────────────────────────────┐
│      Requirement Agent      │  ← YOU ARE HERE
│                             │
│  • Reads your input         │
│  • Asks only what's missing │
│  • Validates structure      │
│  • Saves PRD                │
└─────────────────────────────┘
    │
    │  output/*.json  ──►  Planning Agent (Agent 2)
    │  output/*.md    ──►  Team / Stakeholders
```

---

## Quick Start

```bash
# 1. Install dependencies (once, from SDLC root)
pip install -r ../requirements.txt

# 2. Make sure SDLC/.env exists with your keys (see Environment Variables section)

# 3. Run
python main.py
```

---

## Environment Variables

Location: `SDLC/.env` (one level above this folder — shared by all agents)

```env
# Required — base URL of your OpenAI-compatible API gateway
ASIMOV_BASE_URL=https://your-api-gateway/openai/v1

# Required — API key
ASIMOV_API_KEY=your-api-key-here

# Optional — model name, defaults to openai/gpt-5-chat
ASIMOV_MODEL=openai/gpt-5-chat
```

---

## Inputs

The agent accepts four types of input. You can combine them — e.g. give a PDF and
then add more context in text.

### 1. PDF file

A design brief, business case, or any document with requirements.

```
You: C:/Users/heman/Downloads/experiment_brief.pdf
```

The agent calls `read_input_file`, extracts all text using `pypdf`, maps everything
it finds to PRD fields, and only asks for what is genuinely missing.

---

### 2. Word document (.docx)

Spec documents, feature proposals, existing requirement docs.

```
You: C:/Users/heman/Documents/feature_spec.docx
```

Reads paragraph text and all table cells using `python-docx`.

---

### 3. CSV file

Feature lists, stakeholder sheets, requirement backlogs exported from Excel or Jira.

```
You: C:/Users/heman/Downloads/features.csv
```

Uses `pandas` — shows the agent the column names and first 20 rows for context extraction.

---

### 4. Teams conversation export (.txt)

A copied Microsoft Teams chat or channel thread saved as a text file.

```
You: C:/Users/heman/Downloads/teams_chat.txt
```

**How to export a Teams conversation:**
1. Open the Teams chat or channel thread
2. Scroll to the top of the conversation
3. Select all messages → `Ctrl+A` → Copy → `Ctrl+C`
4. Open Notepad → Paste → `Ctrl+V`
5. Save as `teams_chat.txt`
6. Give that file path to the agent

The agent extracts from the conversation:
- Who is discussing → Stakeholders
- What problem they describe → Problem Statement
- Decisions made ("we agreed to...", "let's scope out...") → Scope
- Mentioned timelines, systems, constraints → Constraints & Dependencies
- Unresolved questions → Open Questions

---

### 5. Plain text description

Type or paste a description directly — no file needed.

```
You: We need a central dashboard for our analysts to track A/B experiments.
     Right now everything lives in Excel and we lose results every quarter.
```

---

## How the Agent Asks Questions

The agent does **not** run through a fixed list of 11 questions every time.
It first extracts everything it can from your input, then asks only for genuine gaps.

### The 11 PRD areas it needs to cover

| # | Area | Skipped if… |
|---|------|-------------|
| 1 | PRD Type (Feature / Bug Fix / Spike / Enhancement / Tech Debt) | File or description makes it obvious |
| 2 | Problem statement — what is broken, who feels it | Found in document |
| 3 | Business value — revenue, cost saving, risk, compliance | Mentioned in document |
| 4 | Stakeholders — name + role (email optional) | Names appear in document |
| 5 | Users / Personas — who will use this product | Described in document |
| 6 | Goals — measurable success metrics with targets | Found in document |
| 7 | Scope — what is in v1 vs explicitly out of scope | Described in document |
| 8 | Technical constraints — stack, infra, budget, timeline | Mentioned in document |
| 9 | Dependencies — other systems, teams, APIs, data | Mentioned in document |
| 10 | Assumptions — what the team is taking for granted | Not always in documents — usually asked |
| 11 | Open questions — unresolved items before dev starts | Extracted from Teams chat; otherwise asked |

**For a text description:** expect 3–5 targeted questions.
**For a well-written PDF or Word doc:** expect 1–3 questions.
**For a Teams conversation:** expect 2–4 questions (conversations rarely have goals or assumptions).

### Revision mode

If you load an existing PRD, the agent shows you a summary of what's already there
and asks only: *"What would you like to change?"* — no re-intake from scratch.

---

## Conversation Flows

### Flow A — PDF / Word / CSV input

```
Agent:  "Do you want to create a new PRD or revise an existing one?"

You:    "New — here's the brief: C:/Downloads/experiment_brief.pdf"
         └─► [read_input_file called internally]

Agent:  "I've read your PDF. Here's what I extracted:
         • Problem: Analysts track experiments manually in Excel
         • Stakeholders: John Smith (PO), Maria Lopez (Dev Lead)
         • Constraint: Azure only, 12-week delivery
         Just a few gaps remaining. What's the expected business value?"

You:    "Saves ~20% of experiment budget. Also reduces compliance risk."

Agent:  "What assumptions is the team making going into this?"
You:    "KPI API will be ready by week 4. Users have modern browsers."

Agent:  "Any open questions that need answering before dev starts?"
You:    "Who approves an experiment before it goes live?"

         └─► [get_current_date called]
         └─► PRD generated internally

Agent:  "Here's your PRD summary:
         Title:         Experiment Management Dashboard
         Type:          Feature
         Stories:       5  |  Requirements: 7  |  Open Questions: 1
         Does this look right? Save it or adjust anything?"

You:    "Save it"
         └─► [save_prd called — validated and written to output/]

Agent:  "Saved!
         MD   → output/20260407_143022_experiment_management_v1_0.md
         JSON → output/20260407_143022_experiment_management_v1_0.json"
```

---

### Flow B — Teams conversation export

```
Agent:  "Do you want to create a new PRD or revise an existing one?"
You:    "New. Here's the Teams thread: C:/Downloads/teams_chat.txt"
         └─► [read_input_file called]

Agent:  "I've read the Teams conversation (47 messages). I extracted:
         • Problem: No central place for experiment results
         • Stakeholders: Sarah (PM), Ravi (Data), Dev team
         • Decision: Out of scope — no ML integration in v1
         I need a bit more. What's the measurable success goal for this?"

You:    "80% reduction in duplicate experiments within 3 months"

Agent:  "What technical constraints should I capture?"
You:    "Must use Azure. GDPR compliant. Go-live in 12 weeks."

         └─► PRD generated

Agent:  "Summary: 4 stories, 6 requirements, 2 open questions. Save it?"
You:    "Yes"
```

---

### Flow C — Plain text

```
Agent:  "Give me a brief description or share a file path."
You:    "We need a login system with email and Google OAuth."

Agent:  "What problem does this solve and who experiences it?"
You:    "Users currently can't log in — there's no auth at all."

Agent:  "What's the business value?"
You:    "Required for launch. No auth = no product."

Agent:  "Any constraints — stack, timeline, budget?"
You:    "FastAPI backend, React frontend. Must ship in 6 weeks."

Agent:  [2 more quick questions → generates PRD → confirms → saves]
```

---

### Flow D — Revise existing PRD

```
Agent:  "Here are your existing PRDs: [list]
         Create new or revise one?"
You:    "Revise the login_system one"
         └─► [load_prd called]

Agent:  "Current PRD: Login System v1.0
         5 stories | 6 requirements | Status: Draft
         What would you like to change?"

You:    "Add a story for password reset and bump version to 1.1"

Agent:  [Adds story, updates version]
        "Updated. Save as v1.1?"
You:    "Yes"
```

---

## Output

### What gets saved

Two files written to `requirement-agent/output/` on every save:

```
output/
├── 20260407_143022_experiment_management_v1_0.json   ← for Planning Agent
└── 20260407_143022_experiment_management_v1_0.md     ← for team
```

**Filename format:** `YYYYMMDD_HHMMSS_<title>_v<version>.json / .md`

---

### `.json` — Machine-readable

Full `PRDDocument` as a structured JSON object. The Planning Agent reads this directly
to generate tickets — no copy-pasting required.

```json
{
  "title": "Experiment Management Dashboard",
  "version": "1.0",
  "date": "2026-04-07",
  "status": "Draft",
  "prd_type": "Feature",
  "author": "AI Requirement Agent",
  "stakeholders": [
    { "name": "John Smith", "role": "Product Owner", "email": null }
  ],
  "problem_statement": "Analysts track A/B experiments manually in Excel...",
  "business_value": "Saves 20% experiment budget, reduces compliance risk",
  "goals": [
    { "goal": "Reduce duplicate experiments", "metric": "Duplicate rate", "target": "80% reduction in 3 months" }
  ],
  "in_scope": ["Experiment creation form", "Results dashboard", "User roles"],
  "out_of_scope": ["ML integration", "Mobile app"],
  "personas": [
    { "name": "Data Analyst", "description": "Creates and monitors experiments", "key_need": "Central tracking" }
  ],
  "functional_requirements": [
    { "id": "FR-01", "requirement": "User can create an experiment with name, hypothesis, KPIs", "priority": "Must Have" }
  ],
  "user_stories": [
    {
      "id": "US-01",
      "title": "Create Experiment",
      "as_a": "Data Analyst",
      "i_want_to": "create a new experiment with a form",
      "so_that": "I have a single source of truth for all experiments",
      "acceptance_criteria": [
        { "criterion": "Form has fields: name, hypothesis, KPI, start/end date", "met": false },
        { "criterion": "Submitted experiment appears in the experiment list", "met": false },
        { "criterion": "User receives a confirmation message on success", "met": false }
      ],
      "priority": "Must Have",
      "story_points": 5,
      "labels": ["frontend", "backend"]
    }
  ],
  "edge_cases": [
    { "scenario": "User submits experiment with end date before start date", "expected_behaviour": "Validation error shown, form not submitted" }
  ],
  "technical_constraints": ["Must run on Azure AKS", "GDPR compliant"],
  "dependencies": ["KPI API from data pipeline team", "Auth service"],
  "assumptions": ["KPI API ready by week 4", "Users have modern browsers"],
  "open_questions": ["Who approves an experiment before it goes live?"]
}
```

---

### `.md` — Human-readable

Formatted markdown with 13 sections. Ready to paste into Confluence, GitHub, or Notion.

```
# PRD: Experiment Management Dashboard

| Version | Date       | Status | Type    |
|---------|------------|--------|---------|
| 1.0     | 2026-04-07 | Draft  | Feature |

## 1. Problem Statement
...
## 2. Business Value
...
## 3. Stakeholders
| Name       | Role          | Email |
...
## 4. Goals & Success Metrics
| Goal | Metric | Target |
...
## 5. Scope
### In Scope (v1)       ### Out of Scope
...
## 6. Users & Personas
...
## 7. Functional Requirements
| ID    | Requirement | Priority  |
...
## 8. User Stories
### US-01: Create Experiment
As a Data Analyst, I want to...
Acceptance Criteria:
  - [ ] ...
...
## 9. Edge Cases
## 10. Technical Constraints
## 11. Dependencies
## 12. Assumptions
## 13. Open Questions
  - [ ] Who approves an experiment before it goes live?
```

---

## Files in This Folder

### `schemas.py`

Defines every data model using **Pydantic v2**. Every PRD is validated against these
before saving. If a field is wrong type or missing, `save_prd` returns an error.

#### Enums

| Enum | Values |
|------|--------|
| `PRDType` | `Feature`, `Bug Fix`, `Spike`, `Enhancement`, `Tech Debt` |
| `PRDStatus` | `Draft`, `In Review`, `Approved` |
| `Priority` | `Must Have`, `Should Have`, `Nice to Have` |

#### Models

**`Stakeholder`**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | Yes | Stakeholder name or role |
| `role` | str | Yes | e.g. Product Owner, Dev Lead, QA |
| `email` | str | No | Contact email |

**`Goal`**
| Field | Type | Description |
|-------|------|-------------|
| `goal` | str | What we want to achieve |
| `metric` | str | How we measure it |
| `target` | str | The quantified success bar |

**`Persona`**
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Persona label, e.g. "Data Analyst" |
| `description` | str | Who they are and what they do |
| `key_need` | str | The primary thing they need from this product |

**`FunctionalRequirement`**
| Field | Type | Description |
|-------|------|-------------|
| `id` | str | e.g. FR-01, FR-02 |
| `requirement` | str | What the system must do |
| `priority` | Priority | MoSCoW value |

**`AcceptanceCriterion`**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `criterion` | str | — | A single testable condition |
| `met` | bool | False | Whether it has been verified |

**`UserStory`**
| Field | Type | Description |
|-------|------|-------------|
| `id` | str | e.g. US-01 |
| `title` | str | Short story title |
| `as_a` | str | The persona taking the action |
| `i_want_to` | str | The action they want to perform |
| `so_that` | str | The benefit they get |
| `acceptance_criteria` | list[AcceptanceCriterion] | Min 3 required |
| `priority` | Priority | MoSCoW value |
| `story_points` | int (1, 2, 3, 5, 8, 13) | Fibonacci only — schema enforced, non-Fibonacci values are rejected |
| `labels` | list[str] | e.g. `["backend", "auth"]` |

**`EdgeCase`**
| Field | Type | Description |
|-------|------|-------------|
| `scenario` | str | The boundary or failure condition |
| `expected_behaviour` | str | What the system should do |

**`PRDDocument`** — root model
| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Product / feature name |
| `version` | str | Defaults to `"1.0"` |
| `date` | str | YYYY-MM-DD |
| `status` | PRDStatus | Defaults to `Draft` |
| `prd_type` | PRDType | Feature / Bug Fix / Spike / Enhancement / Tech Debt |
| `author` | str | Defaults to `"AI Requirement Agent"` |
| `stakeholders` | list[Stakeholder] | |
| `problem_statement` | str | Core problem being solved |
| `business_value` | str | Revenue / cost / risk / compliance impact |
| `goals` | list[Goal] | Min 1 measurable goal |
| `in_scope` | list[str] | What v1 includes |
| `out_of_scope` | list[str] | What is explicitly excluded |
| `personas` | list[Persona] | |
| `functional_requirements` | list[FunctionalRequirement] | Min 3 |
| `user_stories` | list[UserStory] | Min 3, each with ≥3 ACs |
| `edge_cases` | list[EdgeCase] | Min 2 |
| `technical_constraints` | list[str] | Stack, infra, compliance, budget |
| `dependencies` | list[str] | External teams, systems, APIs |
| `assumptions` | list[str] | Things assumed true before building |
| `open_questions` | list[str] | Unresolved items for pre-dev resolution |

---

### `tools.py`

Five tools decorated with `@tool` (LangChain). Each tool's docstring becomes the
description the LLM uses to decide when to call it.

#### `get_current_date()`
- **Called:** Before generating the PRD
- **Does:** Returns today's date as `YYYY-MM-DD`
- **Why:** Populates the `date` field in PRDDocument automatically

---

#### `read_input_file(filepath: str)`
- **Called:** When the user provides a file path
- **Does:**
  1. Detects file type from extension
  2. Routes to the correct reader (`pypdf` / `python-docx` / `pandas` / plain text)
  3. Truncates content >32000 chars to avoid context overflow
  4. Returns extracted text with an instruction telling the agent to map content to PRD fields before asking follow-up questions
- **Supported types:**

| Extension | Library used | What is extracted |
|-----------|-------------|-------------------|
| `.pdf` | `pypdf` | Full text from all pages |
| `.docx` | `python-docx` | Paragraphs + all table cell text |
| `.csv` | `pandas` | Column names + first 20 rows |
| `.txt` / `.md` | built-in | Raw text (Teams exports, plain descriptions, email threads) |

- **Error handling:** Returns a JSON error with a helpful hint if file not found or type unsupported

---

#### `list_existing_prds()`
- **Called:** On agent startup, always
- **Does:** Scans `output/` for `.json` files and returns a list with:
  - filename, title, version, status, prd_type, last modified date
- **Why:** Lets the user choose to revise instead of starting fresh

---

#### `load_prd(filename: str)`
- **Called:** When user says they want to revise an existing PRD
- **Does:** Reads the full `.json` file from `output/` and returns its content
- **Why:** Agent can present a summary and ask targeted revision questions

---

#### `save_prd(prd_json: str)`
- **Called:** After explicit user confirmation ("yes", "save it", "looks good")
- **Does:**
  1. Parses the JSON string
  2. Validates it against `PRDDocument` schema using Pydantic
  3. If validation fails → returns an error (nothing is written)
  4. If valid → writes both `.json` and `.md` to `output/`
- **File naming:** `YYYYMMDD_HHMMSS_<title>_v<version>.json / .md`
- **Returns:** Paths to both saved files, story count, requirement count

---

### `agent.py`

Assembles and returns the LangChain `AgentExecutor`. Everything runs through here.

#### Components

**LLM — `ChatOpenAI`**
| Setting | Value | Reason |
|---------|-------|--------|
| `base_url` | `ASIMOV_BASE_URL` from `.env` | Points to your API gateway |
| `api_key` | `ASIMOV_API_KEY` from `.env` | Authentication |
| `model` | `ASIMOV_MODEL` (default: `openai/gpt-5-chat`) | Model selection |
| `temperature` | `0.2` | Low randomness — consistent, structured output |
| `http_client` | `httpx.Client(verify=False)` | Disables SSL verification for internal gateway |

**Prompt — `ChatPromptTemplate`**

Built from 4 message slots in order:
```
1. system          → full system prompt (agent behaviour, modes, rules)
2. chat_history    → MessagesPlaceholder — injected from memory
3. human           → {input} — current user message
4. agent_scratchpad → MessagesPlaceholder — tool call results injected here
```

**Memory — `ConversationBufferMemory`**
- `memory_key = "chat_history"` — injects history into the prompt slot above
- `return_messages = True` — stores as message objects (not string)
- Retains the full conversation — agent never forgets what you said 10 messages ago

**Agent — `create_tool_calling_agent`**
- Uses the model's native tool-calling API
- No manual parsing or regex — the LLM calls tools by structured JSON

**Executor — `AgentExecutor`**
| Setting | Value | Reason |
|---------|-------|--------|
| `verbose` | `True` | Prints tool call names in terminal for transparency |
| `handle_parsing_errors` | `True` | Recovers gracefully if LLM output is malformed |
| `max_iterations` | `25` | Prevents infinite loops on complex extractions |

#### `build_agent()` function
- Loads `.env` from `../.env`
- Instantiates all components above
- Returns a ready-to-use `AgentExecutor`

---

### `main.py`

CLI entrypoint. Runs the agent in an interactive terminal loop.

#### What it does step by step

| Step | Code | What happens |
|------|------|-------------|
| 1 | `print_banner()` | Prints the cyan bordered agent banner using `Rich` |
| 2 | `build_agent()` | Initialises LLM, prompt, memory, executor |
| 3 | `executor.invoke({"input": "Hello..."})` | Agent's opening turn — calls `list_existing_prds`, greets user |
| 4 | `console.input(...)` | Reads user input from terminal |
| 5 | `executor.invoke({"input": user_input})` | Sends to agent, prints response |
| 6 | Loop continues until `quit` / `exit` / `Ctrl+C` | Clean exit |

#### Error handling
- If `build_agent()` fails (missing env vars, network error) → prints error and exits
- If any `executor.invoke()` fails → prints error and continues the loop (agent doesn't crash)
- `EOFError` and `KeyboardInterrupt` both handled cleanly

#### Dependencies
- `rich` — coloured terminal output (`Console`, `Panel`, `Text`)
- `agent.py` → `build_agent()`
