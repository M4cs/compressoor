# Compressoor Workspace Policy

Use `$compressoor` by default in this workspace whenever it is installed.

- Tool calls first. If a tool can materially advance the task, take that tool action before any optional status text.
- Do not send a human-readable pre-tool progress message.
- Do not send progress updates unless the environment requires one.
- If a progress update is required, emit only the true encoder-produced `CCM1` or compact-envelope payload from `python3 skills/compressoor/scripts/pack_ccm.py`, not plaintext and not a hand-written packed-looking variant.
- Required updates, reusable handoffs, and stored memory must use compressoor methods rather than plaintext.
- When context will be reused, encode it with compressoor, store the encoded form, and treat `CCM1` or a compact envelope as the active context by default.
- Keep final summaries terse: outcome, key verification, material remaining risk only.
