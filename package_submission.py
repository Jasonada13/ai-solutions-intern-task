"""Package a small, self-contained private email submission."""
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from generate_data import sha256

FILES = (
    "README.md", "DATA.md", "NOTES.md", "LICENSE", "data/README.md",
    "models.py", "solution.py", "analysis.sql", "run.py", "generate_data.py",
    "report.py", "package_submission.py", "tests/test_scaffold.py", "tests/test_candidate.py",
    "output/summary.csv", "output/quality.json", "output/report.html",
    "output/manifest.json", "output/reproducibility.json",
)


def build_archive(root: Path) -> Path:
    archive = root / "submission.zip"
    archive.unlink(missing_ok=True)
    try:
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
            raise ValueError("Manifest does not match the output files. Run python3 run.py --check-repro again.")
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as submission:
            for name in FILES:
                submission.write(root / name, arcname=name)
    except Exception:
        archive.unlink(missing_ok=True)
        raise
    return archive


def main() -> int:
    try:
        archive = build_archive(Path(__file__).resolve().parent)
    except (OSError, ValueError, AttributeError) as error:
        print(f"Unable to package submission: {error}", file=sys.stderr)
        return 1
    print(f"Created {archive.name}. Email it through your recruiter invitation or reply channel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
