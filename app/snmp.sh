#!/bin/bash

> output.txt

echo "----- $(date) DESCRIPTION UPDATE -----" >> log.txt

while IFS= read -r ip; do
    echo "-------------------------------------------------------"
    echo "Scanning interface ports on IP: $ip"
    echo "-------------------------------------------------------"

    # Label SNMP block by IP
    echo "SNMP output for $ip:" >> output.txt

#description
    snmpwalk -$SNMP_VERSION -c $COMMUNITY "$ip" .1.3.6.1.2.1.31.1.1.1.18 | \
    awk -F '.18.' 'NF > 1 {
        split($2, a, " = ");
        gsub(/STRING: /, "", a[2]);  # remove STRING:
        gsub(/"/, "", a[2]);         # remove quotes
        printf "D%s: \"%s\"\n", a[1], a[2];
    }' >> output.txt

    echo "Admin state" >> output.txt

#administrative state
    snmpwalk -$SNMP_VERSION -c $COMMUNITY -On "$ip" .1.3.6.1.2.1.2.2.1.7 | \
    awk -F '\\.7\\.' 'NF > 1 {
        split($2, a, " = ");
        gsub(/INTEGER: /, "", a[2]);  # remove INTEGER:
        gsub(/"/, "", a[2]);         # remove quotes
        printf "S%s: \"%s\"\n", a[1], a[2];
    }' >> output.txt

    echo "Link state" >> output.txt
#link state
    snmpwalk -$SNMP_VERSION -c $COMMUNITY -On "$ip" .1.3.6.1.2.1.2.2.1.8 | \
    awk -F '\\.8\\.' 'NF > 1 {
        split($2, a, " = ");
        gsub(/INTEGER: /, "", a[2]);  # remove INTEGER:
        gsub(/"/, "", a[2]);         # remove quotes
        printf "L%s: \"%s\"\n", a[1], a[2];
    }' >> output.txt

#mtu size
    echo "MTU size" >> output.txt
    snmpwalk -$SNMP_VERSION -c $COMMUNITY -On "$ip" .1.3.6.1.2.1.2.2.1.4 | \
    awk -F '\\.4\\.' 'NF > 1 {
        split($2, a, " = ");
        gsub(/INTEGER: /, "", a[2]);  # remove INTEGER:
        gsub(/"/, "", a[2]);         # remove quotes
        printf "M%s: \"%s\"\n", a[1], a[2];
    }' >> output.txt

#mtu size
    echo "Speed" >> output.txt
    snmpwalk -$SNMP_VERSION -c $COMMUNITY -On "$ip" 1.3.6.1.2.1.31.1.1.1.15 | \
    awk -F '\\.15\\.' 'NF > 1 {
        split($2, a, " = ");
        gsub(/Gauge32: /, "", a[2]);  # remove Gauge32:
        gsub(/"/, "", a[2]);         # remove quotes
        printf "G%s: \"%s\"\n", a[1], a[2];
    }' >> output.txt

    echo "" >> output.txt  # Add blank line between blocks
done < switches.txt


#-----------test----------
#python main_test.py --dry-run | tee -a log_test.txt
#----------launch---------
python main.py | tee -a log.txt



echo "Completed at $(date)" >> log.txt
