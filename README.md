# MediaViewer [![Docker Image CI](https://github.com/kyokley/MediaViewer/actions/workflows/publish.yml/badge.svg)](https://github.com/kyokley/MediaViewer/actions/workflows/publish.yml)
Website to track tv shows and movies

## Installation
All commands should be run from within a devenv shell. Before running any of the following commands, make sure to enter the shell with:
```bash
devenv shell
```

### Starting the Application
```bash
# Terminal 1 - Start PostgreSQL
up postgres

# Terminal 2 - Start Django Backend
run

# Terminal 3 - Start React Frontend
frontend-run
```

### Setting up test data
#### Clear current data
```bash
clear
```
#### Seed test data
```bash
seed-data
```
