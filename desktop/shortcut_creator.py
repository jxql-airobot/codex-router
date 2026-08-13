"""Create a Windows shortcut command without executing it."""

from __future__ import annotations


def build_shortcut_command(
    target: str,
    shortcut_path: str,
    arguments: str = "",
) -> str:
    return (
        f"powershell -NoProfile -Command \"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{shortcut_path}');"
        f"$s.TargetPath='{target}';$s.Arguments='{arguments}';$s.Save()\""
    )
