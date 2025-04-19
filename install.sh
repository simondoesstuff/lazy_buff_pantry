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

ln -s "$localDir/$plist.plist" "$plist.plist"
launchctl load -w "$plist.plist"
echo "installed"
echo $(launchctl list | grep "$plist")
echo "uninstall with -u"
echo "manual test with -t"
