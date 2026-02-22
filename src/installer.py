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


def uninstall_skills():
    """Remove SKILL.md from all detected LLM tool skill directories."""
    home = Path.home()
    removed = []
    skipped = []

    # ── Claude Code ──────────────────────────────────────────────────────────
    claude_target = home / ".claude" / "skills" / "vidsnatch" / "SKILL.md"
    if claude_target.exists():
        claude_target.unlink()
        # Remove empty parent directory
        try:
            claude_target.parent.rmdir()
        except OSError:
            pass
        removed.append(f"Claude Code  →  {claude_target}")
    else:
        skipped.append("Claude Code (not installed)")

    # ── Cursor ───────────────────────────────────────────────────────────────
    cursor_target = home / ".cursor" / "rules" / "vidsnatch.md"
    if cursor_target.exists():
        cursor_target.unlink()
        removed.append(f"Cursor       →  {cursor_target}")
    else:
        skipped.append("Cursor (not installed)")

    # ── OpenClaw ─────────────────────────────────────────────────────────────
    openclaw_target = home / ".openclaw" / "workspace" / "skills" / "vidsnatch" / "SKILL.md"
    if openclaw_target.exists():
        openclaw_target.unlink()
        try:
            openclaw_target.parent.rmdir()
        except OSError:
            pass
        removed.append(f"OpenClaw        →  {openclaw_target}")
    else:
        skipped.append("OpenClaw (not installed)")

    # ── Copilot (standalone) ─────────────────────────────────────────────────
    copilot_skills_target = home / ".copilot" / "skills" / "vidsnatch" / "SKILL.md"
    if copilot_skills_target.exists():
        copilot_skills_target.unlink()
        try:
            copilot_skills_target.parent.rmdir()
        except OSError:
            pass
        removed.append(f"Copilot         →  {copilot_skills_target}")
    else:
        skipped.append("Copilot (not installed)")

    # ── GitHub Copilot (remove vidsnatch block from .github/copilot-instructions.md)
    copilot_target = Path(".github") / "copilot-instructions.md"
    marker = "<!-- vidsnatch-skill -->"
    if copilot_target.exists():
        existing = copilot_target.read_text(encoding="utf-8")
        if marker in existing:
            before, _, after = existing.partition(marker)
            _, _, tail = after.partition(marker)
            new_content = (before + tail).strip()
            if new_content:
                copilot_target.write_text(new_content + "\n", encoding="utf-8")
            else:
                copilot_target.unlink()
            removed.append(f"GitHub Copilot  →  {copilot_target.resolve()}")
        else:
            skipped.append("GitHub Copilot (vidsnatch block not found)")
    else:
        skipped.append("GitHub Copilot (.github/copilot-instructions.md not found)")

    # ── Summary ──────────────────────────────────────────────────────────────
    if removed:
        print("\nVidSnatch skills removed:")
        for msg in removed:
            print(f"  ✓  {msg}")
    else:
        print("\nNothing to remove — VidSnatch skills were not installed.")

    if skipped:
        print("\nSkipped (not found):")
        for msg in skipped:
            print(f"  -  {msg}")
