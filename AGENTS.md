# Project Instructions

- Communicate with the user in Czech.
- Write source code, variable names, comments, and technical documentation in English.
- The user is learning Python; explain steps clearly and accessibly.
- Before making substantial changes, explain their purpose first.
- Prefer a simple, maintainable architecture.
- Do not invent PVL API capabilities or behavior that have not been verified.
- Do not run `git commit` or `git push` without the user's explicit permission.
- After every significant change, perform an appropriate review or check and report the result.
- Follow the approved architecture in `PROJECT_CONTEXT.md`: fetch current PVL values only every 10 minutes and use Home Assistant Recorder for history.
- Do not add PVL history downloads or invent unverified PVL API behavior.
- Treat blank source fields as unavailable, never as zero.
- Keep the precipitation sensor free of forced updates; it shares the normal page request and should only create Recorder state changes when its value changes.
- Use the standard-library HTML parser unless a verified need for another dependency arises.
- Run the available parser tests and static checks after significant implementation changes. If Home Assistant runtime dependencies are unavailable, state that limitation clearly.
- Do not claim HACS publication readiness until the GitHub owner/repository placeholders and card distribution path have been resolved.
