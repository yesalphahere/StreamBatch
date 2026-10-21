# StreamBatch - Security Policy & Vulnerability Audit

This document outlines the security architecture, trust boundaries, threat models, and mitigation strategies implemented in StreamBatch. As a project built by an aspiring penetration tester and security-minded software engineer, defensive architecture is treated as a core design priority.

---

## 1. Security Boundaries & Trust Architecture

```
   [ UNTRUSTED WEB CONTENT ]
               |
               v (Browser Extension)
   +--------------------------------------------------------+
   | TRUST BOUNDARY: Input Sanitization & Scheme Validation |
   +--------------------------------------------------------+
               |
               | (Loopback HTTP: 127.0.0.1:9654)
               v
   +--------------------------------------------------------+
   | StreamBatch Core Desktop Engine (User Execution Level) |
   | - Restricted Subprocess Argument Lists                 |
   | - NTFS Path & Filename Character Stripping             |
   | - SQLite Prepared SQL Queries                          |
   +--------------------------------------------------------+
```

---

## 2. Threat Modeling & Mitigations

### A. URL Injection & Protocol Smuggling
- **Threat**: Malicious inputs containing non-HTTP protocols (e.g., `file:///C:/Windows/...`, `gopher://`, `javascript:`, or SMB shares `\\attacker\share`) could lead to local file inclusion (LFI), unauthorized relay, or credential theft via NTLM hashes.
- **Mitigation**: Strict scheme enforcement is applied at both the IPC server layer (`core/api_server.py`) and the UI input handler (`ui/add_dialog.py`). Only URLs strictly beginning with `http://` or `https://` are processed. All other schemes are rejected with `400 Bad Request` or an input warning.

### B. Subprocess Execution & Command Injection
- **Threat**: Passing untrusted media titles or user-supplied strings directly into shell command strings can result in arbitrary command execution.
- **Mitigation**:
  - All external process invocations (`subprocess.run`, `subprocess.Popen`) use explicit argument lists rather than raw shell strings (`shell=False`).
  - No user-controlled strings are evaluated via `eval()`, `exec()`, or passed to `cmd.exe` / `powershell.exe` command lines.

### C. Path Traversal & File Overwrite
- **Threat**: Malicious media streams could advertise names containing path traversal sequences (e.g. `../../../../Windows/System32/evil.dll`).
- **Mitigation**:
  - `yt-dlp`'s `windowsfilenames: True` setting is enforced, automatically stripping NTFS reserved characters (`\ / : * ? " < > |`) and resolving output files strictly within the configured download directory.
  - Target destination folders are verified to exist before starting any worker job.

### D. Local IPC & CORS Considerations
- **Current State**: The local HTTP loopback server binds exclusively to `127.0.0.1:9654`. It is not bound to `0.0.0.0` and cannot be accessed across the local area network.
- **Cross-Origin Requests (CORS)**: The server currently returns `Access-Control-Allow-Origin: *` to enable communication from browser extensions.
- **Hardening Recommendation for Multi-User Systems**: On shared workstations where untrusted web pages might attempt to probe `localhost:9654`, a shared authentication token generated at app launch and shared with the browser extension via Native Messaging should be implemented.

### E. SQL Injection
- **Threat**: Maliciously formatted track titles or URLs containing SQL escape characters (`'`, `"`, `--`).
- **Mitigation**: 100% of SQLite database interactions in `db/database.py` use parameterized queries with placeholder bindings (`?` and `:named_params`). No dynamic SQL string interpolation exists in the codebase.

---

## 3. Responsible Vulnerability Reporting

If you discover a security vulnerability or design flaw in StreamBatch:

1. **Do not open a public issue.**
2. Send an email with a proof of concept (PoC) and details to the repository maintainer.
3. Allow reasonable time for verification and patching before public disclosure.
