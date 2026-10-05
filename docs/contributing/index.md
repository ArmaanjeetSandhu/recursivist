# Contributing to Recursivist

Thank you for your interest in contributing to Recursivist! This page describes how to report a problem, suggest a feature, and get a change merged. Two companion guides go into detail:

- [Development Guide](development.md) — setting up an environment, the project layout, coding standards, and how to extend Recursivist
- [Testing Guide](testing.md) — running the test suite and writing tests

## Reporting Bugs

Please report bugs by opening an [issue](https://github.com/ArmaanjeetSandhu/recursivist/issues) with the following information:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, and the output of `recursivist version`)
- Any relevant logs or screenshots; running the command with `--verbose` often shows the cause

## Suggesting Features

We welcome feature requests! Please open an issue with:

- A clear and descriptive title
- A detailed description of the proposed feature
- Any relevant examples or use cases
- Information about why this feature would be useful

## Making a Change

1. **Fork the repository**: visit the [Recursivist repository](https://github.com/ArmaanjeetSandhu/recursivist) and click "Fork" to create your own copy.

2. **Clone your fork** and set up a development environment as described in the [Development Guide](development.md#setting-up-a-development-environment):

    ```bash
    git clone https://github.com/YOUR_USERNAME/recursivist.git
    cd recursivist
    ```

3. **Create a branch** for your feature or bugfix:

    ```bash
    git checkout -b feature/your-feature-name
    # or
    git checkout -b fix/issue-description
    ```

4. **Make your changes**, following the [coding standards](development.md#coding-standards), and add or update [tests](testing.md) for them.

5. **Run the checks** that CI will run:

    ```bash
    nox -s lint typecheck   # Ruff, mypy, and pyright
    nox -s tests            # the test suite, on every supported Python version
    nox -s docs             # only if you changed the documentation or a docstring
    ```

6. **Commit** with a clear and descriptive message. The pre-commit hooks run automatically; if they flag or fix something, review the result and commit again:

    ```bash
    git add .
    git commit -m "Add feature: description of what you added"
    ```

7. **Keep your branch up to date** by syncing your fork on GitHub and pulling locally:

    ```bash
    git pull origin main
    ```

8. **Push your branch** and open a pull request:

    ```bash
    git push origin feature/your-feature-name
    ```

    On the [Recursivist repository](https://github.com/ArmaanjeetSandhu/recursivist), choose "Pull Requests" > "New Pull Request", select "compare across forks", and pick your fork and branch.

## Describing a Pull Request

A good description answers three questions:

- What problem does it solve?
- How can it be tested?
- Are there any dependencies or breaking changes?

Maintainers may ask for changes; push further commits to the same branch to address the feedback.

## Community

- **[Issues](https://github.com/ArmaanjeetSandhu/recursivist/issues)**: bug reports, feature requests, and questions.
- **[Pull Requests](https://github.com/ArmaanjeetSandhu/recursivist/pulls)**: changes to the codebase or the documentation.

---

Thank you for contributing to Recursivist! Your efforts help make this project better for everyone.
