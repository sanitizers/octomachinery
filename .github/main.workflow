workflow "Publish Python package distribution to PyPI if it's tagged" {
  on = "deployment"
  resolves = ["Publish dists to PyPI", "Publish 📦 to Test PyPI"]
}

action "Check if it's a tagged Git commit" {
  uses = "actions/bin/filter@master"
  args = "tag"
}

action "Make sdist and wheel" {
  uses = "docker://randomknowledge/docker-pyenv-tox"
  needs = ["Check if it's a tagged Git commit"]
  args = "tox -ebuild-dists"
}

action "Publish dists to PyPI" {
  uses = "re-actors/pypi-action@master"
  needs = ["Make sdist and wheel"]
  env = {
    TWINE_USERNAME = "octomachinery-bot"
  }
  secrets = ["TWINE_PASSWORD"]
}

action "Publish 📦 to Test PyPI" {
  uses = "re-actors/pypi-action@master"
  needs = ["Make sdist and wheel"]
  env = {
    TWINE_USERNAME = "octomachinery-bot"
    TWINE_REPOSITORY_URL = "https://test.pypi.org/legacy/"
  }
  secrets = ["TWINE_PASSWORD"]
}
