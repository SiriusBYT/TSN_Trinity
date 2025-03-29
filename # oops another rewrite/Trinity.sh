clear
echo [Trinity Relay] Script Started
cd /System/Services/Trinity-Relay
while :
do
	echo [Trinity Relay] Info: Launching the Trinity Relay...
	python3 Trinity.py
	echo [Trinity Relay] WARNING: A SERVERE Server error has occured ! Restarting server automatically in 10 seconds.
	sleep 10
done
echo [Trinity Relay] Goodbye.
