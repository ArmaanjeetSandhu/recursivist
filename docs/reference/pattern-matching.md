# Pattern Matching

This reference covers the glob and regular-expression syntax used by `--exclude-pattern` and `--include-pattern`. For how these interact with the other filtering options, see [Pattern Filtering](../user-guide/pattern-filtering.md).

## What Patterns Match

`--exclude-pattern` and `--include-pattern` test each file's **name** (its basename), evaluated at every level of the tree. They do **not** match against paths.

!!! warning "Use the right tool for paths"
A pattern that contains a path separator, such as `src/*` or `src/**/*.js`, matches nothing — file names never contain a `/`. A pattern like `*.js` matches `.js` files at **any** depth. To filter by location, use a directory exclusion (`--exclude`) or a gitignore-style [ignore file](../user-guide/pattern-filtering.md#ignore-files), which _do_ match paths.

Patterns are globs by default. Add `--regex` to interpret them as Python regular expressions instead.

## Glob Patterns

### Syntax

| Pattern  | Meaning                                  |
| -------- | ---------------------------------------- |
| `*`      | Matches any run of characters            |
| `?`      | Matches a single character               |
| `[abc]`  | Matches one character listed in brackets |
| `[!abc]` | Matches one character not listed         |

### Examples

| Pattern      | Matches                     | Does Not Match           |
| ------------ | --------------------------- | ------------------------ |
| `*.js`       | `app.js`, `utils.js`        | `app.jsx`, `utils.ts`    |
| `*.test.js`  | `app.test.js`, `db.test.js` | `app.js`, `test.js`      |
| `test_?.py`  | `test_1.py`, `test_a.py`    | `test_.py`, `test_10.py` |
| `[abc]*.js`  | `a.js`, `b123.js`           | `d.js`, `xyz.js`         |
| `[!abc]*.js` | `d.js`, `xyz.js`            | `a.js`, `b123.js`        |

### Usage

```bash
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"
recursivist visualize --include-pattern "*.py" "*.md"
```

## Regular Expressions

With `--regex`, patterns follow Python's regex syntax and are searched within the file name. Anchor with `^` and `$` to match the whole name.

### Common Syntax

| Pattern   | Meaning                      |
| --------- | ---------------------------- |
| `.`       | Any character except newline |
| `^`       | Start of the name            |
| `$`       | End of the name              |
| `*`       | Zero or more repetitions     |
| `+`       | One or more repetitions      |
| `?`       | Zero or one repetition       |
| `\d`      | A digit                      |
| `\w`      | A word character             |
| `[abc]`   | Any listed character         |
| `[^abc]`  | Any character not listed     |
| `a\|b`    | Either `a` or `b`            |
| `(?:...)` | Non-capturing group          |

Escape special characters with a backslash, e.g. `\.` for a literal dot.

### Examples

| Pattern                       | Matches                        | Does Not Match               |
| ----------------------------- | ------------------------------ | ---------------------------- |
| `^test_.*\.py$`               | `test_app.py`, `test_utils.py` | `app_test.py`, `test.py`     |
| `.*\.(spec\|test)\.(js\|ts)$` | `app.test.js`, `db.spec.ts`    | `app.js`, `test.js`          |
| `^(?!.*test).*\.py$`          | `app.py`, `utils.py`           | `test_app.py`, `app_test.py` |
| `\d+_.*\.log$`                | `123_server.log`, `2_app.log`  | `server.log`, `app_123.log`  |

### Usage

```bash
recursivist visualize --exclude-pattern "^test_.*\.py$" ".*_test\.js$" --regex
recursivist visualize --include-pattern ".*\.[jt]sx?$" --regex
```

## Precedence

When include and exclude patterns are combined with other filters, exclude patterns and excluded extensions take priority over include patterns, and include patterns take priority over ignore-file patterns. See [Pattern Filtering](../user-guide/pattern-filtering.md#order-of-precedence) for the full order.

## Performance

Glob patterns are slightly cheaper than regular expressions. Include patterns can speed up large scans by narrowing the set of files that need to be considered.

## Troubleshooting

If a pattern isn't behaving as expected:

1. Remember that patterns match the **file name**, not the path. If you meant to target a location, use `--exclude` or `--ignore-file`.
2. Run with `--verbose` to see how patterns are applied.
3. Anchor regular expressions with `^` and `$` when you want a whole-name match.
4. Test complex regular expressions in a tool like [regex101.com](https://regex101.com/) before using them.
