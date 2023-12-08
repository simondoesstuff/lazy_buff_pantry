#!/bin/bash

run='./node_modules/cypress/bin/cypress run'

echo "I'm getting to work!"

for i in 1 2 3
do

	$run

	if [ $? -eq 0 ]; then
		echo "Registered! 🎉"
		osascript -e 'display notification "I am all done registering! 😊" with title "Lazy Buff Pantry 💪"'
		exit 0
	else
		echo "Didn't work. :/ Trying again..."
	fi
done

echo "Giving up. :/"
exit 1
