---
name: review-security
description: Security audit for vulnerabilities, secrets, and unsafe patterns. Use before releases, after adding auth code, or when reviewing third-party integrations.
argument-hint: [--staged | --all]
---

# Review Security

Security audit for common vulnerabilities and unsafe patterns.

## Usage

```
/review-security              # Review context-related code
/review-security --staged     # Review staged changes
/review-security --all        # Full codebase audit (parallel agents)
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from recent conversation |
| `--staged` | Staged changes | `git diff --cached --name-only` |
| `--all` | Full codebase | Glob source files, parallel agents |

**Do NOT skip checks:**
- "This code is internal only" -- Internal code gets compromised too
- "This is just a prototype" -- Prototypes become production code
- "I already checked for the obvious issues" -- The non-obvious ones are the dangerous ones

## Workflow

1. **Determine scope** based on flags
2. **Review** (directly if ≤5 files, parallel agents if more)
3. **Check dependencies** for known vulnerabilities
4. **Report findings** by severity

## Security Checklist

### Injection (OWASP A03)

**SQL Injection:**
```javascript
// BAD: String concatenation
const query = `SELECT * FROM users WHERE id = ${userId}`;

// GOOD: Parameterized query
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);
```

**Command Injection:**
```javascript
// BAD: Unsanitized input to shell
exec(`ls ${userInput}`);

// GOOD: Use array form or escape
execFile('ls', [sanitizedPath]);
```

**XSS (Cross-Site Scripting):**
```javascript
// BAD: Direct HTML insertion
element.innerHTML = userContent;

// GOOD: Use textContent or sanitize
element.textContent = userContent;
// Or use DOMPurify for HTML
element.innerHTML = DOMPurify.sanitize(userContent);
```

### Broken Authentication (OWASP A07)

- [ ] Passwords hashed with bcrypt/argon2 (not MD5/SHA1)
- [ ] Rate limiting on login endpoints
- [ ] Session tokens are secure (HttpOnly, Secure, SameSite)
- [ ] No credentials in URLs or logs
- [ ] Account lockout after failed attempts

### Sensitive Data Exposure (OWASP A02)

**Hardcoded Secrets:**
```javascript
// BAD: Secrets in code
const apiKey = 'sk-1234567890abcdef';
const password = 'admin123';

// GOOD: Environment variables
const apiKey = process.env.API_KEY;
```

**Patterns to grep for:**
```
password\s*=\s*['"][^'"]+['"]
api[_-]?key\s*=\s*['"][^'"]+['"]
secret\s*=\s*['"][^'"]+['"]
token\s*=\s*['"][^'"]+['"]
Bearer\s+[A-Za-z0-9\-_]+
```

**Logging Sensitive Data:**
```javascript
// BAD: Logging credentials
console.log('User login:', { email, password });

// GOOD: Redact sensitive fields
console.log('User login:', { email, password: '[REDACTED]' });
```

### Security Misconfiguration (OWASP A05)

- [ ] Debug mode disabled in production
- [ ] No default/test credentials
- [ ] Error messages don't expose internals
- [ ] CORS properly configured (not `*` for sensitive APIs)
- [ ] Security headers set (CSP, X-Frame-Options, etc.)

**CORS Issues:**
```javascript
// BAD: Overly permissive
app.use(cors({ origin: '*' }));

// GOOD: Specific origins
app.use(cors({ origin: ['https://myapp.com'] }));
```

### Dependency Vulnerabilities

**Check commands by ecosystem:**
```bash
# Node.js
npm audit
npx audit-ci --critical

# Python
pip-audit
safety check

# Ruby
bundle audit

# Go
govulncheck ./...
```

Report any Critical or High severity vulnerabilities.

## Output Format

```markdown
## Security Review: {scope}

### Critical (fix immediately)
- {file}:{line} - {vulnerability type}: {description}
  **Fix:** {remediation}

### High Priority
- {file}:{line} - {issue}
  **Fix:** {remediation}

### Medium Priority
- {file} - {issue}

### Dependency Vulnerabilities
| Package | Severity | CVE | Fix Version |
|---------|----------|-----|-------------|
| {pkg} | Critical | CVE-XXXX-XXXX | {version} |

### Suggestions
- {improvement}
```

## Notes

- Focus on exploitable vulnerabilities, not theoretical risks
- Always provide remediation guidance
- For `--all`, use parallel agents per category for speed
- Check both source code and configuration files
- Dependency checks require package manager files (package.json, requirements.txt, etc.)
