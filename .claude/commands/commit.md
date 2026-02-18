Stage, commit, and push all changes with a proper conventional commit message.

Steps:
1. Run `git status` and `git diff --staged` to understand all changes
2. Determine the commit type: feat, fix, refactor, test, docs, chore
3. Determine the scope (module name) if applicable
4. Write a concise, descriptive commit message following conventional commits format
5. Stage relevant files (NOT `.env`, credentials, or large binaries)
6. Commit with the message
7. Push to origin
8. Report what was committed
