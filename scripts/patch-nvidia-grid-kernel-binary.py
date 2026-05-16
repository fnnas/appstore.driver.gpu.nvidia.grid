#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

DEFAULT_TARGET = Path("drvpkg/kernel/nvidia/nv-kernel.o_binary")

PATTERNS = [
    (
        "P1xx",
        "071b0700871b0700c71b0700071c0700091c0700",
        "ffff0700ffff0700ffff0700ffff0700ffff0700",
    ),
    (
        "CMP",
        "091e0700491e0700bc1e0700fc1e07000b1f0700812007008220070083200700c2200700892107000d2207004d2207008a240700",
        "ffff0700491e0700bc1e0700fc1e0700ffff070081200700ffff070083200700ffff0700ffff0700ffff07004d220700ffff0700",
    ),
    (
        "RTX 3080 Ti 20 GB",
        "05220000092200001422000017220000",
        "ffff0000092200001422000017220000",
    ),
    (
        "RTX 3060 3840SP",
        "01250000052500000925000040250000",
        "ffff0000052500000925000040250000",
    ),
    (
        "RTX 4070 10 GB",
        "85270000af270000bf270000c2270000",
        "ffff0000af270000bf270000c2270000",
    ),
    (
        "NVIDIA L40 ES",
        "af260000b0260000bf260000c1260000",
        "ffff0000b0260000bf260000c1260000",
    ),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def offsets(data: bytes, needle: bytes) -> list[int]:
    found = []
    start = 0
    while True:
        index = data.find(needle, start)
        if index == -1:
            return found
        found.append(index)
        start = index + len(needle)


def warning(message: str) -> None:
    print(f"::warning::{message}")


def load_patterns() -> list[tuple[str, bytes, bytes]]:
    loaded = []
    for name, search_hex, replace_hex in PATTERNS:
        try:
            search = bytes.fromhex(search_hex)
            replace = bytes.fromhex(replace_hex)
        except ValueError as exc:
            raise ValueError(f"Invalid hex pattern for {name}: {exc}") from exc
        if len(search) != len(replace):
            raise ValueError(
                f"Pattern length mismatch for {name}: "
                f"search={len(search)} bytes replace={len(replace)} bytes"
            )
        loaded.append((name, search, replace))
    return loaded


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TARGET
    if len(sys.argv) > 2:
        print("Usage: patch-nvidia-grid-kernel-binary.py [target-file]", file=sys.stderr)
        return 1
    if not target.is_file():
        print(f"Error: File not found: {target}", file=sys.stderr)
        return 1

    patterns = load_patterns()
    original = target.read_bytes()
    patched = original
    patched_summary: list[tuple[str, int]] = []
    not_found: list[str] = []
    already_replaced: list[tuple[str, int]] = []

    print(f"Target: {target}")
    print(f"SHA256 before: {sha256(original)}")

    for name, search, replace in patterns:
        search_offsets = offsets(patched, search)
        replace_count_before = patched.count(replace)
        if replace_count_before:
            already_replaced.append((name, replace_count_before))
            print(f"Already replaced candidate: {name} — {replace_count_before} occurrence(s)")

        if not search_offsets:
            print(f"Pattern not found: {name}")
            warning(f"NVIDIA GRID kernel patch pattern not found: {name}")
            not_found.append(name)
            continue

        print(
            f"Found pattern: {name} — {len(search_offsets)} occurrence(s) "
            f"at byte offset(s): {', '.join(str(offset) for offset in search_offsets)}"
        )
        patched = patched.replace(search, replace)
        patched_summary.append((name, len(search_offsets)))

    print("=== PATCH SUMMARY ===")
    if patched_summary:
        print("Patched patterns:")
        for name, count in patched_summary:
            print(f"  - {name}: {count} occurrence(s)")
    else:
        print("Patched patterns: none")

    if not_found:
        print("Patterns not found:")
        for name in not_found:
            print(f"  - {name}")
    else:
        print("Patterns not found: none")

    if already_replaced:
        print("Already replaced candidates before patch:")
        for name, count in already_replaced:
            print(f"  - {name}: {count} occurrence(s)")

    if patched == original:
        print("No patterns found. Nothing patched.")
        print(f"SHA256 after: {sha256(patched)}")
        return 0

    target.write_bytes(patched)
    print(f"SHA256 after: {sha256(patched)}")
    print("=== SUCCESS ===")
    print("Patching complete.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
