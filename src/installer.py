"""
VidSnatch skill installer - copies SKILL.md into LLM tool directories.
"""

import os
import shutil
from pathlib import Path


def _skill_source() -> Path:
    """Return the path to the bundled SKILL.md."""
    # When installed as a package the skills dir is alongside src/
    candidate = Path(__file__).parent.parent / "skills" / "vidsnatch" / "SKILL.md"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"Could not locate SKILL.md (looked at {candidate}). "
        "Re-install vidsnatch or run from the project root."
    )


def install_skills():
    """Install SKILL.md into all detected LLM tool skill directories."""
    try:
        source = _skill_source()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    skill_content = source.read_text(encoding="utf-8")
    home = Path.home()
    installed = []
    skipped = []

    # ── Claude Code ──────────────────────────────────────────────────────────
    claude_target = home / ".claude" / "skills" / "vidsnatch" / "SKILL.md"
    claude_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, claude_target)
    installed.append(f"Claude Code  →  {claude_target}")

    # ── Cursor ───────────────────────────────────────────────────────────────
    cursor_rules_dir = home / ".cursor" / "rules"
    if cursor_rules_dir.exists():
        cursor_target = cursor_rules_dir / "vidsnatch.md"
        shutil.copy2(source, cursor_target)
        installed.append(f"Cursor       →  {cursor_target}")
    else:
        skipped.append(
            "Cursor (~/.cursor/rules not found — open Cursor at least once to create it)"
        )

    # ── OpenClaw ─────────────────────────────────────────────────────────────
    openclaw_target = home / ".openclaw" / "workspace" / "skills" / "vidsnatch" / "SKILL.md"
    openclaw_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, openclaw_target)
    installed.append(f"OpenClaw        →  {openclaw_target}")

    # ── Copilot (standalone) ─────────────────────────────────────────────────
    copilot_skills_target = home / ".copilot" / "skills" / "vidsnatch" / "SKILL.md"
    copilot_skills_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, copilot_skills_target)
    installed.append(f"Copilot         →  {copilot_skills_target}")

    # ── GitHub Copilot (append to .github/copilot-instructions.md) ───────────
    copilot_dir = Path(".github")
    copilot_target = copilot_dir / "copilot-instructions.md"
    marker = "<!-- vidsnatch-skill -->"
    if copilot_dir.exists():
        if copilot_target.exists():
            existing = copilot_target.read_text(encoding="utf-8")
            if marker in existing:
                # Already present — overwrite block
                before, _, after = existing.partition(marker)
                _, _, tail = after.partition(marker)
                new_content = before + marker + "\n" + skill_content + "\n" + marker + tail
            else:
                new_content = existing + f"\n\n{marker}\n{skill_content}\n{marker}\n"
        else:
            new_content = f"{marker}\n{skill_content}\n{marker}\n"
        copilot_target.write_text(new_content, encoding="utf-8")
        installed.append(f"GitHub Copilot  →  {copilot_target.resolve()}")
    else:
        skipped.append(
            "GitHub Copilot (.github/ not found — run from the root of a git repo)"
        )

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\nVidSnatch skills installed:")
    for msg in installed:
        print(f"  ✓  {msg}")

    if skipped:
        print("\nSkipped (target not detected):")
        for msg in skipped:
            print(f"  -  {msg}")

    if not installed:
        print("Nothing was installed.")
