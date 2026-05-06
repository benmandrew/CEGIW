# Counterexample-Guided Interval Weakening (CEGIW)

![Coverage](docs/coverage.svg)

This project takes an ideal property in Metric Temporal Logic (MTL) that does not hold in the system, and weakens it by modifying the intervals of the temporal operators such that it either does hold, or deduces that no possible weakening exists.

You can run the the interval weakening algorithm on the included examples yourself by running

```bash
$ docker run benmandrew/cegiw
```

Or set up and run locally, making sure you have `nuXmv 2.1.0` installed, with

```bash
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r dev-requirements.txt
$ python3 -m src.iterative_weaken --model models/foraging-robots-limit-search.smv --de-bruijn 0,1 --mtl 'G(resting_p -> F[1,3](resting_p))'
```

Note that the De Bruijn index ([wikipedia](https://en.wikipedia.org/wiki/De_Bruijn_index)) specifies which interval in the formula is to be weakened.

## Artefacts

The [artefacts](artefacts/) directory contains full proofs of correctness and optimality, as well as input data for the interval-weakenable requirements in FRET case studies.

## Tools

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

### Tests and linting

```bash
# Format
$ make fmt
# Lint
$ make lint
# Run tests
$ make test
```
