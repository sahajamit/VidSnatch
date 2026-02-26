Perform a version bump and release for the VidSnatch project.

## Steps

1. **Read the current version** from `pyproject.toml` (the `version = "X.Y.Z"` line).

2. **Determine the new version**: increment the patch number by 1 (e.g. `0.1.3` → `0.1.4`). If the user has passed an argument to this command (e.g. `/release minor` or `/release 0.2.0`), interpret it:
   - `major` → bump major, reset minor and patch to 0
   - `minor` → bump minor, reset patch to 0
   - `patch` (default, no argument) → bump patch only
   - An explicit version string like `1.2.3` → use it as-is

3. **Update `pyproject.toml`**: replace the old version string with the new one.

4. **Confirm with the user** — show the old → new version and ask for approval before making any git changes.

5. **After approval**, run these git commands in order:
   a. `git add pyproject.toml`
   b. `git commit -m "bump version to <new_version>"`
   c. `git push origin main`
   d. `git tag v<new_version>`
   e. `git push origin v<new_version>`

6. **Report** the tag that was pushed and remind the user that the GitHub Action will now build and publish `vidsnatch-<new_version>` to PyPI.
