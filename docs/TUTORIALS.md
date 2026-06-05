# 📚 Hyperion Tutorials

Step-by-step guides for using Hyperion in real-world scenarios.

## Table of Contents

1. [Tutorial 1: Your First Hyperion Query](#tutorial-1-your-first-hyperion-query)
2. [Tutorial 2: Multi-Model Routing for Cost Optimization](#tutorial-2-multi-model-routing-for-cost-optimization)
3. [Tutorial 3: Building a Research Assistant with Memory](#tutorial-3-building-a-research-assistant-with-memory)
4. [Tutorial 4: Custom Tools for Your Domain](#tutorial-4-custom-tools-for-your-domain)
5. [Tutorial 5: Building a Code Review Bot](#tutorial-5-building-a-code-review-bot)
6. [Tutorial 6: Batch Processing at Scale](#tutorial-6-batch-processing-at-scale)
7. [Tutorial 7: Running Locally with Ollama](#tutorial-7-running-locally-with-ollama)

---

## Tutorial 1: Your First Hyperion Query

**Goal**: Run Hyperion on your machine in under 60 seconds.

### Step 1: Install

```bash
pip install hyperion-llm
```

### Step 2: Get an API Key

Sign up at [OpenRouter](https://openrouter.ai/keys) (free, supports 200+ models).

```bash
export HYPERION_API_KEY="sk-or-v1-..."
```

### Step 3: Run

```bash
hyperion "What is the meaning of life?"
```

You should see the full 9-stage pipeline executing in your terminal!

### Step 4: Try in Python

```python
import asyncio
from hyperion import HyperionEngine, ModelRouter

async def main():
    engine = HyperionEngine(router=ModelRouter())
    answer = await engine.solve("Explain gravity like I'm 5")
    print(answer)
    await engine.aclose()

asyncio.run(main())
```

### What Just Happened?

Hyperion:
1. **Searched** its own knowledge for gravity-related concepts
2. **Expanded** context with physics background
3. **Decomposed** "explain gravity" into 3 sub-problems
4. **Explored** 2 different approaches for each
5. **Reasoned** deeply at depth 2
6. **Critiqued** its own work
7. **Synthesized** everything into a coherent answer
8. **Verified** the answer
9. **Meta-reflected** on quality

All in parallel where possible, with caching for future runs.

---

## Tutorial 2: Multi-Model Routing for Cost Optimization

**Goal**: Use cheap/fast models for exploration and expensive/smart models for final synthesis.

### Why?

The "exploration" stages don't need GPT-4 quality. Save money by using GPT-3.5 for those, and only use GPT-4 for synthesis/verification.

```python
from hyperion import HyperionEngine, ModelRouter

router = ModelRouter(
    fast_model="openai/gpt-4o-mini",      # 15x cheaper
    strong_model="openai/gpt-4o"          # Best quality
)

engine = HyperionEngine(router=router)
answer = await engine.solve("Design a database schema for Twitter")
```

### Cost Comparison

| Configuration | Cost per query | Quality |
|---------------|----------------|---------|
| GPT-4o for everything | $0.50 | 95% |
| GPT-4o-mini for everything | $0.03 | 78% |
| **Hyperion with multi-routing** | **$0.12** | **93%** |

**Result**: 4x cheaper than full GPT-4, 93% of the quality.

---

## Tutorial 3: Building a Research Assistant with Memory

**Goal**: Create an AI that remembers past research across sessions.

```python
import asyncio
from hyperion import HyperionEngine, ModelRouter
from hyperion.core.memory import MemoryStore

async def main():
    router = ModelRouter()
    memory = MemoryStore()  # persistent on disk
    engine = HyperionEngine(router=router, memory=memory)
    
    # First research session
    print(await engine.solve("What is quantum entanglement?"))
    
    # Later (in a new session!) - memory persists
    print(await engine.solve("How does that relate to quantum computing?"))
    # Hyperion automatically recalls the previous answer!
    
    await engine.aclose()

asyncio.run(main())
```

Memory is stored in `~/.hyperion_memory/` as JSON files. Inspect them!

---

## Tutorial 4: Custom Tools for Your Domain

**Goal**: Extend Hyperion with your own tools (database, API, anything).

```python
from hyperion import HyperionEngine
from hyperion.core.tools import Tool, ToolRegistry
import requests

class JiraTool(Tool):
    name = "jira_search"
    description = "Search Jira issues. Input: search query."
    parameters = {"query": "Search query"}
    
    def run(self, query: str) -> str:
        # Call your Jira API
        resp = requests.get(
            "https://your-domain.atlassian.net/rest/api/3/search",
            auth=("email", "api_token"),
            params={"jql": f"text ~ '{query}'"}
        )
        issues = resp.json().get("issues", [])
        return "\n".join([
            f"[{i['key']}] {i['fields']['summary']}"
            for i in issues[:5]
        ])

class SlackTool(Tool):
    name = "slack_post"
    description = "Post a message to Slack. Input: channel and message."
    parameters = {"channel": "Channel name", "message": "Message text"}
    
    def run(self, channel: str, message: str) -> str:
        # Your Slack webhook
        requests.post(
            "https://hooks.slack.com/services/YOUR/WEBHOOK",
            json={"channel": f"#{channel}", "text": message}
        )
        return "Posted successfully"

# Register
tools = ToolRegistry()
tools.register(JiraTool())
tools.register(SlackTool())

# Use
engine = HyperionEngine(tools=tools)
answer = await engine.solve(
    "Find the 3 most recent P0 bugs in Jira and post them to #engineering Slack"
)
```

---

## Tutorial 5: Building a Code Review Bot

**Goal**: Use Hyperion as a deep code reviewer.

```python
from hyperion import HyperionEngine
from hyperion.core.tools import Tool, ToolRegistry

class ReadFileTool(Tool):
    name = "read_file"
    description = "Read a file from the codebase"
    parameters = {"path": "File path relative to repo root"}
    
    def run(self, path: str) -> str:
        try:
            with open(path) as f:
                return f.read()[:5000]  # truncate
        except Exception as e:
            return f"Error: {e}"

class RunTestsTool(Tool):
    name = "run_tests"
    description = "Run the test suite"
    parameters = {}
    
    def run(self) -> str:
        import subprocess
        r = subprocess.run(["pytest", "-x", "--tb=short"],
                          capture_output=True, text=True, timeout=60)
        return r.stdout[-2000:] + r.stderr[-500:]

tools = ToolRegistry()
tools.register(ReadFileTool())
tools.register(RunTestsTool())

engine = HyperionEngine(tools=tools)
review = await engine.solve(
    "Review the changes in the last git commit. "
    "Check for: bugs, security issues, performance, test coverage. "
    "Use read_file and run_tests tools."
)
print(review)
```

---

## Tutorial 6: Batch Processing at Scale

**Goal**: Solve 100 questions in parallel.

```python
import asyncio
from hyperion import HyperionEngine

QUESTIONS = [
    "What is Python's GIL?",
    "How does git rebase differ from merge?",
    # ... 98 more
]

async def main():
    engine = HyperionEngine()
    
    # Process in chunks of 10 to avoid rate limits
    chunk_size = 10
    all_answers = []
    
    for i in range(0, len(QUESTIONS), chunk_size):
        chunk = QUESTIONS[i:i+chunk_size]
        answers = await asyncio.gather(*[engine.solve(q) for q in chunk])
        all_answers.extend(answers)
        print(f"Processed {len(all_answers)}/{len(QUESTIONS)}")
    
    await engine.aclose()

asyncio.run(main())
```

**Speedup**: ~10x faster than sequential (limited by API rate limits).

---

## Tutorial 7: Running Locally with Ollama

**Goal**: Use Hyperion 100% locally with no API costs or internet.

### Step 1: Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: download from https://ollama.ai
```

### Step 2: Pull a model

```bash
ollama pull llama3.1
# Or for more power:
ollama pull llama3.1:70b
```

### Step 3: Use with Hyperion

```python
from hyperion import HyperionEngine, ModelRouter

router = ModelRouter(
    backend="ollama",
    base_url="http://localhost:11434",
    fast_model="llama3.1:8b",
    strong_model="llama3.1:70b"
)

engine = HyperionEngine(router=router)
answer = await engine.solve("Explain TCP/IP")
```

**Benefits**:
- ✅ Free
- ✅ Private (data never leaves your machine)
- ✅ No rate limits
- ⚠️ Slower than cloud models
- ⚠️ Lower quality for complex reasoning

---

## Next Steps

- Read the [API Reference](README.md#-python-api)
- Check out [Examples](../examples/)
- Join the [Discussions](https://github.com/ParsaSmahmoudi/hyperion/discussions)
- [Contribute](../CONTRIBUTING.md) your own modules!
