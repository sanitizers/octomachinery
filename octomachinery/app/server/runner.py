"""Octomachinery CLI runner."""

from ..github import GitHubApplication as _GitHubApplication


run = _GitHubApplication.run_simple
