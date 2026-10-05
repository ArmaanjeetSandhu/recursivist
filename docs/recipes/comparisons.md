# Comparing Versions, Branches, and Builds

Practical uses of `compare`. For how to read the output, see the [Compare guide](../user-guide/compare.md).

## Two Versions of a Project

```bash
recursivist compare project-v1.0 project-v2.0 \
  --exclude node_modules --exclude .git \
  --save --prefix v1-vs-v2 --sort-by-loc
```

`--save` writes `v1-vs-v2.html` instead of printing to the terminal, and `--sort-by-loc` annotates every file with its line count, so files that grew or shrank stand out.

## Two Branches

For a repository on GitHub, compare the branches directly, without cloning anything:

```bash
recursivist compare \
  https://github.com/owner/repo/tree/main \
  https://github.com/owner/repo/tree/develop \
  --save --prefix main-vs-develop
```

For a local repository, check each branch out into its own directory first:

```bash
git clone -b main repo main-branch
git clone -b feature/new-feature repo feature-branch

recursivist compare main-branch feature-branch \
  --exclude node_modules --exclude .git \
  --save --prefix branch-comparison --sort-by-loc
```

## A Fork Against Its Upstream

```bash
recursivist compare ./my-fork https://github.com/owner/repo
```

In a mixed comparison like this one, `--git-status` still annotates the local side. See [GitHub Repositories](../user-guide/github-repositories.md#comparing-with-a-github-repository) for what applies to each side.

## Source Against Build Output

```bash
recursivist compare src dist --include-pattern "*.js" --save --sort-by-size
```

## Verifying a Backup

```bash
recursivist compare original-files backup-files --full-path --save --sort-by-size
```

## In Continuous Integration

GitHub Actions steps that check out a pull request and `main` side by side, compare them, and upload the result as an artifact:

```yaml
- uses: actions/checkout@v4
  with:
      path: pr-branch

- uses: actions/checkout@v4
  with:
      ref: main
      path: main-branch

- uses: actions/setup-python@v5
  with:
      python-version: "3.12"

- run: pip install recursivist

- name: Compare structures
  run: |
      recursivist compare main-branch pr-branch \
        --exclude node_modules --exclude .git \
        --save --prefix structure-diff --sort-by-loc

- uses: actions/upload-artifact@v4
  with:
      name: structure-comparison
      path: structure-diff.html
```
