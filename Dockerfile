FROM squidfunk/mkdocs-material:latest

# Install additional plugins required by our mkdocs configuration
RUN pip install \
    mkdocs-git-revision-date-localized-plugin \
    mkdocstrings[python]