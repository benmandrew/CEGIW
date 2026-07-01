# Counterexample-Guided Interval Weakening (CEGIW)

> B.M. Andrew, L.A. Dennis, M. Fisher, and M. Farrell. *Counterexample-Guided Interval Weakening*. Rigorous State-Based Methods (ABZ) 2026.

[![DOI:10.1007/978-3-032-26752-8_1](https://img.shields.io/badge/DOI-10.1007%2F978.3.032.26752.8.1-82A9C8)](https://doi.org/10.1007/978-3-032-26752-8_1)
![Coverage](docs/coverage.svg)

This tool takes an ideal property in Metric Temporal Logic (MTL) that does not hold in the system, and either

- weakens it by modifying the intervals of the temporal operators such that it does hold,
- or deduces that no possible weakening exists.

You can run the the interval weakening algorithm on the included examples yourself by running

```bash
$ docker run benmandrew/cegiw
```

Or set up and run locally with [Nix](#development-environment):

```bash
$ nix develop -c python3 -m src.iterative_weaken --model models/foraging-robots-limit-search.smv --de-bruijn 0,1 --mtl 'G(resting_p -> F[1,3](resting_p))'
```

Note that the [De Bruijn index](https://en.wikipedia.org/wiki/De_Bruijn_index) specifies which interval in the formula is to be weakened.

## Development Environment

This repository provides a [Nix](https://nixos.org/) flake with a `devShell` supplying every tool the build needs: Python 3.13, `nuXmv 2.1.0`, SPIN, GCC, and `expect`. Enter it with:

```bash
$ nix develop
```

The first time you enter the shell it creates a `.venv` and installs the pinned Python dependencies from `dev-requirements.txt`. All commands below (`make fmt`, `make lint`, `make test`, `make docs`, `./case-studies.sh`) are run from inside this shell, e.g. `nix develop -c make test`.

If you'd rather not use Nix, install `nuXmv 2.1.0`, SPIN, and GCC yourself, then set up the Python environment directly:

```bash
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r dev-requirements.txt
```

## Artefacts

The [artefacts](artefacts/) directory contains the [preprint](artefacts/preprint.pdf), [full proofs](artefacts/proofs.pdf) of correctness and optimality, and [input data](artefacts/requirements/) for the interval-weakenable requirements in FRET case studies.

## Tools

CEGIW provides several commandline tools.

### `iterative_weaken.py`

Iteratively weaken an MTL formula on a model

Example:
```bash
$ python3 -m src.iterative_weaken --model model.pml --mtl 'G(a -> F[0,2](b))' --de-bruijn 0,1
Bound 20: [0,2] → [0,18] in 0.26 seconds
Bound 23: [0,18] → [0,25] in 12.64 seconds
Bound 27: [0,25] → Final weakened interval
Total time: 12.90 seconds
```

### `analyse_cex.py`

Determine the optimal weakening of an MTL formula to satisfy a given trace.

Example:
```bash
$ python3 -m src.analyse_cex --mtl 'G(a -> F[0,2](b))' --de-bruijn 0,1 -- trace.xml
[0,5]
```

### `mtl2ltlspec.py`

Convert an MTL formula to LTL, and print it in the correct format for the given model checker.

Example:
```bash
$ python3 -m src.mtl2ltlspec --model-checker SPIN --mtl 'G(a -> F[0,2](b))'
[] ((a -> (b || X ((b || X (b))))))

$ python3 -m src.mtl2ltlspec --model-checker NUXMV --mtl 'G(a -> F[0,2](b))'
G ((a -> (b || X ((b || X (b))))))
```

## Documentation

Code documentation can be found at https://benmandrew.com/docs/cegiw/.

## Tests and linting

Run these from inside the [Nix devShell](#development-environment) (`nix develop`, or prefix each command with `nix develop -c`):

```bash
# Format
$ make fmt
# Lint
$ make lint
# Build documentation
$ make docs
# Run tests
$ make test
```
