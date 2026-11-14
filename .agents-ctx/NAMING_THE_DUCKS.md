# Naming the Ducks

Canonical names for this project, and how to refer to it in
prose. Other files in `.agents-ctx/` (and any generated content)
should say "the project" rather than hardcoding one of these --
reach for a specific name only when the distinction actually
matters (e.g. citing a package, an import, or a repository URL).

## Distribution / PyPI name: `octomachinery`

The installable, published name -- recorded in `setup.cfg`'s
`[metadata]` `name`. This is also the preferred way to refer to
the project by name in prose.

## Python import name: `octomachinery`

The same as the distribution name.

## GitHub repository slug: `sanitizers/octomachinery`

Use it verbatim when it's actually the repository being
referenced (URLs, `gh` invocations, PR/issue citations) -- not as
a stand-in for the project's name in prose. The documentation
lives at <https://octomachinery.dev>.

## Don't confuse it with the apps built on it

GitHub Apps like `sanitizers/chronographer-github-app` and
`sanitizers/patchback-github-app` are built on octomachinery, but
they're separate projects in their own repositories. Say which one
is meant.
