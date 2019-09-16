#!/usr/bin/python
# aws-ec2.py
# j.willis@f5.com - 6-2-2016
#
# Objective: Interact with AWS CLI to list, stop, and start ec2 instances and get and release public IP addresses
# for specified private IP addresses
#
# Requirements: 
# 1. python v 2.6 or later for subprocess and json
# 2. AWS cli installed and configured on local host
# 
# Usage: ./aws-ec2.py <action|> <instanceIds|privateIPs|>
# 	actions: 
#       list - list all instances in all regions, all instances in a region by specifying region, or
#              instance(s) in a region by specifying region and instance(s). See examples
# 		start|stop - start or stop ec2 instance(s)
# 		pub|nopub - get or release public IP(s) for specified private IP(s)
# 	
# 1. LIst EC2 instances
# 	Example: ./aws-ec2.py --action list
#            ./aws-ec2.py -a list --region us-west-1
#            ./aws-ec2.py -a list -r us-west-1 --instance-ids "i-ca12d212 i-5c0ece84"
# 	
# 2. Start|stop EC2 instances
# 	Example:	./aws-ec2.py -a start -r us-west-1 --instance-ids "i-ca12d212 i-5c0ece84"
# 				./aws-ec2.py -a stop -r us-west-1 --instance-ids "i-ca12d212 i-5c0ece84"
# 
# 3. get|release elastic IP(s) for private IP(s)
# 	Example:	./aws-ec2.py -a pub -r us-west-1 --priv-ips "10.0.1.226 10.0.101.21" --instance-ids "i-ca12d212 i-5c0ece84"
# 				./aws-ec2.py -a nopub -r us-west-1 --priv-ips "10.0.1.226 10.0.101.21" --instance-ids "i-ca12d212 i-5c0ece84"
#

# -------------------------------------------------------------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------------------------------------------------------------

import sys, os
import optparse
import subprocess
import json
import time

ec2reservations = {}
ec2regions = {}
instances = {}
regions = {}

class colors:
    header = '\033[95m'
    blue = '\033[94m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    default = '\033[0m'


# -------------------------------------------------------------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------------------------------------------------------------

def command_args():
    parser = optparse.OptionParser()
    parser.add_option('-a', '--action', 
        dest="action", 
        default="list",
    )
    parser.add_option('-r', '--region',
        dest="region",
        default="",
    )
    parser.add_option('--instance-ids',
        dest="instanceIds",
        default="",
    )
    parser.add_option('--priv-ips',
        dest="privIps",
        default="",
        type="string"
    )
    global options
    options, remainder = parser.parse_args()

    print 'ACTION     :', options.action
    print 'REGION     :', options.region
    print 'INSTANCES  :', options.instanceIds
    print 'PRIVATEIPS :', options.privIps
    return;

def usage():
    print 'Interact with AWS CLI to list, stop, and start ec2 instances and get and release public IP addresses for specified private IP addresses.'
    print '\nRequirements:\n\t1. python v 2.6 or later for subprocess and json\n\t2. AWS cli installed and configured on local host'
    print '\nUsage: ./aws-ec2.py <action|> <instanceIds|privateIPs|>\n\tactions:\n\t\tstart|stop - start or stop ec2 instance(s)\n\t\tpub|nopub - get or release public IP(s) for private IP(s)\n\tinstance Ids: List ec2 instance Ids to stop or start. If more than one, coma separated with no spaces\n\tPrivate IPs: List private IPs to get or release public IPs for. If more than one, coma separated with no spaces'
    return;

def get_instances():

    for regionIndex in  range(len(ec2regions["Regions"])):
        region = ec2regions["Regions"][regionIndex]["RegionName"]
        output = subprocess.Popen('aws ec2 describe-instances --instance-ids ' + options.instanceIds + ' --region ' + region, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (ec2JSON, err) = output.communicate()
        #global ec2reservations
        if (err != ""):
            print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
            sys.exit(0)
        else:
            ec2reservations[regionIndex] = json.loads(ec2JSON)
            for instance in range(len(ec2reservations[regionIndex]["Reservations"])):
                instId = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["InstanceId"]
                
                instances[instId] = {}
                instances[instId]['interfaces'] = {}
                instances[instId]['Region'] = region
                
                instances[instId]['state'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["State"]["Name"]

                if 'PrivateIpAddress' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]:
                    instances[instId]["instPrivIP"] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["PrivateIpAddress"]
                else:
                    instances[instId]["instPrivIP"] = 'None'

                if 'PublicIpAddress' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]:
                    instances[instId]["instPubIP"] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["PublicIpAddress"]
                else:
                    instances[instId]["instPubIP"] = 'None'
                

                if 'Tags' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]:
                    for tag in range(len(ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["Tags"])):
                        if 'Name' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["Tags"][tag]["Key"]:
                            instances[instId]["instName"] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["Tags"][tag]["Value"]
                else:
                    instances[instId]["instName"] = 'None'

                if not instances[instId]["instName"]:
                    instances[instId]["instName"] = 'None'
                
                for netInt in range(len(ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"])):
                    intId = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["NetworkInterfaceId"]
                    instances[instId]['interfaces'][intId] = {}
                    instances[instId]['interfaces'][intId]['privIPs'] = {}
                    instances[instId]['interfaces'][intId]['intId'] = intId
                    instances[instId]['interfaces'][intId]['macAddr'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["MacAddress"]
                    instances[instId]['interfaces'][intId]['desc'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["Description"]
                    instances[instId]['interfaces'][intId]['index'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["Attachment"]["DeviceIndex"]
                    for intPrivIP in range(len(ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"])):
                        privIP = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]["PrivateIpAddress"]
                        instances[instId]['interfaces'][intId]['privIPs'][privIP] = {}
                        instances[instId]['interfaces'][intId]['privIPs'][privIP]['privIP'] = privIP
                        instances[instId]['interfaces'][intId]['privIPs'][privIP]['pubIp'] = 'None'
                        if 'Association' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]:
                            if 'PublicIp' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]["Association"]:
                                instances[instId]['interfaces'][intId]['privIPs'][privIP]['pubIp'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]["Association"]["PublicIp"]
                            
                        instances[instId]['interfaces'][intId]['privIPs'][privIP]['primaryIP'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]["Primary"]

def get_regions():
    output = subprocess.Popen('aws ec2 describe-regions --region-names ' +options.region, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (ec2JSON, err) = output.communicate()
    global ec2regions
    if (err != ""):
        print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
        sys.exit(0)
    else:
        ec2regions = json.loads(ec2JSON)
        return;
    
def show_instances():
    for regionIndex in range(len(ec2regions["Regions"])):
        region = ec2regions["Regions"][regionIndex]["RegionName"]
        print '\n' + colors.blue + '############################\n# Region:',region,'\n############################' + colors.default,
        for instance in range(len(ec2reservations[regionIndex]["Reservations"])):
            instId = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["InstanceId"]

            if instances[instId]["state"] == "stopped":
                color = colors.red
            elif instances[instId]["state"] == "running":
                color = colors.green
            else:
                color = colors.yellow

            print '\n  Name:', colors.blue + instances[instId]["instName"] + colors.default ,', Instance ID:',instId, \
                  ', State:', color + instances[instId]["state"] + colors.default
            print '    KeyName:',ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["KeyName"],', Launch Time:', ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["LaunchTime"]
            print '    Primary Priv IP:',instances[instId]["instPrivIP"],', Primary Public IP:',instances[instId]["instPubIP"]
            for intId in instances[instId]['interfaces'].keys():
                print '\tInterface:',instances[instId]['interfaces'][intId]['desc'],', ID:',instances[instId]['interfaces'][intId]['intId'],', MAC:',instances[instId]['interfaces'][intId]['macAddr']
                print '\t  IP Addresses:'
                for privIP in instances[instId]['interfaces'][intId]['privIPs'].keys():
                    print '\t  Primary:',instances[instId]['interfaces'][intId]['privIPs'][privIP]['primaryIP'],', Private IP:',privIP,', Public IP:',instances[instId]['interfaces'][intId]['privIPs'][privIP]['pubIp']
    
    return;

def stop_start_instance():
    output = subprocess.Popen('aws ec2 ' + options.action + '-instances --instance-ids ' + options.instanceIds + ' --region ' + options.region, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (ec2JSON, err) = output.communicate()
    if (err != ""):
        print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
        sys.exit(0)
    else:
        return;

def get_pub_addr():
    output = subprocess.Popen('aws ec2 describe-network-interfaces --region ' + options.region , stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (netIntInfo, err) = output.communicate()
    if (err != ""):
        print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
        sys.exit(0)
    else:
        netInts = json.loads(netIntInfo) 
        privIps = options.privIps
        privIps = privIps.split(' ')   
        for i in range(len(privIps)):
            priIP = privIps[i]
            output = subprocess.Popen('aws ec2 allocate-address --region ' + options.region, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            (allocatedAddrInfo, err) = output.communicate()
            if (err != ""):
                print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
                sys.exit(0)
            else:
                allocAddr = json.loads(allocatedAddrInfo)
                if 'NetworkInterfaces' in netInts:
                    for netInt in range(len(netInts['NetworkInterfaces'])):
                        for IPIdx in range(len(netInts['NetworkInterfaces'][netInt]['PrivateIpAddresses'])):
                            if priIP in netInts['NetworkInterfaces'][netInt]['PrivateIpAddresses'][IPIdx]['PrivateIpAddress']:
                                allocId = allocAddr['AllocationId']
                                pubIp = allocAddr['PublicIp']
                                netIntId = netInts['NetworkInterfaces'][netInt]['NetworkInterfaceId']
                                print '* assigning public IP address', pubIp, 'to network interface', netIntId, 'private IP', priIP
                                output = subprocess.Popen('aws ec2 associate-address --allocation-id ' + allocId + ' --network-interface-id ' + netIntId + ' --private-ip-address ' + priIP + ' --region ' + options.region, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                                (assocAddrInfo, err) = output.communicate()
                                if (err != ""):
                                    print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
                                    sys.exit(0)

        return;
    
def del_pub_addr():
    privIps = options.privIps
    privIps = privIps.split(' ')
    for i in range(len(privIps)):
        priIP = privIps[i]
        output = subprocess.Popen('aws ec2 describe-addresses --filters \"Name=private-ip-address,Values=' + priIP + '\" --region ' + options.region, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (elaIPInfo, err) = output.communicate()
        if (err != ""):
            print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
            sys.exit(0)
        else:
            elaIPs = json.loads(elaIPInfo)
            for i in range(len(elaIPs['Addresses'])):
                pubIP = elaIPs['Addresses'][i]['PublicIp']
                assocId = elaIPs['Addresses'][i]['AssociationId']
                allocId = elaIPs['Addresses'][i]['AllocationId']
                print '* Releasing elastic IP', pubIP, 'from private IP', priIP
                output = subprocess.Popen('aws ec2 disassociate-address --association-id ' + assocId + ' --region ' + options.region, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                (result, err) = output.communicate()
                if (err != ""):
                    print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
                    sys.exit(0)
                output = subprocess.Popen('aws ec2 release-address --allocation-id ' + allocId + ' --region ' + options.region, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                (result, err) = output.communicate()
                if (err != ""):
                    print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
                    sys.exit(0)
    return;
    
# -------------------------------------------------------------------------------------------------------------------------
# main
# -------------------------------------------------------------------------------------------------------------------------

command_args()
# if (command_args.error or command_args.help):
#     usage()
#     quit()
get_regions()
get_instances()
show_instances()
if (options.action == 'stop' or options.action == 'start'):
    stop_start_instance()
    time.sleep(5)
    get_instances()
    show_instances()
elif (options.action == 'pub'):
    get_pub_addr()
    get_instances()
    show_instances()
elif (options.action == 'nopub'):
    del_pub_addr()
    get_instances()
    show_instances()
