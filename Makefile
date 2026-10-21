.PHONY: all setup build clean

override base_version := $(shell sed -n 's/^version[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' pyproject.toml | head -n 1)

SHELL := /bin/bash
python := python3
venv := .venv
vpython := $(venv)/bin/python3
vpip := $(venv)/bin/pip3

ifneq ($(strip $(build_identifier)),)
override version := $(base_version)-$(build_identifier)
else
override version := $(base_version)
endif

build_heavy_optimize ?= 0
build_optimize ?= 0
build_lto ?= 0
build_use_clang ?= 0
build_no_quiet ?= 0
_build_flags ?=
ifeq ($(build_heavy_optimize),1)
$(warning building with heavy optimizations will take much longer!)
_build_flags += --python-flag=no_site,no_asserts --pgo-python --pgo-python-error-exit=yes --deployment
override build_lto := 1
else ifeq ($(build_optimize),1)
$(warning building with optimizations will take longer!)
_build_flags += --python-flag=no_site,no_asserts
endif
ifeq ($(build_lto),1)
_build_flags += --lto=yes
endif
ifeq ($(build_use_clang),1)
_build_flags += --clang
endif
ifeq ($(build_no_quiet),0)
_build_flags += --quiet
endif
ifdef build_target_arch
_build_flags += --target-arch=$(build_target_arch)
endif

all: build

.ONESHELL:
setup:
	@
	echo "running setup..."
	echo "setting up python venv... "
	$(python) -m venv $(venv)
	echo "installing project dependencies... "
	$(vpip) -q install -e .
	echo "ensuring nuitka is installed... "
	$(vpip) -q install nuitka
	IFS=. read major minor _ <<< "$$(python3 --version 2>&1 | cut -d' ' -f2)";
	if (( major < 3 || (major == 3 && minor < 14) )); then
		echo "your python version is below 3.14! installing zstandard package"
		$(vpip) -q install zstandard 
	fi
	echo "making build dir..."
	mkdir -p build

	echo "setup complete!"

build: setup
	@echo "building scmgr $(version) with nuitka"
	@$(vpython) -m nuitka \
		--force-runtime-environment-variable=SCMGR_BUILD_TIME_VERSION=$(version) \
		--product-name="scmgr" \
		--output-dir=build \
		--output-filename=scmgr \
		--mode=onefile \
		$(_build_flags) \
		src/scmgr.py

	@echo "moving built executable to dist/"
	@mkdir -p dist
	@rm -f dist/scmgr*
	@mv build/scmgr dist/

	@echo "build complete!"
	
clean:
	@echo "removing build/"
	@rm -r build