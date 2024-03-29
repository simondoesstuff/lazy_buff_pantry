# Lazy Buff Pantry 💪

Web scraping agent to automatically make weekly appointments
at the buff pantry.

# Setup

Designed for MacOS, but the agent itself is based on Cypress
with NodeJS so it should be very portable.

1. To get the dependencies, use `npm install`

## cypress/e2e/registerAppt/config.json
**is required** and in the form:
```
{
  "identiKey": "...",
  "password": "...",
  "logFile": "log.txt",
  "minDayGap": "4",
  "times": [
    {
      "day": "Tue",
      "t1": "1:00pm",
      "t2": "2:00pm"
    },
    {
      "day": "Fri",
      "t1": "3:00pm",
      "t2": "4:00pm"
    },
    {
      "day": "Fri",
      "t1": "3:30pm",
      "t2": "4:00pm"
    }
  ]
}
```
where `day` is one of `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, `Sun`,
and `t1` and `t2` represent the start and end times of the appointment.

The `minDayGap` is the minimum number of days between appointments.
It is used to prevent registering for multiple appointments in the same week.

**You must manually create the (empty) log file** as specified in the config.
The agent will not create it for you. This is due to the way Cypress handles
file creation.

### Registration Algorithm:
1. It will only register for one appointment per day.
2. If there is already a registration for that day, it will not register.
3. If there has already been a recent(minDayGap) registration, it will not register.
4. If there are multiple available appointments that meet the criteria,
it will register in priority order of the `times` array.
5. It will only register for future appointments (after the previously registered appointment).

### Run with [./register_buff_pantry.sh](./register_buff_pantry.sh) 

## Scheduled Registration

MacOS has a built-in scheduler called `launchd`, a parallel to `cron` on Linux.
It can be used to automatically run the script at a specified time.
1. Create a `.plist` file in `~/Library/LaunchAgents/` with the following contents:
```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>org.author.buff_pantry</string>
    <key>ProgramArguments</key>
    <array>
            <string>/buff_pantry/register_buff_pantry.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>10</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>4</integer>
    </dict>
</dict>
</plist>
```

- Note line `string>/buff_pantry/register_buff_pantry.sh</string>` will
need to contain the appropriate path to the script on your machine.
- This example will run the script every Thursday at 10:00 AM. By the nature
of launchd, it will attempt to register at that time or as soon as
the device is turned on after that time.

2. Load the `.plist` file with `launchctl load ~/Library/LaunchAgents/org.author.buff_pantry.plist`  
-- or the appropriate name/path to the `.plist` file on your machine.
