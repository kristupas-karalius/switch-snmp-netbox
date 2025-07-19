# switch-snmp-netbox
Takes info from Switch via SNMP and updates it on Netbox

Add the list of switches to /app/switches.txt

It takes info from switches via snmpwalk, cleans and saves the info inside the .txt, finds the corresponding switches IP (main) address inside of Netbox and updates the interfaces information according to the switches interface no.

Updates: interfaces description, administrative state, link state, mtu size, speed.

set up "docker compose up --build" cron for automatic info renewal.
