"""
Day 02: Password Generator + Strength Checker
A CLI tool for generating secure passwords and evaluating password strength.

Usage:
    python password_tool.py                        # Interactive menu
    python password_tool.py generate               # Generate password (interactive)
    python password_tool.py check "MyPassword123!" # Check a password
"""

import random
import string
import re
import sys
import getpass
import argparse

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

COMMON_PATTERNS = [
    "password", "passw0rd", "pa$$word", "123456", "12345678", "1234567890",
    "qwerty", "abc123", "letmein", "iloveyou", "admin", "welcome",
    "monkey", "dragon", "master", "sunshine", "princess", "football",
    "shadow", "superman", "michael", "charlie", "donald", "123123",
    "000000", "111111", "654321", "1qaz2wsx", "qwertyuiop",
]

SPECIAL_CHARS = "!@#$%^&*"


# ─────────────────────────────────────────────
# PASSWORD GENERATOR
# ─────────────────────────────────────────────

def generate_password(length: int, use_upper: bool, use_lower: bool,
                      use_digits: bool, use_special: bool) -> str:
    """
    Generate a cryptographically random password based on selected criteria.
    Guarantees at least one character from each selected category.
    """
    if not any([use_upper, use_lower, use_digits, use_special]):
        raise ValueError("At least one character category must be selected.")

    if not (8 <= length <= 64):
        raise ValueError("Password length must be between 8 and 64 characters.")

    pool = ""
    required_chars = []

    if use_upper:
        pool += string.ascii_uppercase
        required_chars.append(random.SystemRandom().choice(string.ascii_uppercase))
    if use_lower:
        pool += string.ascii_lowercase
        required_chars.append(random.SystemRandom().choice(string.ascii_lowercase))
    if use_digits:
        pool += string.digits
        required_chars.append(random.SystemRandom().choice(string.digits))
    if use_special:
        pool += SPECIAL_CHARS
        required_chars.append(random.SystemRandom().choice(SPECIAL_CHARS))

    rng = random.SystemRandom()
    remaining = [rng.choice(pool) for _ in range(length - len(required_chars))]
    all_chars = required_chars + remaining
    rng.shuffle(all_chars)
    return "".join(all_chars)


# ─────────────────────────────────────────────
# STRENGTH CHECKER
# ─────────────────────────────────────────────

def check_strength(password: str) -> dict:
    """
    Evaluate password strength. Returns a dict with:
        score (0–10), level, emoji, breakdown, suggestions
    """
    if not password:
        return {
            "score": 0, "level": "Weak", "emoji": "❌",
            "breakdown": {}, "suggestions": ["Password cannot be empty."]
        }

    score = 0
    breakdown = {}
    suggestions = []

    # ── Length ──────────────────────────────
    length = len(password)
    if length >= 16:
        score += 3
        breakdown["length"] = ("✅", f"{length} chars — excellent")
    elif length >= 12:
        score += 2
        breakdown["length"] = ("⚠️", f"{length} chars — good")
    elif length >= 8:
        score += 1
        breakdown["length"] = ("⚠️", f"{length} chars — acceptable")
    else:
        breakdown["length"] = ("❌", f"{length} chars — too short")
        suggestions.append("Use at least 12 characters for better security.")

    # ── Character diversity ──────────────────
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]", password))

    diversity = sum([has_upper, has_lower, has_digit, has_special])

    if has_upper:
        score += 1
        breakdown["uppercase"] = ("✅", "Has uppercase letters")
    else:
        breakdown["uppercase"] = ("❌", "No uppercase letters")
        suggestions.append("Add uppercase letters (A–Z).")

    if has_lower:
        score += 1
        breakdown["lowercase"] = ("✅", "Has lowercase letters")
    else:
        breakdown["lowercase"] = ("❌", "No lowercase letters")
        suggestions.append("Add lowercase letters (a–z).")

    if has_digit:
        score += 1
        breakdown["digits"] = ("✅", "Has numbers")
    else:
        breakdown["digits"] = ("❌", "No numbers")
        suggestions.append("Add numbers (0–9).")

    if has_special:
        score += 2
        breakdown["special"] = ("✅", "Has special characters")
    else:
        breakdown["special"] = ("❌", "No special characters")
        suggestions.append("Add special characters like !@#$%^&*")

    # ── Common patterns ──────────────────────
    lower_pw = password.lower()
    if any(pattern in lower_pw for pattern in COMMON_PATTERNS):
        score = max(0, score - 3)
        breakdown["patterns"] = ("❌", "Contains common pattern")
        suggestions.append("Avoid common words like 'password', 'admin', '12345'.")
    else:
        breakdown["patterns"] = ("✅", "No common patterns found")

    # ── Repeated characters ──────────────────
    if re.search(r"(.)\1{2,}", password):
        score = max(0, score - 1)
        breakdown["repeats"] = ("⚠️", "Contains repeated characters")
        suggestions.append("Avoid repeating the same character 3+ times in a row.")
    else:
        breakdown["repeats"] = ("✅", "No excessive repetition")

    # ── Sequential characters ────────────────
    sequences = ["abcdefghijklmnopqrstuvwxyz", "0123456789", "qwertyuiop", "asdfghjkl"]
    has_seq = any(
        seq[i:i+3] in lower_pw
        for seq in sequences
        for i in range(len(seq) - 2)
    )
    if has_seq:
        score = max(0, score - 1)
        breakdown["sequential"] = ("⚠️", "Contains sequential characters")
        suggestions.append("Avoid sequential patterns like 'abc' or '123'.")
    else:
        breakdown["sequential"] = ("✅", "No sequential patterns")

    # ── Score → Level ────────────────────────
    score = max(0, min(10, score))
    if score <= 3:
        level, emoji = "Weak", "❌"
    elif score <= 6:
        level, emoji = "Medium", "⚠️"
    else:
        level, emoji = "Strong", "✅"

    return {
        "score": score,
        "level": level,
        "emoji": emoji,
        "breakdown": breakdown,
        "suggestions": suggestions,
    }


# ─────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────

def print_separator(char="─", width=50):
    print(char * width)


def print_strength_report(password: str, result: dict, show_password: bool = True):
    print_separator()
    if show_password:
        print(f"  Password : {password}")
    print(f"  Strength : {result['emoji']} {result['level']}")
    print(f"  Score    : {result['score']}/10  {'█' * result['score']}{'░' * (10 - result['score'])}")
    print_separator()
    print("  Breakdown:")
    for key, (icon, msg) in result["breakdown"].items():
        label = key.capitalize().ljust(12)
        print(f"    {icon}  {label} {msg}")

    if result["suggestions"]:
        print_separator()
        print("  Suggestions to improve:")
        for tip in result["suggestions"]:
            print(f"    → {tip}")
    print_separator()


def print_banner():
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║     🔐 Password Generator & Checker      ║")
    print("  ╚══════════════════════════════════════════╝")
    print()


# ─────────────────────────────────────────────
# INPUT HANDLERS
# ─────────────────────────────────────────────

def get_yes_no(prompt: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        val = input(f"  {prompt} {hint}: ").strip().lower()
        if val == "":
            return default
        if val in ("y", "yes"):
            return True
        if val in ("n", "no"):
            return False
        print("  Please enter y or n.")


def get_int(prompt: str, min_val: int, max_val: int, default: int) -> int:
    while True:
        val = input(f"  {prompt} [{min_val}–{max_val}, default {default}]: ").strip()
        if val == "":
            return default
        try:
            n = int(val)
            if min_val <= n <= max_val:
                return n
            print(f"  ⚠️  Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("  ⚠️  Invalid input. Please enter a whole number.")


# ─────────────────────────────────────────────
# MAIN FLOWS
# ─────────────────────────────────────────────

def flow_generate():
    print()
    print("  ── Generate a Password ──────────────────────")
    length = get_int("Password length?", 8, 64, 16)
    use_upper = get_yes_no("Include uppercase letters (A–Z)?", True)
    use_lower = get_yes_no("Include lowercase letters (a–z)?", True)
    use_digits = get_yes_no("Include numbers (0–9)?", True)
    use_special = get_yes_no("Include special characters (!@#$%^&*)?", True)

    if not any([use_upper, use_lower, use_digits, use_special]):
        print("\n  ⚠️  You must select at least one character type. Defaulting to all.\n")
        use_upper = use_lower = use_digits = use_special = True

    try:
        password = generate_password(length, use_upper, use_lower, use_digits, use_special)
    except ValueError as e:
        print(f"\n  ❌ Error: {e}\n")
        return

    print()
    result = check_strength(password)
    print_strength_report(password, result)

    if CLIPBOARD_AVAILABLE:
        if get_yes_no("Copy password to clipboard?", True):
            pyperclip.copy(password)
            print("  ✅ Copied to clipboard!")
    else:
        print("  💡 Tip: Install pyperclip to enable clipboard copying.")
    print()


def flow_check(password: str = None, masked: bool = False):
    print()
    print("  ── Check Password Strength ──────────────────")
    if password is None:
        if masked:
            password = getpass.getpass("  Enter password (hidden): ")
        else:
            password = input("  Enter password: ")

    if not password.strip():
        print("\n  ❌ Password cannot be empty.\n")
        return

    result = check_strength(password)
    print_strength_report(password, result, show_password=not masked)
    print()


def interactive_menu():
    print_banner()
    while True:
        print("  What would you like to do?")
        print("  1. Generate a secure password")
        print("  2. Check password strength")
        print("  3. Exit")
        print()
        choice = input("  Enter choice [1/2/3]: ").strip()

        if choice == "1":
            flow_generate()
        elif choice == "2":
            flow_check(masked=True)
        elif choice == "3":
            print("\n  👋 Stay secure!\n")
            break
        else:
            print("\n  ⚠️  Invalid choice. Please enter 1, 2, or 3.\n")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🔐 Password Generator + Strength Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python password_tool.py                    # Interactive menu\n"
            "  python password_tool.py generate           # Generate a password\n"
            '  python password_tool.py check "MyPass123!" # Check a specific password\n'
            "  python password_tool.py check              # Check (hidden input)\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("generate", help="Generate a secure password")

    check_parser = subparsers.add_parser("check", help="Check password strength")
    check_parser.add_argument(
        "password", nargs="?", default=None,
        help="Password to check. Omit to enter securely via prompt."
    )

    args = parser.parse_args()

    if args.command == "generate":
        print_banner()
        flow_generate()
    elif args.command == "check":
        print_banner()
        flow_check(password=args.password, masked=(args.password is None))
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
