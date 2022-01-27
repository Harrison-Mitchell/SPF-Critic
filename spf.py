import ipaddr
from sys import argv
from os.path import isfile
from dns.resolver import resolve, NXDOMAIN

recurStr = []
rawSPF = []
totalIPs = 0
lookups = 1
badCIDRs = []
CIDRs = []
CIDRmaps = {}
# spf.protection.outlook.com has false positives for these CIDRs
FPCIDRs = ["40.92.0.0/15", "52.100.0.0/14"]
platformLinks = {
	"GCP": "https://cloud.google.com/compute/docs/faq#find_ip_range",
	"AWS": "https://docs.aws.amazon.com/general/latest/gr/aws-ip-ranges.html",
	"Azure": "https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519",
	"DigitalOcean": "https://docs.digitalocean.com/products/platform/",
	"OracleCloud": "https://docs.oracle.com/en-us/iaas/Content/General/Concepts/addressranges.htm"
}

if not isfile("IPs.txt"):
	exit("Run ./refreshIPs.sh to pull latest public CIDR lists")

if len(argv) <= 1:
	exit("Usage: python3 spf.py example-domain.com")

# ./refreshIPs delimits by |, so split and load into python array and dict
with open("IPs.txt", "r") as rawCIDRs:
	lines = rawCIDRs.read().split("\n")
	for line in lines[:-1]:
		cidr, platform = line.split("|")
		CIDRs.append(ipaddr.IPNetwork(cidr))
		CIDRmaps[cidr] = platform

# Grab just the hostname in case a URL is supplied
domain = argv[1].strip("/").replace("https://", "")

def paintY(s): return f"\033[93m{s}\033[00m"
def paintB(s): return f"\033[44m{s}\033[00m"
def paintR(s): return f"\033[41m{s}\033[00m\033[93m"
def info(title, desc): print(f"\033[44m{title}\033[00m - {desc}")
def warn(title, desc): print(f"\033[43m{title}\033[00m - {desc}")
def crit(title, desc): print(f"\033[41m{title}\033[00m - {desc}")

# DNS resolves, filters for SPF records  and cleans them up
def PullSPF(host):
	try:
		recs = resolve(host, "TXT", raise_on_no_answer=False)
	except NXDOMAIN:
		return "HOSTNAME_COULD_NOT_BE_RESOLVED"
	spfRecs = [str(r) for r in recs if "v=spf1" in str(r)]
	return spfRecs[0].replace('" "',"").replace('"', "").strip() if spfRecs else ""

# Recursive function to pull SPF records and collect stats
def RecurseSPF(host, depth=0):
	# Globals because otherwise you have to pass it with the recursion and... eh
	global recurStr, totalIPs, lookups
	spf = PullSPF(host)
	print(f"Resolving {host}..." + " " * 20, end="\r")

	# Structure pretty print
	recurStr.append("    " * (depth * 1) + f"{paintB(host)}'s SPF record is:\n")
	recurStr.append(paintY("    " * (depth * 1) + "  " + spf + "\n"))

	# For each piece in the resolved record
	for part in spf.split(" "):
		if part.startswith("ip4"):
			cidr = part.replace("=", ":").split(":")[1]
			# If it's a single IP then there's no overtake harm (unless IP lease has lapsed)
			if "/" not in part or "/32" in part:
				totalIPs += 1
			else:
				partCIDR = ipaddr.IPNetwork(cidr)
				totalIPs += partCIDR.numhosts
				# For every SPF CIDR, check if it overlaps public IP CIDRs
				for CIDR in CIDRs:
					if partCIDR.overlaps(CIDR) and cidr not in FPCIDRs:
						recurStr[-1] = recurStr[-1].replace(cidr, paintR(cidr))
						badCIDRs.append([cidr, str(CIDR)])
						break

		# The two causes for an recursive resolution
		if part.startswith("include") or part.startswith("redirect"):
			lookups += 1
			host = part.replace("=", ":").split(":")[1]
			RecurseSPF(host, depth + 1)

# Actually resolve the passed hostname and pretty print
RecurseSPF(domain)
print(" " * 40 + "\r" + "\n".join(recurStr))

# No SPF record
if totalIPs == 0 and "v=spf1 -all" not in "".join(recurStr):
	crit("No SPF record is defined", "Mail can be easily spoofed for this domain. Either implement a record, or explicitly set a no-send record or domains not designed to send mail: 'v=spf1 -all'")
else:
	info("SPF record is defined", "Spoofed mail is somewhat prevented")

# Too many permitted senders
if totalIPs > 1000000:
	crit(f"{totalIPs} IPs are permitted senders", "Regularly review your SPF record to ensure the record is as least-permissive as possible")
elif totalIPs > 10000:
	warn(f"{totalIPs} IPs are permitted senders", "Regularly review your SPF record to ensure the record is as least-permissive as possible")
elif totalIPs > 0:
	info(f"{totalIPs} IPs are permitted senders", "Regularly review your SPF record to ensure the record is as least-permissive as possible")

# Too many DNS lookups - invalid
if lookups > 10:
	crit(f"{lookups} DNS lookups were made", "Most clients refuse and ignore SPF records that result in more than 10 DNS lookups")
else:
	info(f"{lookups} DNS lookup(s) were made", "More than 10, and the record would be invalid")

# Non resolvable hostname
if "HOSTNAME_COULD_NOT_BE_RESOLVED" in "".join(recurStr):
	crit("A hostname could not be resolved", "The entire SPF record may be ignored by clients")
else:
	info("All hostnames were resolved", "An irresolvable hostname may invalidate the entire record")

# No hard fail
if recurStr[1].endswith("all") and not recurStr[1].endswith("-all"):
	warn(f"{recurStr[1][-4:]} directive leaves action ambiguous", "Without a hard fail '-all' directive, mail clients will not take firm actions against spoofed mail")
elif recurStr[1].endswith("-all"):
	info("'-all' directive is in use", "Mail clients know to hard fail spoofed mail")

# EC2 etc. CIDRs are present
if badCIDRs:
	crit("Permitted ranges are public-obtainable", "This record contains CIDR ranges for IPs adversaries can obtain, allowing them to bypass SPF and spoof email for your domain")
	for CIDR in badCIDRs:
		print(f"    {CIDR[0]} overlaps {CIDR[1]} ({CIDRmaps[CIDR[1]]}) {platformLinks[CIDRmaps[CIDR[1]]]}")
else:
	info("No common public-obtainable IP ranges exist", "E.g no EC2, Digital Ocean etc. IP ranges are present in the record that would allow adversaries to bypass SPF")