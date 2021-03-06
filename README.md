# Manage OpenCast Series with Ufora interfacing

## Installation

```
$ pip install -r requirements.txt

$ pip install setup.py
```

## Development

This project includes a number of helpers in the `Makefile` to streamline common development tasks.

### Environment Setup

The following demonstrates setting up and working with a development environment:

```
### create a virtualenv for development

$ make virtualenv

$ source env/bin/activate


### run seriesmanager cli application

$ seriesmanager --help


### run pytest / coverage

$ make test
```


### Releasing to PyPi

Before releasing to PyPi, you must configure your login credentials:

**~/.pypirc**:

```
[pypi]
username = YOUR_USERNAME
password = YOUR_PASSWORD
```

Then use the included helper function via the `Makefile`:

```
$ make dist

$ make dist-upload
```

## Deployments

### Docker

Included is a basic `Dockerfile` for building and distributing `Ufora OpenCast Series Manager`,
and can be built with the included `make` helper:

```
$ make docker

$ docker run -it seriesmanager --help
```

## Usage

### Config file

Copy the config example from the config dir into your homedir with filename '.seriesmanager.yml' (make it a hidden file)

```
$ cp config/seriesmanager.yml.example ~/.seriesmanager.yml
```



### List all series in OpenCast

```
|> seriesmanager <|  $ seriesmanager series list
```

### Create OpenCast series

prd_fulldump_pretty_20190911.json is the Ufora courses dumpfile.

```
|> seriesmanager <|  $ seriesmanager series import-from-memory output/prd_fulldump_pretty_20190911.json
```
