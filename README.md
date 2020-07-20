# BSP Split script

Takes a BSP that does not contain aosp git history and overlays the OEM's changes on top of aosp so that all the changes that were done can be more easily tracked.

## Installation

1. Clone the repo 
2. Install Github's CLI tool called [Hub](https://github.com/github/hub#installation)
3. Create a oauth token on [github](https://github.com/settings/tokens)
4. Give it all of the repo scope
5. Create/Edit the file located at ~/.config/hub with the following format

```python
github.com:
- user: deadman96385
  oauth_token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  protocol: https
```

## Usage
TBD

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
