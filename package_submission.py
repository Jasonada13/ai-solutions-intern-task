"""Build the submission ZIP, including any selected report files."""
import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple
from zipfile import ZIP_DEFLATED, ZipFile

from generate_data import sha256

FILES = (
    "README.md", "DATA.md", "NOTES.md", "LICENSE", "data/README.md",
    "models.py", "solution.py", "analysis.sql", "run.py", "generate_data.py",
    "report.py", "package_submission.py", "tests/test_scaffold.py", "tests/test_candidate.py",
    "output/summary.csv", "output/quality.json", "output/report.html",
    "output/manifest.json", "output/reproducibility.json",
)


class ReportAttachment(NamedTuple):
    source: Path
    archive_name: str


def report_attachments(root: Path, business_report: str | Path | None,
                       report_preview: str | Path | None) -> list[ReportAttachment]:
    if report_preview is not None and business_report is None:
        raise ValueError("--report-preview requires --business-report.")
    attachments = []
    archive = root / "submission.zip"
    for selected, prefix in ((business_report, "business-report"),
                             (report_preview, "business-report/preview")):
        if selected is None:
            continue
        path = Path(selected)
        if not path.is_absolute():
            path = root / path
        if any(part.is_symlink() for part in (path, *path.parents)):
            raise ValueError(f"Report attachment must not use a symlink: {selected}")
        if path.resolve() == archive.resolve() or (
                path.exists() and archive.exists() and path.samefile(archive)):
            raise ValueError("submission.zip cannot also be a report attachment.")
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Report attachment must be a regular, nonempty file: {selected}")
        name = path.name
        if name.rstrip(" .") != name or any(
                char in "/\\:" or unicodedata.category(char) == "Cc" for char in name):
            raise ValueError(f"Report attachment has an unsafe filename: {name!r}")
        attachments.append(ReportAttachment(path, f"{prefix}/{name}"))
    return attachments


def build_archive(root: Path, *, business_report: str | Path | None = None,
                  report_preview: str | Path | None = None) -> Path:
    root = root.resolve()
    archive = root / "submission.zip"
    try:
        attachments = report_attachments(root, business_report, report_preview)
        names = [*FILES, *(item.archive_name for item in attachments)]
        destinations = set()
        for name in names:
            normalized = name.casefold()
            if normalized in destinations or any(
                    normalized.startswith(existing + "/") or existing.startswith(normalized + "/")
                    for existing in destinations):
                raise ValueError(f"Two files would use conflicting paths in the ZIP: {name}")
            destinations.add(normalized)
        archive.unlink(missing_ok=True)
        for name in FILES:
            path = root / name
            if not path.is_file():
                raise ValueError(f"Missing {name}. Run python3 run.py --check-repro before packaging.")
            if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"{name} must be a regular file inside the task folder.")
        proof = json.loads((root / "output/reproducibility.json").read_text(encoding="utf-8"))
        expected = {name: sha256(root / "output" / name)
                    for name in ("summary.csv", "quality.json", "report.html", "manifest.json")}
        if proof.get("matched") is not True or proof.get("hashes") != expected:
            raise ValueError("Outputs changed after the two-run check. Run python3 run.py --check-repro again.")
        manifest = json.loads((root / "output/manifest.json").read_text(encoding="utf-8"))
        source_hashes = {name: sha256(root / name)
                         for name in ("solution.py", "analysis.sql", "tests/test_candidate.py", "NOTES.md")}
        if manifest.get("candidate_files") != source_hashes:
            raise ValueError("Candidate files changed after the run. Run python3 run.py --check-repro again.")
        if manifest.get("outputs") != {name: expected[name] for name in ("summary.csv", "quality.json", "report.html")}:
            raise ValueError("The output hashes in manifest.json do not match the files. Run python3 run.py --check-repro again.")
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as submission:
            for name in FILES:
                submission.write(root / name, arcname=name)
            for attachment in attachments:
                submission.write(attachment.source, arcname=attachment.archive_name)
    except Exception:
        archive.unlink(missing_ok=True)
        raise
    return archive


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Create submission.zip with your code, results and optional report.")
    parser.add_argument("--business-report", metavar="PATH", help="business report file in any format")
    parser.add_argument("--report-preview", metavar="PATH", help="readable report preview, requires --business-report")
    root = Path(__file__).resolve().parent
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        if error.code:
            (root / "submission.zip").unlink(missing_ok=True)
        raise
    try:
        archive = build_archive(root, business_report=args.business_report, report_preview=args.report_preview)
    except (OSError, ValueError, AttributeError) as error:
        print(f"Unable to package submission: {error}", file=sys.stderr)
        return 1
    print(f"Created {archive.name}. Send it by email using the instructions in your invitation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
