import nox
import nox_uv

nox.options.default_venv_backend = "uv"

nox.options.sessions = ["lint", "typecheck", "tests"]

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


@nox_uv.session(python=PYTHON_VERSIONS, uv_groups=["test"])
def tests(session: nox.Session) -> None:
    """Run the test suite against multiple Python versions."""
    session.run("pytest", *session.posargs)


@nox.session(python=PYTHON_VERSIONS[0])
def tests_lowest(session: nox.Session) -> None:
    """Run the test suite against the oldest dependency versions allowed."""
    session.install("--resolution", "lowest-direct", "-e", ".")
    session.install("--group", "test")
    session.run("pytest", *session.posargs)


@nox_uv.session(python="3.13", uv_only_groups=["lint"])
def lint(session: nox.Session) -> None:
    """Check code style and formatting with Ruff."""
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")


@nox_uv.session(python="3.13", uv_groups=["typecheck"])
def typecheck(session: nox.Session) -> None:
    """Run mypy and pyright type checkers."""
    session.run("mypy", ".")
    session.run("pyright", ".")


@nox_uv.session(python="3.13", uv_groups=["docs"])
def docs(session: nox.Session) -> None:
    """Build the documentation (without deploying)."""
    session.run("zensical", "build", "--clean", "--strict")
