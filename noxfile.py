import nox

nox.options.default_venv_backend = "uv"

nox.options.sessions = ["lint", "typecheck", "tests"]

PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite against multiple Python versions."""
    session.install(".[dev]")
    session.run("pytest", *session.posargs)
    # session.posargs lets you pass extra args through, e.g.:
    #   nox -s tests -- -k test_something


@nox.session(python="3.13")
def lint(session: nox.Session) -> None:
    """Check code style and formatting with Ruff."""
    session.install("ruff")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")


@nox.session(python="3.13")
def typecheck(session: nox.Session) -> None:
    """Run mypy and pyright type checkers."""
    session.install(".[dev]")
    session.run("mypy", "--strict", ".")
    session.run("pyright", ".")


@nox.session(python="3.13")
def docs(session: nox.Session) -> None:
    """Build the documentation (without deploying)."""
    session.install(".[docs]")
    session.run("mkdocs", "build", "--strict")
