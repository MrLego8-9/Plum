# Plum
De-Dockerized coding style checker for Epitech projects


## Install

```sh
curl https://raw.githubusercontent.com/MrLego8-9/Plum/main/plum_install.sh | bash
```
### Requires
- Git
- Make
- GCC / G++
- CMake
- Python3
- Pip
- Pylint
- TCL
- Boost libs
- Docker (Only for installation)

### Supported Linux distributions
The current installer script will install the required dependencies for the following distributions:
- Ubuntu (Untested)
- Fedora
- Arch

### Docker
Plum is also available as a docker image for CI/CD purposes.
```shell
docker pull citro102/plum:latest
```

Using it for regular development is not recommended as it is slower than the de-dockerized version.
The image is updated every time a commit is added to the main branch. (Or when the coding style rules are updated)

## Usage

```sh
Usage of plum:
  --no-ignore
    Do not ignore files in .gitignore and .plumignore
  --no-status
    Always return with exit code 0
  --update
    Update Plum
  --update-rules
    Update the coding style rules
```

## What makes Plum faster than the dockerised version ?
Plum is faster for several reasons:
 - It doesn't pull the docker image every time you run it
 - It doesn't have to start and remove the docker container
 - The C coding style checker is compiled with optimization flags
 - The C coding style checks are ran in parallel