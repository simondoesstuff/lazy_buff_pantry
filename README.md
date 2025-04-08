# Lazy Buff Pantry 💪

An agent to automatically make weekly appointments
at the buff pantry. Runs purely at the network level -- no browser.

# Setup

Designed for MacOS; platform agnostic besides notifications.

1. To get the dependencies (uv),  
   `direnv allow` if you have `direnv` installed.  
   or `nix develop` if you have only `nix` installed.  

## config.json

**is required** and in the form:

```json
{
  "username": "?",
  "password": "?",
  "target": {
    "day": "Fri",
    "hour": 12
  },
  "phone_number": "+19998887777"
}
```

`phone_number` field is optional and macos only.

### Run with `uv run main.py`

or `uv run main.py | tee -a log` to run the script and tee the output to a log.  
or `./run.sh`

## Scheduled Registration

MacOS has a built-in scheduler called `launchd`, a parallel to `cron` on Linux.  
It can be used to automatically run the script at a specified time.

1. Create a `.plist` file in `~/Library/LaunchAgents/` that matches
[simondoesstuff.fastpantry.plist](./simondoesstuff.fastpantry.plist)

- Note the `sh -c` argument must point to the location of `run.sh` on your system.
  - `run.sh` uses nix.
- This example will run the script every Thursday at 10:00 AM.
  It will attempt to register at that time or as soon as the device is turned on after that time.

2. Load the `.plist` file with `launchctl load -w
    ~/Library/LaunchAgents/simondoesstuff.fastpantry.plist`
