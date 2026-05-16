#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TARGET = Path("drvpkg/kernel/nvidia/nv-kernel.o_binary")
MAX_OFFSETS_TO_PRINT = 20


@dataclass(frozen=True)
class PatchRule:
    name: str
    search_hex: str
    replace_hex: str


@dataclass(frozen=True)
class PatchResult:
    name: str
    count: int
    offsets: list[int]


RULES = [
    PatchRule(
        name="P1xx",
        search_hex="071b0700871b0700c71b0700071c0700091c0700",
        replace_hex="ffff0700ffff0700ffff0700ffff0700ffff0700",
    ),
    PatchRule(
        name="CMP",
        search_hex="091e0700491e0700bc1e0700fc1e07000b1f0700812007008220070083200700c2200700892107000d2207004d2207008a240700",
        replace_hex="ffff0700491e0700bc1e0700fc1e0700ffff070081200700ffff070083200700ffff0700ffff0700ffff07004d220700ffff0700",
    ),
    PatchRule(
        name="RTX 3080 Ti 20 GB",
        search_hex="05220000092200001422000017220000",
        replace_hex="ffff0000092200001422000017220000",
    ),
    PatchRule(
        name="RTX 3060 3840SP",
        search_hex="01250000052500000925000040250000",
        replace_hex="ffff0000052500000925000040250000",
    ),
    PatchRule(
        name="RTX 4070 10 GB",
        search_hex="85270000af270000bf270000c2270000",
        replace_hex="ffff0000af270000bf270000c2270000",
    ),
    PatchRule(
        name="NVIDIA L40 ES",
        search_hex="af260000b0260000bf260000c1260000",
        replace_hex="ffff0000b0260000bf260000c1260000",
    ),
]


def sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def warning(message: str) -> None:
    print(f"::warning::{message}")


def pattern_bytes(rule: PatchRule) -> tuple[bytes, bytes]:
    try:
        search = bytes.fromhex(rule.search_hex)
        replace = bytes.fromhex(rule.replace_hex)
    except ValueError as exc:
        raise ValueError(f"Invalid hex pattern for {rule.name}: {exc}") from exc
    if len(search) != len(replace):
        raise ValueError(
            f"Pattern length mismatch for {rule.name}: "
            f"search={len(search)} bytes replace={len(replace)} bytes"
        )
    return search, replace


def format_offsets(found_offsets: list[int], count: int) -> str:
    shown = ", ".join(str(offset) for offset in found_offsets)
    if count > len(found_offsets):
        return f"{shown}, ... ({count - len(found_offsets)} more)"
    return shown


def replace_all(data: bytearray, search: bytes, replace: bytes) -> tuple[int, list[int]]:
    count = 0
    found_offsets: list[int] = []
    start = 0
    while True:
        index = data.find(search, start)
        if index == -1:
            return count, found_offsets
        count += 1
        if len(found_offsets) < MAX_OFFSETS_TO_PRINT:
            found_offsets.append(index)
        data[index:index + len(search)] = replace
        start = index + len(replace)


def count_pattern(data: bytearray, pattern: bytes) -> int:
    count = 0
    start = 0
    while True:
        index = data.find(pattern, start)
        if index == -1:
            return count
        count += 1
        start = index + len(pattern)


def apply_rules(data: bytearray) -> tuple[list[PatchResult], list[str], list[PatchResult]]:
    patched: list[PatchResult] = []
    not_found: list[str] = []
    already_replaced: list[PatchResult] = []

    for rule in RULES:
        search, replace = pattern_bytes(rule)
        count, found_offsets = replace_all(data, search, replace)
        if count:
            print(
                f"Found pattern: {rule.name} - {count} occurrence(s) "
                f"at byte offset(s): {format_offsets(found_offsets, count)}"
            )
            patched.append(PatchResult(rule.name, count, found_offsets))
            continue

        replace_count = count_pattern(data, replace)
        if replace_count:
            print(f"Already replaced: {rule.name} - {replace_count} occurrence(s)")
            already_replaced.append(PatchResult(rule.name, replace_count, []))
            continue

        print(f"Pattern not found: {rule.name}")
        warning(f"NVIDIA GRID kernel patch pattern not found: {rule.name}")
        not_found.append(rule.name)

    return patched, not_found, already_replaced


def print_summary(
    patched: list[PatchResult],
    not_found: list[str],
    already_replaced: list[PatchResult],
) -> None:
    print("=== PATCH SUMMARY ===")
    if patched:
        print("Patched patterns:")
        for result in patched:
            print(f"  - {result.name}: {result.count} occurrence(s)")
    else:
        print("Patched patterns: none")

    if not_found:
        print("Patterns not found:")
        for name in not_found:
            print(f"  - {name}")
    else:
        print("Patterns not found: none")

    if already_replaced:
        print("Already replaced patterns:")
        for result in already_replaced:
            print(f"  - {result.name}: {result.count} occurrence(s)")


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TARGET
    if len(sys.argv) > 2:
        print("Usage: patch-nvidia-grid-kernel-binary.py [target-file]", file=sys.stderr)
        return 1
    if not target.is_file():
        print(f"Error: File not found: {target}", file=sys.stderr)
        return 1

    original = target.read_bytes()
    patched_data = bytearray(original)

    print(f"Target: {target}")
    print(f"SHA256 before: {sha256(original)}")

    patched, not_found, already_replaced = apply_rules(patched_data)
    print_summary(patched, not_found, already_replaced)

    patched_bytes = bytes(patched_data)
    if patched_bytes == original:
        print("No patterns found. Nothing patched.")
        print(f"SHA256 after: {sha256(patched_bytes)}")
        return 0

    target.write_bytes(patched_bytes)
    print(f"SHA256 after: {sha256(patched_bytes)}")
    print("=== SUCCESS ===")
    print("Patching complete.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
