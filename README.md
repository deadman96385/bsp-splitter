# BSP Split script

Takes a BSP that does not contain aosp git history and overlays the OEM's changes on top of aosp so that all the changes that were done can be more easily tracked.

## Installation

1. Clone the repo 
2. Install GitHub's CLI tool called [gh](https://cli.github.com/)
3. Authenticate with GitHub using `gh auth login` and grant the tool `repo` scopes.

## Usage

### 1. Splitting a BSP
To split a local BSP directory and push the modified repositories to a GitHub organization, run `splitter.py`.

```bash
python3 splitter.py -p /path/to/bsp/ -o your-github-org -c "Add BSP Changes" -b "my-branch-name"
```

*If the pipeline fails midway or you need to recover an unattended run without restarting, you can pass the `--resume` flag with the path to the previously generated results JSON:*
```bash
python3 splitter.py -p /path/to/bsp/ -o your-github-org -c "Add BSP Changes" -b "my-branch-name" --resume output/results_20260410-014226.json
```

### 2. Generating a Repo Manifest
Once `splitter.py` successfully finishes, use `manifest_generator.py` to create a custom `default.xml` repo manifest that links all your customized GitHub forks together using the official AOSP manifest as a baseline.

```bash
python3 manifest_generator.py --results output/results_20260410-014226.json --branch "my-branch-name" --org "your-github-org"
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
