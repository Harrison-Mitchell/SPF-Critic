#!/bin/bash

rm -f IPs.txt

echo -n "Pulling user-registrable GCP CIDRs... "
curl -s https://www.gstatic.com/ipranges/cloud.json | jq . | grep ipv4Prefix | cut -d '"' -f 4 | sed -e 's/$/|GCP/' >> IPs.txt
echo "done"

echo -n "Pulling user-registrable AWS CIDRs... "
curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | jq -r '.prefixes[] | select(.service=="EC2") | .ip_prefix' | sed -e 's/$/|AWS/' >> IPs.txt
echo "done"

echo -n "Pulling user-registrable Azure CIDRs... "
curl -s https://download.microsoft.com/download/7/1/D/71D86715-5596-4529-9B13-DA13A5DE5B63/ServiceTags_Public_20220110.json | jq -r '.values[] | select(.name | contains("AzureCloud")) | .properties.addressPrefixes | join("\n")' | grep -v '::' | sed -e 's/$/|Azure/' >> IPs.txt
echo "done"

echo -n "Pulling user-registrable Digital Ocean CIDRs... "
curl -s https://www.digitalocean.com/geo/google.csv | grep -v '::' | cut -d , -f 1 | sed -e 's/$/|DigitalOcean/' >> IPs.txt
echo "done"

echo -n "Pulling user-registrable Oracle Cloud CIDRs... "
curl -s https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json | grep 'cidr":' | cut -d '"' -f 4 | sed -e 's/$/|OracleCloud/' >> IPs.txt
echo "done"

echo Pulled `wc -l IPs.txt` CIDRs