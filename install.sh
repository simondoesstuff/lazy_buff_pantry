#!/bin/bash

# set -e

plist="simondoesstuff.fastpantry"
cd $(dirname "$0")
localDir="$(pwd)"

getopts "ut" opts
if [ "$opts" == "t" ]; then
  launchctl start "$plist"
  tail -f "$localDir/log"
  exit 0
fi

cd "$HOME/Library/LaunchAgents"
rm -f "$plist.plist"

daemons=$(launchctl list | grep "$plist")
if [ "$daemons" ]; then
  launchctl remove "$plist"
fi

if [ "$opts" == "u" ]; then
  echo "uninstalled"
  exit 0
fi

if [ ! -f "$localDir/config.json" ]; then
  echo "config.json set up..."
  echo -n " - username: " && read username
  echo -n " - password: " && read password
  echo -n " - day (eg tues): " && read day
  echo -n " - hour (eg 13): " && read hour
  echo -n " - phone number (eg +19998887777): " && read phone
  o="$localDir/config.json"
  echo "{" > "$o"
  echo "\"username\": \"$username\"," >> "$o"
  echo "\"password\": \"$password\"," >> "$o"
  echo "\"target\": {" >> "$o"
  echo "\"day\": \"$day\"," >> "$o"
  echo "\"hour\": $hour" >> "$o"
  echo "}," >> "$o"
  echo "\"phone_number\": \"$phone\"" >> "$o"
  echo "}" >> "$o"
fi

ln -s "$localDir/$plist.plist" "$plist.plist"
launchctl load -w "$plist.plist"
echo "installed"
echo $(launchctl list | grep "$plist")
echo "uninstall with -u"
echo "manual test with -t"
