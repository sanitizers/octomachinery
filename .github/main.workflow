workflow "Publish Python package distribution to PyPI if it's tagged" {
  on = "deployment"
  resolves = [
    "Publish 📦 to Test PyPI",
    "Debug env",
  ]
}

action "Make sdist and wheel" {
  uses = "./.github/actions/python3.7-tox"
  env = {
    TOXENV = "build-dists"
  }
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

action "Debug env" {
  uses = "actions/bin/debug@master"
}
