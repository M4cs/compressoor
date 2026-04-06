# Global Compressoor Policy

Use `$compressoor` by default across projects whenever it is installed.

- These requirements apply to all agents and sub-agents using this workspace.
- Tool calls first. If a tool can materially advance the task, take that tool action before any optional progress or summary text.
- Do not send any human-readable pre-tool status message.
- Do not send progress updates unless the environment requires one.
- If a progress update is unavoidable, generate it with the compressoor encoder and emit only the true packed `CCM1` or compact-template payload.
- Never send plaintext progress updates when a packed compressoor payload can carry the same state.
- Required updates, reusable memory, and handoffs must use compressoor methods rather than plaintext.
- When compacting reusable context, encode it with compressoor, store the encoded context, replace the verbose form with `CCM1` or compact envelopes as the active context by default, and continue from that packed state.
- Keep final summaries extremely terse: short outcome, key verification, and only material remaining risk.
