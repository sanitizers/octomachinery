FROM python:3.7-slim

LABEL maintainer "Sviatoslav Sydorenko <wk+github-actions@sydorenko.org.ua>"
LABEL repository https://github.com/sanitizers/octomachinery/tree/master/.github/actions/python3.7-tox
LABEL homepage https://github.com/sanitizers/octomachinery/tree/master/.github/actions/python3.7-tox

LABEL com.github.actions.name python3.7-tox
LABEL com.github.actions.description "Run a tox under Python 3.7"
LABEL com.github.actions.icon code
LABEL com.github.actions.color blue

# Install Git
    # \
RUN set -ex \
        \
        && apt-get update \
        && apt-get install -y --no-install-recommends \
            git \
        && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
        && rm -rf /var/lib/apt/lists/*

# Install the newest tox
RUN pip install -U tox

ENTRYPOINT ["python", "-m", "tox"]
CMD []
