# SPF Critic

Audit your domain's SPF record, particularly for overtake and impersonation conditions. 

### Dependencies

* Python 3
* Curl

### Install

```
sudo python3 -m pip install -r requirements.txt
```

### Usage

Run `./refreshIPs.sh` to renew publicly-registrable CIDR ranges for various cloud platforms, then `python3 spf.py example.com` to audit an SPF policy.

### Checks

* Whether an SPF record (or no-send record exists)
* Whether the number of permitted senders is sane
* Whether the number of DNS lookups is within 10 (RFC requirement)
* Whether all hostnames are resolvable (RFC requirement)
* Whether fradulant mail is hard-failed (`-all`)
* Whether IPs overlap with cloud IPs members of the public can register (e.g EC2 IPs)

### Example (fictional)

```
$ python3 spf.py google.com

google.com's SPF record is:

  v=spf1 include:_spf.google.com ~all

    _spf.google.com's SPF record is:

      v=spf1 include:_netblocks.google.com include:_netblocks2.google.com include:_netblocks3.google.com ~all

        _netblocks.google.com's SPF record is:

          v=spf1 ip4:35.190.247.0/24 ip4:64.233.160.0/19 ip4:66.102.0.0/20 ip4:66.249.80.0/20 ip4:72.14.192.0/18 ip4:74.125.0.0/16 ip4:108.177.8.0/21 ip4:173.194.0.0/16 ip4:209.85.128.0/17 ip4:216.58.192.0/19 ip4:216.239.32.0/19 ~all

        _netblocks2.google.com's SPF record is:

          v=spf1 ip6:2001:4860:4000::/36 ip6:2404:6800:4000::/36 ip6:2607:f8b0:4000::/36 ip6:2800:3f0:4000::/36 ip6:2a00:1450:4000::/36 ip6:2c0f:fb50:4000::/36 ~all

        _netblocks3.google.com's SPF record is:

          v=spf1 ip4:172.217.0.0/19 ip4:172.217.32.0/20 ip4:172.217.128.0/19 ip4:172.217.160.0/20 ip4:172.217.192.0/19 ip4:172.253.56.0/21 ip4:172.253.112.0/20 ip4:108.177.96.0/19 ip4:35.191.0.0/16 ip4:130.211.0.0/22 ~all

SPF record is defined - Spoofed mail is somewhat prevented
328960 IPs are permitted senders - Regularly review your SPF record to ensure the record is as least-permissive as possible
5 DNS lookup(s) were made - More than 10, and the record would be invalid
All hostnames were resolved - An irresolvable hostname may invalidate the entire record
Permitted ranges are public-obtainable - This record contains CIDR ranges for IPs adversaries can obtain, allowing them to bypass SPF and spoof email for your domain
    172.217.32.0/20 overlaps 172.217.32.0/24 (Azure) https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519
```
