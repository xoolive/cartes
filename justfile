# Bump pyproject.toml, commit, tag, and push a release tag.
# Usage: just release patch|minor|major|0.8.6
release bump:
    #!/usr/bin/env bash
    set -euxo pipefail
    test -z "$(git status --porcelain)"
    case "{{bump}}" in
      patch|minor|major) uv version --bump "{{bump}}" ;;
      *) uv version "{{bump}}" ;;
    esac
    VERSION="$(uv version --short)"
    test -z "$(git tag -l v${VERSION})"
    git add pyproject.toml uv.lock
    git commit -m "bump version to ${VERSION}"
    git tag "v${VERSION}"
    git push origin master "v${VERSION}"
