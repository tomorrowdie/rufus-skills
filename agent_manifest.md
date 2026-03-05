# Multi-Agent Collaboration Manifest

## 1. Project Management
* **Project Manager:** Gemini
* **Role:** Assigns tasks, reviews code, resolves integration conflicts, and tracks overall progress. All agents must report completion or blockers back to the PM.

## 2. Agent Departments & Boundaries
**Agent 1: Claude (VS Code) - Core Architecture & Backend**
* **Scope:** Server-side logic, database models, authentication, and system architecture.
* **Boundary:** Do not alter frontend components or automation scripts. Expose clean API endpoints for the Builder and Integrator.

**Agent 2: Codex - Frontend & Component Engineering**
* **Scope:** UI/UX, client-side rendering, styling, and component assembly.
* **Boundary:** Do not alter backend logic. Consume APIs provided by the Architect. Focus strictly on user-facing directories.

**Agent 3: Antigravity - Integration & Workflow Automation**
* **Scope:** External API connections, background workers, CRON jobs, and data routing pipelines.
* **Boundary:** Do not alter core app logic or UI. Build standalone automation modules that plug into the main system.

## 3. Rules of Engagement
1. **Isolation:** Only write code within your assigned domain directories. 
2. **Communication:** Use clear, documented interfaces/APIs to pass data between departments.
3. **Reporting:** When a task is complete, generate a brief summary of changes, endpoints created, and dependencies required, to be submitted to the Project Manager (Gemini).
4. **Conflict:** If a task requires modifying another agent's domain, halt and request a cross-department sync via the Project Manager.