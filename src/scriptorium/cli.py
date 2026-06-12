"""Command-line entry point for the scriptorium walking skeleton.

Usage:
    scriptorium render <page_gt.json> <out_dir>

Renders a PageGT-shaped JSON file to LaTeX (always) and PDF (if tectonic is installed).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scriptorium.render import render_pdf, tectonic_available


def main(argv: list[str] | None = None) -> int:
    """Run the scriptorium CLI. Returns a process exit code."""
    parser = argparse.ArgumentParser(prog="scriptorium", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render", help="Render a PageGT JSON file to LaTeX + PDF")
    render.add_argument("page_gt", type=Path, help="Path to a PageGT-shaped JSON file")
    render.add_argument("out_dir", type=Path, help="Output directory")
    render.add_argument(
        "--strict-schema",
        action="store_true",
        help="Require the scholar-schema package for validation",
    )
    render.add_argument("--stem", default="page", help="Output filename stem")

    args = parser.parse_args(argv)

    if args.command == "render":
        page_gt = json.loads(args.page_gt.read_text(encoding="utf-8"))
        result = render_pdf(
            page_gt,
            args.out_dir,
            strict_schema=args.strict_schema,
            stem=args.stem,
        )
        tex_path = args.out_dir / f"{args.stem}.tex"
        print(f"wrote {tex_path}")
        if result.pdf_path is not None:
            print(f"wrote {result.pdf_path}")
        elif not tectonic_available():
            print(
                "tectonic not installed: PDF not rendered. Install with `brew install tectonic`.",
                file=sys.stderr,
            )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
