# ChatGPT 3 — migration status

## Status: PARTIAL — binary transfer is blocked

### Completed
- Assigned this independent workspace as `chatgpt-3`; `chatgpt-1` already exists and `chatgpt-2` is reserved.
- Copied all seven UTF-8 files from the legacy `CHATGPT/` directory into `legacy-chatgpt/`.
- Created the required workspace documentation.
- Isolated all changes on branch `migration/chatgpt-3-pio-co-ai-zx81`; `main` and all other model workspaces are untouched.

### Not completed
- The 225,941-byte CleanDisplay `.t81` and 35,961-byte IYBootstrap ZIP have not been transferred into GitHub.
- The GitHub write action available here accepts textual content or base64 strings but has no direct local-file upload input. A local ZIP was prepared and hashed, but it is not in this branch. I will not claim binary migration success without the actual bytes being committed.

### Required to finish
Add `PICOAI_ChatGPT3_Continuity_Bundle.zip` to `chatgpt/zx-81/chatgpt-3/artifacts/` using a byte-preserving Git upload route. Then verify the committed Git blob and the extracted inner-file SHA-256 values against `MIGRATION_MANIFEST.md`.

### Historical test status
The shared conversation reports that the final storage layout compiled and passed nine checks, and that 15 cassette blocks / 24 screen rows were checked. Those checks have not been independently repeated here. A compile or static check is not an emulator or real-hardware test.
