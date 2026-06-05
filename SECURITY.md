# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it privately:

- **Email**: security@hyperion-llm.dev
- **GitHub**: Open a private security advisory at https://github.com/ParsaSmahmoudi/hyperion/security/advisories/new

**Please do NOT open a public GitHub issue for security vulnerabilities.**

We will respond within 48 hours and work with you to understand and address the issue.

## Security Considerations

Hyperion executes LLM-generated code in certain cases (via the `code_exec` tool). This is sandboxed but:

- Code execution is time-limited (10 seconds)
- Code runs in a subprocess (separate from main process)
- The `code_exec` tool is **disabled by default** in many configurations
- We recommend using `--no-tools` flag in production unless you trust your prompts

### Best Practices

1. **Never expose Hyperion directly to untrusted users** without proper input validation
2. **Use environment variables** for API keys, never hardcode them
3. **Set timeouts** for all operations
4. **Monitor API usage** to detect abuse
5. **Use the `verify` stage** to catch harmful outputs
6. **Review custom tools** carefully before registering them
7. **Run with minimal permissions** in production

### Sandboxing

The `code_exec` tool:
- Runs Python code in a subprocess with a 10-second timeout
- Cannot access the network (uses subprocess with limited env)
- Cannot access files outside the temp directory
- Returns truncated output (max 2000 chars)

This provides reasonable isolation but is **not a complete sandbox**. Do not use it with untrusted code in security-sensitive contexts.

## Disclosure Policy

When we receive a security report, we will:

1. Confirm the issue and determine its severity
2. Develop a fix
3. Release a security patch
4. Publicly disclose the vulnerability after the fix is available
5. Credit the reporter (if they wish)

Thank you for helping keep Hyperion and its users safe!
