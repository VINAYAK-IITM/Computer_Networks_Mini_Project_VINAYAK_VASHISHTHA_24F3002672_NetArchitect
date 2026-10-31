"""Command-line interface for the NetArchitect planning engine."""

import argparse
import json
from pathlib import Path
import sys

from .engine import build_plan, write_exports
from .errors import NetArchitectError
from .models import Profile
from .packetflow import simulate_deny_rule

PROFILE_DIR = Path(__file__).resolve().parent / "profiles"


def _profile_ids() -> list[str]:
    return sorted(path.stem for path in PROFILE_DIR.glob("*.json"))


def load_profile(profile_id: str) -> Profile:
    path = PROFILE_DIR / f"{profile_id}.json"
    if not path.is_file():
        raise NetArchitectError(
            f"Unknown profile '{profile_id}'. Choose one of: {', '.join(_profile_ids())}."
        )
    try:
        return Profile.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ValueError) as exc:
        raise NetArchitectError(f"Could not read profile '{profile_id}': {exc}") from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netarchitect",
        description="Explainable network planning, IPv4 VLSM, and Cisco IOS draft generation.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list-profiles", help="List the built-in scenarios.")

    show = commands.add_parser("show-profile", help="Show a built-in scenario summary.")
    show.add_argument("profile_id", choices=_profile_ids())

    generate = commands.add_parser("generate", help="Generate plans and IOS drafts for a preset.")
    generate.add_argument("profile_id", choices=_profile_ids())
    generate.add_argument("--out", type=Path, help="Output directory (default: output/<profile>).")

    custom = commands.add_parser("generate-custom", help="Generate from a custom JSON profile.")
    custom.add_argument("input", type=Path, help="Path to a profile JSON file.")
    custom.add_argument("--out", type=Path, required=True, help="Output directory.")

    flow = commands.add_parser("flow", help="Walk one configured deny ACL for a packet.")
    flow.add_argument("profile_id", choices=_profile_ids())
    flow.add_argument("--acl", required=True, help="ACL rule name from the profile, e.g. GUEST-TO-MANAGEMENT.")
    flow.add_argument("--source", required=True, help="Source IPv4 address.")
    flow.add_argument("--destination", required=True, help="Destination IPv4 address.")
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None and len(sys.argv) == 1:
        argv = ["list-profiles"]
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list-profiles":
            for profile_id in _profile_ids():
                profile = load_profile(profile_id)
                print(f"{profile_id:8} {profile.name} - {profile.description}")
            return 0

        if args.command == "show-profile":
            profile = load_profile(args.profile_id)
            print(f"{profile.name}\n{profile.description}\nAddress pool: {profile.root_cidr}")
            return 0

        if args.command == "generate":
            profile = load_profile(args.profile_id)
            out_dir = args.out or Path("output") / args.profile_id
            plan = build_plan(profile)
            write_exports(plan, out_dir)
            print(f"Generated {profile.name} exports in {out_dir.resolve()}")
            return 0

        if args.command == "generate-custom":
            try:
                profile_data = json.loads(args.input.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise NetArchitectError(f"Could not read custom JSON: {exc}") from exc
            profile = Profile.from_dict(profile_data)
            plan = build_plan(profile)
            write_exports(plan, args.out)
            print(f"Generated {profile.name} exports in {args.out.resolve()}")
            return 0

        if args.command == "flow":
            plan = build_plan(load_profile(args.profile_id))
            rule = next(
                (item for item in plan["profile"]["acls"] if item["name"] == args.acl),
                None,
            )
            if rule is None:
                raise NetArchitectError(f"ACL '{args.acl}' is not defined by this profile.")
            result = simulate_deny_rule(plan, rule, args.source, args.destination)
            print(json.dumps(result, indent=2))
            return 0
    except (NetArchitectError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0

