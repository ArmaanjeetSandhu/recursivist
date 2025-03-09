# Pattern Matching

This reference guide explains the pattern matching capabilities in Recursivist, covering both glob patterns and regular expressions.

## Pattern Types

Recursivist supports two types of patterns:

1. **Glob patterns** (default): Simple wildcard-based patterns familiar to shell users
2. **Regular expressions**: More powerful pattern matching syntax for complex cases

## Glob Patterns

By default, Recursivist uses glob patterns for matching files and directories.

### Glob Syntax

| Pattern  | Meaning                                       |
| -------- | --------------------------------------------- |
| `*`      | Matches any number of characters (except `/`) |
| `?`      | Matches a single character (except `/`)       |
| `[abc]`  | Matches one character in the brackets         |
| `[!abc]` | Matches one character not in the brackets     |
| `**`     | Matches any number of directories (recursive) |

### Glob Examples

| Pattern       | Matches                                  | Does Not Match             |
| ------------- | ---------------------------------------- | -------------------------- |
| `*.js`        | `app.js`, `utils.js`                     | `app.jsx`, `utils.ts`      |
| `*.test.js`   | `app.test.js`, `utils.test.js`           | `app.js`, `test.js`        |
| `src/*`       | `src/app.js`, `src/utils.js`             | `src/components/button.js` |
| `src/**/*.js` | `src/app.js`, `src/components/button.js` | `app.js`, `src/app.ts`     |
| `test?.js`    | `test1.js`, `testA.js`                   | `test.js`, `test10.js`     |
| `[abc]*.js`   | `a.js`, `b123.js`, `capp.js`             | `d.js`, `xyz.js`           |
| `[!abc]*.js`  | `d.js`, `xyz.js`                         | `a.js`, `b123.js`          |

### Using Glob Patterns

Glob patterns are used with the `--exclude-pattern` and `--include-pattern` options:

```bash
recursivist visualize --exclude-pattern "*.test.js" "*.spec.js"
recursivist visualize --include-pattern "src/**/*.js" "docs/*.md"
```

## Regular Expressions

For more complex pattern matching, you can use regular expressions by adding the `--regex` flag.

### Regex Syntax

Regular expressions in Recursivist follow Python's regex syntax. Some common elements:

| Pattern   | Meaning                                   |
| --------- | ----------------------------------------- |
| `.`       | Matches any character except newline      |
| `^`       | Matches the start of a string             |
| `$`       | Matches the end of a string               |
| `*`       | Matches 0 or more repetitions             |
| `+`       | Matches 1 or more repetitions             |
| `?`       | Matches 0 or 1 repetition                 |
| `\d`      | Matches a digit                           |
| `\w`      | Matches a word character                  |
| `\s`      | Matches a whitespace character            |
| `[abc]`   | Matches any character in the brackets     |
| `[^abc]`  | Matches any character not in the brackets |
| `a\|b`    | Matches either a or b                     |
| `(...)`   | Capture group                             |
| `(?:...)` | Non-capturing group                       |

Special characters need to be escaped with a backslash, e.g., `\.` to match a literal period.

### Regex Examples

| Pattern                       | Matches                        | Does Not Match                 |
| ----------------------------- | ------------------------------ | ------------------------------ |
| `^test_.*\.py$`               | `test_app.py`, `test_utils.py` | `app_test.py`, `test.py`       |
| `.*\.(spec\|test)\.(js\|ts)$` | `app.test.js`, `utils.spec.ts` | `app.js`, `test.js`            |
| `^src/.*\.jsx?$`              | `src/app.js`, `src/utils.jsx`  | `src/app.ts`, `lib/app.js`     |
| `^(?!.*test).*\.py$`          | `app.py`, `utils.py`           | `app_test.py`, `test_utils.py` |
| `\d+_.*\.log$`                | `123_server.log`, `2_app.log`  | `server.log`, `app_123.log`    |

### Using Regex Patterns

To use regular expressions, add the `--regex` flag:

```bash
recursivist visualize \
--exclude-pattern "^test_.*\.py$" ".*_test\.js$" \
--regex

recursivist visualize \
--include-pattern "^src/.*\.(jsx?|tsx?)$" \
--regex
```

## Pattern Precedence

When multiple patterns are specified, Recursivist applies them in the following order:

1. Include patterns (if specified, only matching files will be considered)
2. Exclude patterns (matching files are excluded)
3. Excluded extensions (files with matching extensions are excluded)
4. Excluded directories (directories matching these names are excluded)
5. Gitignore patterns (if specified, patterns from the ignore file are applied)

This means that include patterns have the highest precedence and can override all other exclusions.

## Combining Include and Exclude Patterns

You can use both include and exclude patterns together:

```bash
recursivist visualize \
--include-pattern "src/**/*.js" "docs/*.md" \
--exclude-pattern "**/node_modules/*" "**/*.min.js"
```

In this case, only files that match at least one include pattern will be considered, and among those, files matching any exclude pattern will be excluded.

## Pattern Matching in Different Commands

Pattern matching works the same way across all Recursivist commands:

- `visualize`: Control what files and directories are displayed
- `export`: Control what's included in the exported file
- `compare`: Control what's considered when comparing directories

## Advanced Pattern Examples

### Show Only Source Code

```bash
# Glob pattern
recursivist visualize \
--include-pattern "src/**/*"

# Regex pattern
recursivist visualize \
--include-pattern "^src/" \
--regex
```

### Exclude All Test Files

```bash
# Glob pattern
recursivist visualize \
--exclude-pattern "**/*.test.js" "**/*.spec.js" "test/**/*"

# Regex pattern
recursivist visualize \
--exclude-pattern ".*\.(test|spec)\.[jt]sx?$" "^test/" \
--regex
```

### Show Only Specific File Types

```bash
# Glob pattern
recursivist visualize \
--include-pattern "**/*.{js,jsx,ts,tsx}"

# Regex pattern
recursivist visualize \
--include-pattern ".*\.[jt]sx?$" \
--regex
```

### Complex Filtering with Regex

```bash
# Include JavaScript modules, exclude test files and minified files
recursivist visualize \
--include-pattern "^src/.*\.js$" \
--exclude-pattern ".*\.(test|spec)\.js$" ".*\.min\.js$" \
--regex
```

### Pattern Matching with File Statistics

To focus on important code metrics, combine pattern matching with file statistics:

```bash
# Find large source files
recursivist visualize \
--include-pattern "src/**/*.js" \
--sort-by-size

# Identify complex modules
recursivist visualize \
--include-pattern "src/**/*.py" \
--exclude-pattern "**/*test*.py" \
--sort-by-loc

# See recent changes to specific areas
recursivist visualize \
--include-pattern "src/components/**/*.jsx" \
--sort-by-mtime
```

### Filter Based on File Contents (Gitignore Style)

When using a gitignore-style file with the `--ignore-file` option, you can use patterns that work similarly to `.gitignore` files:

```bash
# .recursivist-ignore
*.log
node_modules/
**/dist/
*~
```

Then use it with:

```bash
recursivist visualize \
--ignore-file .recursivist-ignore
```

## Performance Considerations

- Glob patterns are generally faster than regex patterns
- Complex regex patterns can be slower on large directory structures
- Include patterns can improve performance by reducing the number of files to process

## Common Use Cases

### Development Project

```bash
recursivist visualize \
--exclude "node_modules .git build dist" \
--exclude-ext ".min.js .map"
```

### Documentation Project

```bash
recursivist visualize \
--include-pattern "**/*.md" "**/*.rst" "**/*.txt" "docs/**/*"
```

### Source Code Analysis

```bash
recursivist visualize \
--include-pattern "src/**/*" \
--exclude-pattern "**/*.test.js" "**/*.spec.js"
```

### Backend Development

```bash
recursivist visualize \
--include-pattern "**/*.py" "**/*.go" "**/*.java" \
--exclude-pattern "**/*_test.py" "**/*_test.go" "**/*Test.java"
```

## Troubleshooting Pattern Matching

If your patterns aren't working as expected:

1. **Use verbose mode**: Run with `--verbose` to see detailed logging about pattern matching
2. **Test simpler patterns first**: Start with basic patterns and build up complexity
3. **Check pattern syntax**: Ensure you're using the correct syntax for glob or regex
4. **Remember path conventions**: Patterns match against relative paths from the root directory
5. **Check precedence**: Remember that include patterns override exclude patterns

For debugging complex regex patterns, consider testing them in a regex tool like [regex101.com](https://regex101.com/) before using them in Recursivist.
