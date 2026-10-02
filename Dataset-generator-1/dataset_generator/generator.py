#!/usr/bin/env python3

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

DATASET_ROOT = Path(__file__).resolve().parent.parent / "dataset"
CASES_ROOT = DATASET_ROOT / "cases"

TEMP_ROOT = Path("/tmp/bugsinpy_generator")

CONDA_PATH = os.environ.get("CONDA_PATH", "/opt/conda")


# ============================================================
# Command runner
# ============================================================

def run_command(command, timeout=1800, check=False):
    """
    Run a shell command and capture stdout/stderr.
    """

    print(f"\n$ {command}")

    env = os.environ.copy()
    env["CONDA_PATH"] = CONDA_PATH

    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=check,
            env=env,
        )

        return (
            result.returncode,
            result.stdout or "",
            result.stderr or "",
        )

    except subprocess.TimeoutExpired as e:
        stdout = e.stdout or ""
        stderr = e.stderr or ""

        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")

        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")

        return (
            -1,
            stdout,
            f"{stderr}\nCommand timed out after {timeout} seconds",
        )

    except Exception as e:
        return (
            -1,
            "",
            str(e),
        )


# ============================================================
# Utility functions
# ============================================================

def clean_directory(path):
    """
    Remove a directory if it exists and recreate it.
    """

    if path.exists():
        shutil.rmtree(path)

    path.mkdir(parents=True, exist_ok=True)


def write_json(path, data):
    """
    Write JSON with readable formatting.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# BugsInPy++ checkout detection
# ============================================================

def find_checkout(workspace):
    """
    BugsInPy++ may create:

        workspace/project_name/

    instead of putting the checkout directly in workspace.

    Find the directory containing bugsinpy_bug.info.
    """

    workspace = Path(workspace)

    info_files = list(
        workspace.rglob("bugsinpy_bug.info")
    )

    if not info_files:
        return None

    # The metadata file's parent is the actual checkout.
    return info_files[0].parent


# ============================================================
# BugsInPy metadata
# ============================================================

def parse_bug_info(checkout):
    """
    Parse bugsinpy_bug.info.

    Example:

        python_version="3.7.0"
        buggy_commit_id="..."
        fixed_commit_id="..."
        test_file="test/test_utils.py"
        project_name=youtube-dl
        bug_id=1
    """

    info_file = Path(checkout) / "bugsinpy_bug.info"

    if not info_file.exists():
        raise RuntimeError(
            f"Missing bugsinpy_bug.info: {info_file}"
        )

    metadata = {}

    with open(info_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            key = key.strip()
            value = value.strip()

            # Remove surrounding quotes.
            value = value.strip('"').strip("'")

            metadata[key] = value

    required = [
        "python_version",
        "project_name",
        "bug_id",
    ]

    for key in required:
        if key not in metadata:
            raise RuntimeError(
                f"Missing '{key}' in {info_file}"
            )

    return metadata


# ============================================================
# Conda environment
# ============================================================

def conda_environment_exists(environment_name):
    """
    Check whether a Conda environment exists.
    """

    conda_bin = Path(CONDA_PATH) / "bin" / "conda"

    if not conda_bin.exists():
        raise RuntimeError(
            f"Conda executable not found: {conda_bin}"
        )

    command = (
        f'"{conda_bin}" env list'
    )

    returncode, stdout, stderr = run_command(
        command,
        timeout=120,
    )

    if returncode != 0:
        print("WARNING: Unable to query Conda environments.")
        print(stderr)

        return False

    for line in stdout.splitlines():

        line = line.strip()

        if not line or line.startswith("#"):
            continue

        # First column is environment name.
        name = line.split()[0]

        if name == environment_name:
            return True

    return False


def ensure_conda_environment(
    project_name,
    bug_id,
    python_version,
):
    """
    Create the BugsInPy++ Conda environment if necessary.

    Environment naming convention:

        <project_name>_<bug_id>

    Example:

        youtube-dl_1
    """

    environment_name = f"{project_name}_{bug_id}"

    print("\nChecking Conda environment...")
    print(f"Environment : {environment_name}")
    print(f"Python      : {python_version}")
    print(f"Conda       : {CONDA_PATH}")

    if conda_environment_exists(environment_name):

        print(
            f"✓ Conda environment already exists: "
            f"{environment_name}"
        )

        return environment_name

    print(
        f"Creating Conda environment: "
        f"{environment_name}"
    )

    conda_bin = Path(CONDA_PATH) / "bin" / "conda"

    command = (
        f'"{conda_bin}" create '
        f'-n "{environment_name}" '
        f'-y '
        f'python="{python_version}" '
        f'pytest'
    )

    returncode, stdout, stderr = run_command(
        command,
        timeout=1800,
    )

    if stdout:
        print(stdout)

    if stderr:
        print(stderr)

    if returncode != 0:
        raise RuntimeError(
            f"Failed to create Conda environment "
            f"{environment_name}"
        )

    print(
        f"✓ Created Conda environment: "
        f"{environment_name}"
    )

    return environment_name


# ============================================================
# BugsInPy++ checkout
# ============================================================

def checkout_bug(
    project,
    bug_id,
    version,
    workspace,
):
    """
    Checkout a BugsInPy++ bug.

    version:
        0 = buggy
        1 = fixed

    Important:
    BugsInPy++ creates a nested project directory.
    We detect it automatically afterwards.
    """

    clean_directory(workspace)

    command = (
        f'bugsinpy-checkout '
        f'-p "{project}" '
        f'-i "{bug_id}" '
        f'-v "{version}" '
        f'-w "{workspace}"'
    )

    returncode, stdout, stderr = run_command(
        command,
        timeout=1800,
    )

    if stdout:
        print(stdout)

    if stderr:
        print(stderr)

    if returncode != 0:
        raise RuntimeError(
            f"BugsInPy++ checkout failed "
            f"for {project}_{bug_id}, version={version}"
        )

    checkout = find_checkout(workspace)

    if checkout is None:
        raise RuntimeError(
            f"Checkout succeeded but "
            f"bugsinpy_bug.info was not found "
            f"under {workspace}"
        )

    print(
        f"✓ Actual checkout: {checkout}"
    )

    return checkout


# ============================================================
# Compile
# ============================================================

def compile_project(checkout):
    """
    Compile using the working BugsInPy++ interface.
    """

    command = (
        f'bugsinpy-compile '
        f'-w "{checkout}"'
    )

    return run_command(
        command,
        timeout=1800,
    )


# ============================================================
# Test
# ============================================================

def test_project(checkout):
    """
    Run BugsInPy++ tests.
    """

    command = (
        f'bugsinpy-test '
        f'-w "{checkout}"'
    )

    return run_command(
        command,
        timeout=1800,
    )


# ============================================================
# Save buggy repository
# ============================================================

def save_buggy_repository(
    checkout,
    destination,
):
    """
    Copy the buggy source tree into the dataset case.

    The fixed source is never copied here.
    """

    if destination.exists():
        shutil.rmtree(destination)

    print(
        f"\nCopying buggy repository to:"
        f"\n{destination}"
    )

    shutil.copytree(
        checkout,
        destination,
    )

    print("✓ Buggy repository saved")


# ============================================================
# Extract test metadata
# ============================================================

def find_test_result_files(checkout):
    """
    Find BugsInPy++ generated test result files.

    We don't depend on one exact filename because
    BugsInPy++ versions can differ.
    """

    possible_names = [
        "bugsinpy_test.txt",
        "bugsinpy_test.log",
        "test_result.txt",
    ]

    results = []

    for name in possible_names:

        path = Path(checkout) / name

        if path.exists():
            results.append(path)

    return results


def read_test_result_files(checkout):
    """
    Read any generated BugsInPy++ test result files.
    """

    result = {}

    for path in find_test_result_files(checkout):

        try:

            result[path.name] = path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        except Exception as e:

            result[path.name] = (
                f"Unable to read result: {e}"
            )

    return result


# ============================================================
# Generate one bug
# ============================================================

def generate_case(project, bug_id):
    """
    Generate a complete dataset case.
    """

    case_id = f"{project}_{bug_id}"

    print("\n")
    print("=" * 70)
    print(f"Generating case: {case_id}")
    print("=" * 70)

    case_directory = CASES_ROOT / case_id

    buggy_workspace = (
        TEMP_ROOT / f"{case_id}_buggy"
    )

    fixed_workspace = (
        TEMP_ROOT / f"{case_id}_fixed"
    )

    # --------------------------------------------------------
    # Remove previous case
    # --------------------------------------------------------

    if case_directory.exists():

        print("\nRemoving previous case...")

        shutil.rmtree(case_directory)

    case_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Step 1 — Checkout buggy
    # --------------------------------------------------------

    print("\n[1/8] Checking out BUGGY version...")

    try:

        buggy_checkout = checkout_bug(
            project,
            bug_id,
            version=0,
            workspace=buggy_workspace,
        )

    except Exception as e:

        print(
            f"ERROR: Buggy checkout failed:\n{e}"
        )

        return False

    # --------------------------------------------------------
    # Step 2 — Read metadata
    # --------------------------------------------------------

    print("\n[2/8] Reading bug metadata...")

    try:

        metadata = parse_bug_info(
            buggy_checkout
        )

    except Exception as e:

        print(
            f"ERROR: Could not read metadata:\n{e}"
        )

        return False

    actual_project = metadata["project_name"]
    actual_bug_id = metadata["bug_id"]
    python_version = metadata["python_version"]

    environment_name = (
        f"{actual_project}_{actual_bug_id}"
    )

    print(
        f"Project       : {actual_project}"
    )

    print(
        f"Bug ID        : {actual_bug_id}"
    )

    print(
        f"Python        : {python_version}"
    )

    print(
        f"Environment   : {environment_name}"
    )

    # --------------------------------------------------------
    # Step 3 — Conda environment
    # --------------------------------------------------------

    print("\n[3/8] Preparing Conda environment...")

    try:

        ensure_conda_environment(
            actual_project,
            actual_bug_id,
            python_version,
        )

    except Exception as e:

        print(
            f"ERROR: Conda environment setup failed:\n{e}"
        )

        return False

    # --------------------------------------------------------
    # Step 4 — Compile buggy
    # --------------------------------------------------------

    print("\n[4/8] Compiling BUGGY version...")

    buggy_compile_rc, buggy_compile_out, buggy_compile_err = (
        compile_project(buggy_checkout)
    )

    if buggy_compile_out:
        print("\nCompile stdout:")
        print(buggy_compile_out)

    if buggy_compile_err:
        print("\nCompile stderr:")
        print(buggy_compile_err)

    if buggy_compile_rc != 0:

        print(
            "\nERROR: Buggy version failed to compile."
        )

        write_json(
            case_directory / "metadata.json",
            {
                "case_id": case_id,
                "project": actual_project,
                "bug_id": int(actual_bug_id),
                "python_version": python_version,
                "conda_environment": environment_name,
                "status": "compile_failed",
                "buggy_commit": metadata.get(
                    "buggy_commit_id"
                ),
                "fixed_commit": metadata.get(
                    "fixed_commit_id"
                ),
                "test_file": metadata.get(
                    "test_file"
                ),
            },
        )

        return False

    print("✓ Buggy version compiled")

    # --------------------------------------------------------
    # Step 5 — Run buggy test
    # --------------------------------------------------------

    print("\n[5/8] Running BUGGY tests...")

    buggy_test_rc, buggy_test_out, buggy_test_err = (
        test_project(buggy_checkout)
    )

    print(
        f"\nBuggy test return code: "
        f"{buggy_test_rc}"
    )

    if buggy_test_out:
        print("\nTest stdout:")
        print(buggy_test_out)

    if buggy_test_err:
        print("\nTest stderr:")
        print(buggy_test_err)

    buggy_result_files = read_test_result_files(
        buggy_checkout
    )

    # A benchmark bug should reproduce a failure.
    if buggy_test_rc == 0:

        print(
            "\nWARNING:"
            "\nThe buggy version did not return a failure."
            "\nThis case may not be suitable for the benchmark."
        )

    else:

        print(
            "\n✓ Buggy failure reproduced"
        )

    # --------------------------------------------------------
    # Save buggy repository
    # --------------------------------------------------------

    buggy_destination = (
        case_directory / "buggy_project"
    )

    save_buggy_repository(
        buggy_checkout,
        buggy_destination,
    )

    # --------------------------------------------------------
    # Save failure information
    # --------------------------------------------------------

    failure_data = {
        "case_id": case_id,
        "project": actual_project,
        "bug_id": int(actual_bug_id),
        "status": (
            "failed"
            if buggy_test_rc != 0
            else "passed_unexpectedly"
        ),
        "return_code": buggy_test_rc,
        "stdout": buggy_test_out,
        "stderr": buggy_test_err,
        "test_result_files": buggy_result_files,
        "test_file": metadata.get("test_file"),
        "buggy_commit": metadata.get(
            "buggy_commit_id"
        ),
    }

    write_json(
        case_directory / "failure.json",
        failure_data,
    )

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    metadata_data = {
        "case_id": case_id,
        "project": actual_project,
        "bug_id": int(actual_bug_id),
        "python_version": python_version,
        "conda_environment": environment_name,
        "test_file": metadata.get(
            "test_file"
        ),
        "buggy_commit": metadata.get(
            "buggy_commit_id"
        ),
        "fixed_commit": metadata.get(
            "fixed_commit_id"
        ),
        "buggy_test_return_code": buggy_test_rc,
        "buggy_compile_return_code": buggy_compile_rc,
    }

    write_json(
        case_directory / "metadata.json",
        metadata_data,
    )

    # --------------------------------------------------------
    # Step 6 — Checkout fixed
    # --------------------------------------------------------

    print("\n[6/8] Checking out FIXED version...")

    try:

        fixed_checkout = checkout_bug(
            project,
            bug_id,
            version=1,
            workspace=fixed_workspace,
        )

    except Exception as e:

        print(
            f"ERROR: Fixed checkout failed:\n{e}"
        )

        return False

    # --------------------------------------------------------
    # Step 7 — Compile fixed
    # --------------------------------------------------------

    print("\n[7/8] Compiling FIXED version...")

    fixed_compile_rc, fixed_compile_out, fixed_compile_err = (
        compile_project(fixed_checkout)
    )

    if fixed_compile_out:
        print("\nFixed compile stdout:")
        print(fixed_compile_out)

    if fixed_compile_err:
        print("\nFixed compile stderr:")
        print(fixed_compile_err)

    if fixed_compile_rc != 0:

        print(
            "\nERROR: Fixed version failed to compile."
        )

        return False

    print("✓ Fixed version compiled")

    # --------------------------------------------------------
    # Step 8 — Test fixed
    # --------------------------------------------------------

    print("\n[8/8] Running FIXED tests...")

    fixed_test_rc, fixed_test_out, fixed_test_err = (
        test_project(fixed_checkout)
    )

    print(
        f"\nFixed test return code: "
        f"{fixed_test_rc}"
    )

    if fixed_test_out:
        print("\nFixed test stdout:")
        print(fixed_test_out)

    if fixed_test_err:
        print("\nFixed test stderr:")
        print(fixed_test_err)

    fixed_result_files = read_test_result_files(
        fixed_checkout
    )

    fixed_passed = fixed_test_rc == 0

    if fixed_passed:

        print(
            "\n✓ Fixed version passes"
        )

    else:

        print(
            "\nWARNING:"
            "\nFixed version did not pass."
        )

    # --------------------------------------------------------
    # Ground truth
    # --------------------------------------------------------

    ground_truth = {
        "case_id": case_id,
        "project": actual_project,
        "bug_id": int(actual_bug_id),
        "expected_status": (
            "fixed"
            if fixed_passed
            else "fixed_test_failed"
        ),
        "fixed_test_return_code": fixed_test_rc,
        "fixed_test_stdout": fixed_test_out,
        "fixed_test_stderr": fixed_test_err,
        "fixed_test_result_files": fixed_result_files,
        "buggy_commit": metadata.get(
            "buggy_commit_id"
        ),
        "fixed_commit": metadata.get(
            "fixed_commit_id"
        ),
        "test_file": metadata.get(
            "test_file"
        ),
    }

    write_json(
        case_directory / "ground_truth.json",
        ground_truth,
    )

    # --------------------------------------------------------
    # Cleanup FIXED source
    # --------------------------------------------------------

    # VERY IMPORTANT:
    # Fixed source must not remain in the dataset.
    #
    # It is evaluation-only.

    if fixed_workspace.exists():

        shutil.rmtree(
            fixed_workspace
        )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    success = (
        buggy_test_rc != 0
        and fixed_test_rc == 0
    )

    print("\n")
    print("=" * 70)

    if success:

        print(
            f"✓ SUCCESS: {case_id}"
        )

        print(
            f"\nDataset case:"
            f"\n{case_directory}"
        )

    else:

        print(
            f"⚠ CASE GENERATED WITH WARNINGS: "
            f"{case_id}"
        )

        print(
            f"\nDataset case:"
            f"\n{case_directory}"
        )

    print("=" * 70)

    return success


# ============================================================
# Bug list parsing
# ============================================================

def parse_bug_list(bugs):
    """
    Parse:

        1
        1,2,3
        1-5
        1,3,5-8

    """

    result = []

    if not bugs:
        return result

    parts = bugs.split(",")

    for part in parts:

        part = part.strip()

        if not part:
            continue

        if "-" in part:

            start, end = part.split("-", 1)

            start = int(start)
            end = int(end)

            if start > end:
                raise ValueError(
                    f"Invalid bug range: {part}"
                )

            result.extend(
                range(start, end + 1)
            )

        else:

            result.append(
                int(part)
            )

    # Remove duplicates while preserving order.
    return list(dict.fromkeys(result))


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate an AI CI/CD debugging "
            "dataset from BugsInPy++"
        )
    )

    parser.add_argument(
        "--project",
        required=True,
        help="BugsInPy++ project name",
    )

    parser.add_argument(
        "--bug",
        help="Single bug ID",
    )

    parser.add_argument(
        "--bugs",
        help=(
            "Multiple bug IDs, e.g. "
            "1-5 or 1,3,5-8"
        ),
    )

    args = parser.parse_args()

    if not args.bug and not args.bugs:

        parser.error(
            "Specify --bug or --bugs"
        )

    if args.bug and args.bugs:

        parser.error(
            "Use either --bug or --bugs, not both"
        )

    if args.bug:

        try:
            bug_ids = [int(args.bug)]

        except ValueError:

            parser.error(
                "--bug must be an integer"
            )

    else:

        try:
            bug_ids = parse_bug_list(
                args.bugs
            )

        except ValueError as e:

            parser.error(str(e))

    # --------------------------------------------------------
    # Prepare directories
    # --------------------------------------------------------

    CASES_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    TEMP_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("BugsInPy++ Dataset Generator")
    print("=" * 70)

    print(
        f"Project : {args.project}"
    )

    print(
        f"Bugs    : {bug_ids}"
    )

    print(
        f"Dataset : {CASES_ROOT}"
    )

    print(
        f"Conda   : {CONDA_PATH}"
    )

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    successful = []
    failed = []

    for index, bug_id in enumerate(
        bug_ids,
        start=1,
    ):

        print("\n")
        print(
            f"Progress: "
            f"[{index}/{len(bug_ids)}]"
        )

        try:

            success = generate_case(
                args.project,
                bug_id,
            )

            if success:

                successful.append(
                    f"{args.project}_{bug_id}"
                )

            else:

                failed.append(
                    f"{args.project}_{bug_id}"
                )

        except KeyboardInterrupt:

            print(
                "\nGeneration interrupted."
            )

            sys.exit(1)

        except Exception as e:

            print(
                f"\nUnexpected error:"
                f"\n{e}"
            )

            failed.append(
                f"{args.project}_{bug_id}"
            )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"Total      : {len(bug_ids)}"
    )

    print(
        f"Successful : {len(successful)}"
    )

    print(
        f"Failed     : {len(failed)}"
    )

    if successful:

        print("\nSuccessful bugs:")

        for case in successful:

            print(
                f"  ✓ {case}"
            )

    if failed:

        print("\nFailed/warning bugs:")

        for case in failed:

            print(
                f"  ✗ {case}"
            )

    print(
        f"\nDataset location:"
        f"\n{CASES_ROOT}"
    )


if __name__ == "__main__":
    main()