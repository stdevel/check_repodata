check_repodata
==============

``check_repodata.py`` is a Nagios / Icinga plugin for checking sync states of repositories managed by Spacewalk, Red Hat Satellite or SUSE Manager. It can assist you detecting outdates repositories and ``taskomaticd`` issues. The script checks file system timestamps and - optionally - YUM repo sync states that are queried using the Spacewal API. If using this features (*which is the default*) a valid username / password combination to your Spacewalk, Red Hat Satellite or SUSE Manager system is required. The login credentials **are prompted** when running the script. To automate this you have two options:

**1.Setting two shell variables:**
* **SATELLITE_LOGIN** - a username
* **SATELLITE_PASSWORD** - the appropriate password

You might also want to set the HISTFILE variable (*depending on your shell*) to hide the command including the password in the history:
```
$ HISTFILE="" SATELLITE_LOGIN=mylogin SATELLITE_PASSWORD=mypass ./check_repodata.py -l centos6-x86_64
```

**2.Using an authfile**

A better possibility is to create a authfile with permisions **0600**. Just enter the username in the first line and the password in the second line and hand the path to the script:
```
$ ./check_repodata.py -a myauthfile -l centos6-x86_64
```


Parameters
==========

```
$ ./check_repodata.py -h
Usage: check_repodata.py [options]

check_repodata.py is used to check repo sync states of content synchronized
with Spacewalk, Red Hat Satellite and SUSE Manager. Login credentials are
assigned using the following shell variables:
SATELLITE_LOGIN username
SATELLITE_PASSWORDpassword
It is also possible to create an authfile (permissions 0600) for usage with this
script. The first line needs to contain the username, the second line should
consist of the appropriate password. If you're not defining variables or an
authfile you will be prompted to enter your login information.
Checkout the GitHub page for updates:
https://github.com/stdevel/check_repodata

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -a FILE, --authfile=FILE
                        defines an auth file to use instead of shell variables
  -s SERVER, --server=SERVER
                        defines the server to use
  -d, --debug           enable debugging outputs
  -r, --repodata-only   only checks repodata on file system, skipping Yum sync
                        state inside Spacewalk
  -l CHANNELS, --channels=CHANNELS
                        defines one or more channels that should be checked
  -w THRESHOLD, --warning-threshold=THRESHOLD
                        warning threshold in hours (default: 24)
  -c THRESHOLD, --critical-threshold=THRESHOLD
                        critical threshold in hours (default: 48)
```



Examples
========
Check sync status for two repositories with default threshold (*warning: 24 hours, critical: 48 hours*). Login information are provided by an authfile ``myauthfile``:
```
$ ./check_repodata.py -l centos6-x86_64 -l epel-el6-x86_64 -a myauthfile
OK: Specified channels are synchronized: 'centos6-x86_64', 'epel-el6-x86_64'
```

Check sync status for two repositories (*alternative notation*) with custom thresholds, Spacewalk API checks are disabled:
```
$ ./check_repodata.py -l "centos6-x86_64,epel-el6-x86_64" -r -w 12 -c 24
WARNING: At least one channel is still syncing or outdated: 'centos6-x86_64'
```

Debugging repo sync state checks:
```
$ ./check_repodata.py -l epel-el6-x86_64 -d
OPTIONS: {'authfile': '', 'warningThres': 24, 'criticalThres': 48, 'server': 'localhost', 'channels': ['epel-el6-x86_64'], 'repodataOnly': False, 'debug': True}
ARGUMENTS: []
DEBUG:  ['epel-el6-x86_64']
DEBUG: prompting for login credentials
Username: admin
Password:
...
DEBUG: Yum sync difference for channel 'epel-el6-x86_64' is 12 hours
DEBUG: Difference for /var/cache/rhn/repodata/epel-el6-x86_64/repomd.xml is 12 hours
ERRORS: []
OK: Specified channels are synchronized: 'epel-el6-x86_64'
```
