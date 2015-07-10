#!/usr/bin/python

# check_repodata.py - a script for checking repo sync
# states of content synchronized with Spacewalk,
# Red Hat Satellite or SUSE Manager.
#
# 2014 By Christian Stankowic
# <info at stankowic hyphen development dot net>
# https://github.com/stdevel
#
# 2015 by Bernhard Lichtinger < lichtinger at lrz dot de >:
# * add new options -n and -p
# * correct calculation of time difference
# * only spaces for indentation thanks to reindent.py
# * add supported API version 16 for spacewalk-2.3
#

from optparse import OptionParser
import xmlrpclib
import os
import stat
import getpass
import time
import glob
import datetime

#list of supported API levels
supportedAPI = ["11.1","12","13","13.0","14","14.0","15","15.0","16"]

if __name__ == "__main__":
    #define description, version and load parser
    desc='''%prog is used to check repo sync states of content synchronized with Spacewalk, Red Hat Satellite and SUSE Manager. Login credentials are assigned using the following shell variables:

            SATELLITE_LOGIN  username
            SATELLITE_PASSWORD  password

            It is also possible to create an authfile (permissions 0600) for usage with this script. The first line needs to contain the username, the second line should consist of the appropriate password.
If you're not defining variables or an authfile you will be prompted to enter your login information.

            Checkout the GitHub page for updates: https://github.com/stdevel/check_repodata'''
    parser = OptionParser(description=desc,version="%prog version 0.2")

    #-a / --authfile
    parser.add_option("-a", "--authfile", dest="authfile", metavar="FILE", default="", help="defines an auth file to use instead of shell variables")

    #-s / --server
    parser.add_option("-s", "--server", dest="server", metavar="SERVER", default="localhost", help="defines the server to use")

    #-d / --debug
    parser.add_option("-d", "--debug", dest="debug", default=False, action="store_true", help="enable debugging outputs")

    #-r / --repodata-only
    parser.add_option("-r", "--repodata-only", dest="repodataOnly", default=False, action="store_true", help="only checks repodata on file system, skipping Yum sync state inside Spacewalk")

    #-l / --channels
    parser.add_option("-l", "--channels", dest="channels", action="append", metavar="CHANNELS", help="defines one or more channels that should be checked")

    #-e / --all-channels
    parser.add_option("-e", "--all-channels", dest="allChannels", action="store_true", default=False, help="checks all channels served by Spacewalk, Red Hat Satellite or SUSE Manager")

    #-x / --exclude-channels
    parser.add_option("-x", "--exclude-channels", dest="excludeChannels", action="append", metavar="CHANNELS", help="defines channels that should be ignored (in combination with -e / --all-channels)")

    #-w / --warning-threshold
    parser.add_option("-w", "--warning-threshold", dest="warningThres", metavar="THRESHOLD", type="int", default=24, help="warning threshold in hours (default: 24)")

    #-c / --critical-threshold
    parser.add_option("-c", "--critical-threshold", dest="criticalThres", metavar="THRESHOLD", type="int", default=48, help="critical threshold in hours (default: 48)")

    #-f / --full-output
    parser.add_option("-f", "--full-output", dest="fullOutput", action="store_true", default=False, help="displays the names of successfully synchronized channels")

    #-p / --positive-filter
    parser.add_option("-p", "--positive-filter", dest="positiveFilter", action="append", metavar="POSFILTER", help="only channels containing POSFILTER are checked. POSFILTER is evaluated before NEGFILTER (in combination with -e / --all-channels)")

    #-n / --negative-filter
    parser.add_option("-n", "--negative-filter", dest="negativeFilter", action="append", metavar="NEGFILTER", help="channels containing NEGFILTER are ignored. NEGFILTER is evaluated after POSFILTER (in combination with -e / --all-channels)")

    # -o / --logical-and
    parser.add_option("-o", "--logical-and", dest="logicalAnd", action="store_true", default=False, help="if set, the check result is only not OK if all checked channels are not OK (e.g. taskkomatic is not running anymore.). Usefull if some of your channels do net get frequently updates")

    #parse arguments
    (options, args) = parser.parse_args()

    #define URL and login information
    SATELLITE_URL = "http://"+options.server+"/rpc/api"

    #debug outputs
    if options.debug: print "OPTIONS: {0}".format(options)
    if options.debug: print "ARGUMENTS: {0}".format(args)

    #initiate excludeChannels without content if none specified
    try:
        if len(options.excludeChannels) == 0: options.excludeChannels = []
        else:
            #try to explode string
            if len(options.excludeChannels) == 1: options.excludeChannels = str(options.excludeChannels).strip("[]'").split(",")
    except:
        options.excludeChannels = []

    #check whether channels were specified
    if options.allChannels == False:
        try:
            if len(options.channels) == 0:
                #no channel specified
                print "UNKNOWN: no channel(s) specified"
                exit(3)
            else:
                #try to explode string
                if len(options.channels) == 1: options.channels = str(options.channels).strip("[]'").split(",")
                if options.debug: print "DEBUG: ",options.channels
        except:
            #size excpetion, no channel specified
            print "UNKNOWN: no channel(s) specified"
            exit(3)

    #setup client and key depending on mode if needed
    if not options.repodataOnly:
        client = xmlrpclib.Server(SATELLITE_URL, verbose=options.debug)
        if options.authfile:
            #use authfile
            if options.debug: print "DEBUG: using authfile"
            try:
                #check filemode and read file
                filemode = oct(stat.S_IMODE(os.lstat(options.authfile).st_mode))
                if filemode == "0600":
                    if options.debug: print "DEBUG: file permission ("+filemode+") matches 0600"
                    fo = open(options.authfile, "r")
                    s_username=fo.readline().replace("\n", "")
                    s_password=fo.readline().replace("\n", "")
                    key = client.auth.login(s_username, s_password)
                else:
                    if options.verbose: print "ERROR: file permission ("+filemode+") not matching 0600!"
                    exit(1)
            except OSError:
                print "ERROR: file non-existent or permissions not 0600!"
                exit(1)
        elif "SATELLITE_LOGIN" in os.environ and "SATELLITE_PASSWORD" in os.environ:
            #shell variables
            if options.debug: print "DEBUG: checking shell variables"
            key = client.auth.login(os.environ["SATELLITE_LOGIN"], os.environ["SATELLITE_PASSWORD"])
        else:
            #prompt user
            if options.debug: print "DEBUG: prompting for login credentials"
            s_username = raw_input("Username: ")
            s_password = getpass.getpass("Password: ")
            key = client.auth.login(s_username, s_password)

        #check whether the API version matches the minimum required
        api_level = client.api.getVersion()
        if not api_level in supportedAPI:
            print "ERROR: your API version ("+api_level+") does not support the required calls. You'll need API version 1.8 (11.1) or higher!"
            exit(1)
        else:
            if options.debug: print "INFO: supported API version ("+api_level+") found."

    #try to guess channels if requested
    if options.allChannels == True:
        myChannels = []
        if options.repodataOnly == False:
            #check using Spacewalk API
            for channel in client.channel.listAllChannels(key):
                #add channel if not blacklisted
                if channel["label"] not in options.excludeChannels: myChannels.append(channel["label"])
        else:
            #check for folder names on file system
            d="/var/cache/rhn/repodata"
            tempChannels = [os.path.join(d,o) for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]
            for entry in tempChannels:
                k = entry.rfind("/")
                #add channel if not blacklisted
                if str(entry[k+1:]) not in options.excludeChannels: myChannels.append(entry[k+1:])
        # apply positiveFilter if not empty
        if options.positiveFilter:
            myChannels = [ channelname for channelname in myChannels for filter in options.positiveFilter if filter in channelname ]
        # apply negativeFilter if not empty
        if options.negativeFilter:
            for filter in options.negativeFilter:
                myChannels = [ channelname for channelname in myChannels if not filter in channelname ]
        options.channels = myChannels

    #check repo sync state
    errors = []
    critError = False
    if not options.repodataOnly:
        for channel in options.channels:
            #get channel details
            details = client.channel.software.getDetails(key, channel)
            if "yumrepo_last_sync" in details:
                #check last sync state if given (not all channels provide these information - e.g. RHEL channels)
                stamp = datetime.datetime.strptime(str(details["yumrepo_last_sync"]), "%Y%m%dT%H:%M:%S")
                now = datetime.datetime.today()
                diff = now - stamp
                diff = diff.seconds / 3600 + diff.days * 24
                if options.debug: print "DEBUG: Yum sync difference for channel '"+channel+"' is "+str(diff)+" hours"
                if int(diff) >= options.criticalThres:
                    if options.debug: print "DEBUG: Yum sync difference (" + str(diff) + ") is higher than critical threshold (" + str(options.criticalThres) + ")"
                    if channel not in errors: errors.append(channel)
                    critError = True
                elif int(diff) >= options.warningThres:
                    if options.debug: print "DEBUG: Yum sync difference (" + str(diff) + ") is higher than warning threshold (" + str(options.warningThres) + ")"
                    if channel not in errors: errors.append(channel)

    #check repodata age
    for channel in options.channels:
        #check for *.new files (indicator for running repodata rebuild)
        newfiles = glob.glob("/var/cache/rhn/repodata/"+channel+"/*.new")
        if len(newfiles) >= 1:
            #rebuild in progress, check timestamp of first file
            errors.append(channel)
        #check for outdated repodata
        try:
            stamp = datetime.datetime.fromtimestamp(os.path.getmtime("/var/cache/rhn/repodata/"+channel+"/repomd.xml"))
            now = datetime.datetime.today()
            diff = now - stamp
            diff = diff.seconds / 3600 + diff.days * 24
            if options.debug: print "DEBUG: Difference for /var/cache/rhn/repodata/"+channel+"/repomd.xml is "+str(diff)+" hours"
            if int(diff) >= options.criticalThres:
                if options.debug: print "DEBUG: File system timestamp difference (" + str(diff) + ") is higher than critical threshold (" + str(options.criticalThres) + ")"
                if channel not in errors: errors.append(channel)
                critError = True
                if options.debug: print "DEBUG: File system timestamp difference (" + str(diff) + ") is higher than warning threshold (" + str(options.criticalThres) + ")"
            elif int(diff) >= options.warningThres:
                if channel not in errors: errors.append(channel)
        except:
            #unable to check filesystem
            if options.debug: print "DEBUG: unable to check filesystem timestamp for /var/cache/rhn/repodata/"+channel+"/repomd.xml."
            critError = True
            if channel not in errors: errors.append(channel)

    #exit with appropriate Nagios / Icinga plugin return code and message
    if options.debug: print "ERRORS: " + str(errors)
    if ( not options.logicalAnd and len(errors) >= 1) or ( options.logicalAnd and len(errors) == len(options.channels) ) :
        if critError == True:
            print "CRITICAL: "+str(len(errors))+" channel(s) still syncing or outdated:",str(errors).strip("[]")
            exit(2)
        else:
            print "WARNING: "+str(len(errors))+" channel(s) still syncing or outdated:",str(errors).strip("[]")
            exit(1)
    else:
        if options.fullOutput == True:
            print "OK: Specified channel(s) ("+str(len(options.channels))+") synchronized:",str(options.channels).strip("[]")
        else:
            print "OK: Specified channel(s) ("+str(len(options.channels))+") synchronized"
        exit(0)
