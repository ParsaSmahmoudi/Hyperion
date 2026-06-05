# Contributing to Hyperion

First off, thank you for considering contributing to Hyperion! 🎉

Hyperion is an open-source project and we welcome contributions of all kinds:
- 🐛 Bug reports
- 💡 Feature requests
- 📝 Documentation improvements
- 🔧 Code contributions
- 🧪 New tests
- 🎨 UI/UX improvements

## Code of Conduct

By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

Found a bug? Please open an issue with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, OS, etc.)
- Minimal code example

### Suggesting Features

Have an idea? Open an issue with the `enhancement` label and describe:
- The problem it solves
- Your proposed solution
- Any alternatives you've considered

### Pull Requests

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/amazing-thing`
3. **Make your changes**:
   - Write code that follows the existing style
   - Add tests for new functionality
   - Update documentation as needed
4. **Run tests**: `pytest`
5. **Commit**: `git commit -m "Add amazing thing"`
6. **Push**: `git push origin feature/amazing-thing`
7. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/ParsaSmahmoudi/hyperion.git
cd hyperion

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=hyperion --cov-report=html
```

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for formatting: `black hyperion/`
- Use [mypy](https://mypy.readthedocs.io/) for type checking
- Add docstrings to all public functions and classes
- Keep functions small and focused

## Project Structure

```
hyperion/
├── core/              # Core reasoning modules
│   ├── hyperion.py    # Main engine
│   ├── decomposer.py  # Problem decomposition
│   ├── explorer.py    # Multi-path exploration
│   ├── reasoner.py    # Deep reasoning
│   ├── critic.py      # Self-critique
│   ├── synthesizer.py # Solution synthesis
│   ├── verifier.py    # Verification
│   ├── reflector.py   # Meta-reflection
│   ├── searcher.py    # Deep knowledge search
│   ├── expander.py    # Context expansion
│   ├── memory.py      # Long-term memory
│   └── tools.py       # Tool use system
├── models/            # LLM backends
│   ├── async_backend.py
│   ├── backends.py
│   └── router.py
├── prompts/           # Prompt templates
├── visual/            # Display & web UI
├── tests/             # Test suite
├── examples/          # Usage examples
├── config.py
├── __main__.py        # CLI entry point
└── server.py          # Web server
```

## Adding New Tools

```python
from hyperion.core.tools import Tool, ToolRegistry

class MyTool(Tool):
    name = "my_tool"
    description = "What it does"
    parameters = {"arg": "Description"}
    
    def run(self, arg: str) -> str:
        return f"Result: {arg}"

# In your code:
tools = ToolRegistry()
tools.register(MyTool())
```

## Adding New Reasoning Modules

1. Create `hyperion/core/my_module.py`
2. Subclass the pattern used by other modules
3. Use `AsyncLLM` for LLM calls
4. Add tests in `tests/test_my_module.py`
5. Document in README

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue with the `question` label or join our discussions!

Thank you for making Hyperion better! 🚀
