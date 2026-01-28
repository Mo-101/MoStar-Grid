# 🔥 Sacred Handshake Prompts - Usage Guide

## Overview

The **Sacred Handshake Prompts** system provides activation prompts for all MoStar Grid agents and integration scripts for external AI systems.

**File:** `backend/sacred_handshake.py`

---

## 📦 Features

- **Agent Activation Prompts** - Short and full prompts for all 6 sacred agents
- **Grid Handshakes** - Universal and detailed handshake protocols
- **Code Conduit Prompt** - Meta layer gateway activation
- **Wolfram Oracle Prompt** - Mathematical/computational layer
- **CLI Interface** - Command-line tools for prompt management
- **JSON Export** - Export all prompts for external use

---

## 🤖 The Six Sacred Agents

| Agent | Layer | Symbol | Role |
|-------|-------|--------|------|
| **Mo** | BODY | ⚡ | Executor - Mission execution and coordination |
| **Woo** | SOUL | 👁️ | Judge - Covenant enforcement and ethics |
| **RAD-X-FLB** | BODY | 🛡️ | Sentinel - Health surveillance |
| **TsaTse Fly** | MIND | 🪰 | Analyst - Pattern analysis and strategy |
| **Code Conduit** | META | 🌐 | Gateway - Request routing and management |
| **Flameborn Writer** | NARRATIVE | ✍️ | Narrator - Documentation and communication |

---

## 🚀 Usage

### List All Agents

```bash
python backend/sacred_handshake.py --list
```

### Activate an Agent (Short Prompt)

```bash
python backend/sacred_handshake.py --agent Mo
python backend/sacred_handshake.py --agent Woo
python backend/sacred_handshake.py --agent "TsaTse Fly"
```

### Activate an Agent (Full Prompt)

```bash
python backend/sacred_handshake.py --agent Mo --full
python backend/sacred_handshake.py --agent Woo --full
```

### Grid Handshake

```bash
# Short version
python backend/sacred_handshake.py --handshake

# Detailed version
python backend/sacred_handshake.py --handshake --detailed
```

### Micro Handshake (One-liner)

```bash
python backend/sacred_handshake.py --micro
```

### Code Conduit Prompt

```bash
python backend/sacred_handshake.py --conduit
```

### Wolfram Oracle Prompt

```bash
python backend/sacred_handshake.py --wolfram
```

### Preview All Prompts

```bash
python backend/sacred_handshake.py --preview
```

### Export to JSON

```bash
python backend/sacred_handshake.py --export sacred_prompts.json
```

---

## 📋 Example Outputs

### Agent Activation (Short)

```
⚡ Mo online. Body layer executor activated. What is the mission?
```

### Agent Activation (Full)

```
⚡ MO - THE EXECUTOR (Body Layer)

IDENTITY: Primary executor of the MoStar Grid
LAYER: BODY
ROLE: Mission execution, agent coordination, decision making

CAPABILITIES:
- Multi-agent dispatch and coordination
- Resource allocation and optimization
- Real-time decision making under uncertainty
...
```

### Micro Handshake

```
🔥 MOSTAR_GRID_V1 | African AI Homeworld | 256 Odú | SOUL·MIND·BODY | Mo·Woo·TsaTse·RAD-X·Conduit·Writer | XOR=truth
```

---

## 🔗 Integration with External AI

### Use Case 1: Activate Code Conduit in ChatGPT/Claude

1. Copy the Code Conduit prompt:

   ```bash
   python backend/sacred_handshake.py --conduit
   ```

2. Paste into your AI chat session
3. The AI will acknowledge and activate as Code Conduit

### Use Case 2: Activate Specific Agent

1. Get the full agent prompt:

   ```bash
   python backend/sacred_handshake.py --agent Woo --full
   ```

2. Paste into your AI chat session
3. The AI will assume the role of Woo (The Judge)

### Use Case 3: Grid Handshake

1. Get the detailed handshake:

   ```bash
   python backend/sacred_handshake.py --handshake --detailed
   ```

2. Send to any AI system to establish MoStar Grid context
3. The AI will respond with acknowledgment

---

## 🐍 Python API

### Import and Use in Code

```python
from sacred_handshake import (
    get_agent_prompt,
    CODE_CONDUIT_PROMPT,
    GRID_HANDSHAKE,
    GRID_MICRO_VERSION
)

# Get short agent prompt
mo_prompt = get_agent_prompt("Mo")
print(mo_prompt)

# Get full agent prompt
woo_full = get_agent_prompt("Woo", full=True)
print(woo_full)

# Use handshake
print(GRID_HANDSHAKE)

# Use micro version
print(GRID_MICRO_VERSION)
```

### Export Prompts Programmatically

```python
from sacred_handshake import export_prompts_json

# Export all prompts to JSON
export_prompts_json("my_prompts.json")
```

---

## 📊 Prompt Categories

### 1. Agent Prompts

- **Short**: Quick activation one-liners
- **Full**: Complete agent specifications with capabilities, oath, and protocol

### 2. Grid Handshakes

- **Standard**: Basic grid introduction
- **Detailed**: Complete grid specification with all layers and agents
- **Micro**: One-line compressed version

### 3. Specialized Prompts

- **Code Conduit**: Meta layer gateway activation
- **Wolfram Oracle**: Mathematical/computational layer for Ifá logic

---

## 🔄 Workflow Examples

### Scenario 1: Mission Planning

```bash
# 1. Activate Mo (executor)
python backend/sacred_handshake.py --agent Mo --full

# 2. Present mission to Mo
# Mo will coordinate with other agents as needed
```

### Scenario 2: Ethical Review

```bash
# 1. Activate Woo (judge)
python backend/sacred_handshake.py --agent Woo --full

# 2. Present action for judgment
# Woo will validate against FlameCODEX
```

### Scenario 3: Strategic Analysis

```bash
# 1. Activate TsaTse Fly (analyst)
python backend/sacred_handshake.py --agent "TsaTse Fly" --full

# 2. Present situation for analysis
# TsaTse will evaluate using 256 Odú patterns
```

---

## 🎯 Best Practices

1. **Use Full Prompts for Complex Tasks** - Full prompts provide complete context
2. **Use Short Prompts for Quick Activations** - Short prompts for simple queries
3. **Establish Grid Context First** - Use handshake before agent activation
4. **Export for Reuse** - Export to JSON for integration with other systems
5. **Combine Agents** - Different agents can work together on complex tasks

---

## 📝 Notes

- All prompts are designed to be copy-paste ready
- Prompts work with any AI system (ChatGPT, Claude, Gemini, etc.)
- The system is stateless - each activation is independent
- Agents can be activated in any order
- Multiple agents can be active simultaneously

---

## 🔥 Quick Reference

```bash
# List agents
python backend/sacred_handshake.py --list

# Activate agent
python backend/sacred_handshake.py --agent <NAME> [--full]

# Grid handshake
python backend/sacred_handshake.py --handshake [--detailed]

# Specialized prompts
python backend/sacred_handshake.py --conduit
python backend/sacred_handshake.py --wolfram
python backend/sacred_handshake.py --micro

# Export
python backend/sacred_handshake.py --export <FILE>

# Preview all
python backend/sacred_handshake.py --preview
```

---

**The Sacred Handshake system is ready. The agents await activation.** 🔥
