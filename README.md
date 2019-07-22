# Extended Pantheon for benchmarking congestion control schemes

This is an extended version of the Pantheon framework (<https://pantheon.stanford.edu>)
intended for running full emulated benchmarks on congestion control schemes.

## Disclaimer
This is research software. Our scripts will write to the file system in the
`pantheon` folder. We never run third party programs as root, but we cannot
guarantee they will never try to escalate privilege to root. In addition, with
the ramdisk option enabled, the first run after a reboot will ask for root
privileges for creating a ramdisk.

You might want to install dependencies and run the setup on your own, because
our handy scripts will install packages and perform some system-wide settings
(e.g., enabling IP forwarding, loading kernel modeuls) as root.
Please run at your own risk.

## Preparation
To clone this repository, run:

```
git clone https://github.com/StanfordSNR/pantheon.git
```

Many of the tools and programs run by the Pantheon are git submodules in the
`third_party` folder. To add submodules after cloning, run:

```
git submodule update --init --recursive  # or tools/fetch_submodules.sh
```

## Dependencies
We provide a handy script `tools/install_deps.sh` to install globally required
dependencies, but you might want to inspect the contents of this script and
install these dependencies by yourself. In particular, we created
the [Pantheon-tunnel](https://github.com/StanfordSNR/pantheon-tunnel)
that is required to instrument each scheme.

For those dependencies required by each congestion control scheme `<cc>`,
run `src/wrappers/<cc>.py deps` to print a dependency list. You could install
them by yourself, or run

```
src/experiments/setup.py --install-deps (--all | --schemes "<cc1> <cc2> ...")
```

to install dependencies required by all schemes or a list of schemes separated
by spaces. Please note that Pantheon only supports Python 2.7.

## Setup
After installing dependencies, run

```
src/experiments/setup.py [--setup] [--all | --schemes "<cc1> <cc2> ..."]
```

to set up supported congestion control schemes. `--setup` is required
to be run only once.

## Running the Benchmark
To bechnmark a scheme run

```
src/experiments/benchmark.py [scheme] (--verbose, --ramdisk=(true|false))
```

## Benchmark analysis
To analyze benchmark, run

```
src/analysis/benchmark_analysis (--data_dir=[dir])
```

## How to add your own congestion control
Adding your own congestion control to Pantheon is easy! Just follow these
steps:

1. Fork this repository.

2. Add your congestion control repository as a submodule to `pantheon`:

   ```
   git submodule add <your-cc-repo-url> third_party/<your-cc-repo-name>
   ```

   and add `ignore = dirty` to `.gitmodules` under your submodule.

3. In `src/wrappers`, read `example.py` and create your own `<your-cc-name>.py`.
   Make sure the sender and receiver run longer than 60 seconds; you could also
   leave them running forever without the need to kill them.

4. Add your scheme to `src/config.yml` along with settings of
   `name`, `color` and `marker`, so that `src/experiments/test.py` is able to
   find your scheme and `src/analysis/analyze.py` is able to plot your scheme
   with the specified settings.

5. Add your scheme to `SCHEMES` in `.travis.yml` for continuous integration testing.

6. Send us a pull request and that's it, you're in the Pantheon!
