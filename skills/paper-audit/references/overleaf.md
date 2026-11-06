# Working With Overleaf

Used by add-results and paper-audit when the paper is on Overleaf.

## Access

Overleaf projects can be cloned with git: `git clone https://git.overleaf.com/<project-id>`, where the project ID is the last part of the project URL. Authentication uses the username `git` and an Overleaf access token as the password (Overleaf: Account Settings, Git integration).

**Recommend storing the token once in the system credential store**, so it never appears in the chat or in files. Ask the user to run the commands below **in their own terminal, not through the agent**, replacing `<TOKEN>`:

macOS (Keychain):
```
git config --global credential.helper osxkeychain
printf 'protocol=https\nhost=git.overleaf.com\nusername=git\npassword=<TOKEN>\n' | git credential-osxkeychain store
```

Linux: `git config --global credential.helper libsecret` (or `store`, which keeps it in a plain file, `~/.git-credentials`), then clone once and enter the token when asked. Windows: Git Credential Manager, which comes with Git for Windows, asks once and stores it.

If the user pastes a token into the chat anyway, use it only for the clone, then run `git remote set-url origin https://git.overleaf.com/<project-id>` so the token is not left in `.git/config`. Never write it to any other file. Remind the user that it stays in the chat history and that they can revoke it in Overleaf.

## Checking the stored credential

Check only whether an entry exists, never print it: `printf 'protocol=https\nhost=git.overleaf.com\n\n' | git credential-osxkeychain get >/dev/null && echo found`. The helper's output contains the token more than once (for example in a `state[]` line), so masking one line is not enough.

If Overleaf answers `403`, the token is revoked, expired or lacks access. Do not retry in a loop. Stop, tell the user, and ask them to store a new token in their own terminal (erase the old entry first with `git credential-osxkeychain erase`).

A push that shows no progress for more than two minutes may still have reached Overleaf. Stop it, run `git fetch`, and compare **content**, not commit IDs: `git diff --stat HEAD origin/<branch>`. Overleaf rewrites pushed commits as "Update on Overleaf." with a new ID and the token owner's name, so a new remote commit can be your own push. If the diff is empty, the push succeeded; do not push again. If the remote has other changes, show them to the user before merging.

## Working copy

Clone into a new folder outside the code repository (for example a temp folder) and tell the user where it is. Before reading, run `git log -1` to show the date of the last Overleaf change. Before pushing, `git pull` to pick up co-authors' edits made in the meantime, and stop if there are conflicts.

Pushing follows the skill's rule: ask first, name the project and branch, and push only after an explicit yes. Commit messages contain no AI attribution (no `Co-Authored-By` for an AI). Overleaf shows pushed changes to all co-authors immediately.
