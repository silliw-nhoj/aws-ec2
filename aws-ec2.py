#!/usr/bin/python
# aws-ec2.py
# j.willis@f5.com - 6-2-2016
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
volumes = {}

usage = "\n\
Objective: Interact with AWS CLI to list, stop, and start ec2 instances and get and release public IP addresses\n\
for specified private IP addresses\n\n\
Requirements:\n\
  1. python v 2.6 or later for subprocess and json\n\
  2. AWS cli installed and configured on local host\n\n\
Usage: ./%prog [options]\n\
ACTIONS:\n\
  list - list all instances in all regions, all instances in a region by specifying region, or\n\
         instance(s) in a region by specifying region and instance(s). See examples\n\
  running - same as list but only for running instances\n\
  bigvols - same as list but only for instances with big vols (> 100GB)\n\
  start|stop - start or stop ec2 instance(s)\n\
  pub|nopub - get or release public IP(s) for specified private IP(s)\n\n\
EXAMPLES:\n\
1. LIst EC2 instances\n\
  Example: ./%prog --action list\n\
           ./%prog -a list --region us-west-1\n\
           ./%prog -a list -r us-west-1 --instance-ids \"i-ca12d212 i-5c0ece84\"\n\
2. Start|stop EC2 instances\n\
  Example:  ./%prog -a start -r us-west-1 --instance-ids \"i-ca12d212 i-5c0ece84\"\n\
            ./%prog -a stop -r us-west-1 --instance-ids \"i-ca12d212 i-5c0ece84\"\n\
3. Get|release elastic IP(s) for private IP(s)\n\
  Example:  ./%prog -a pub -r us-west-1 --priv-ips \"10.0.1.226 10.0.101.21\" --instance-ids \"i-ca12d212 i-5c0ece84\"\n\
            ./%prog -a nopub -r us-west-1 --priv-ips \"10.0.1.226 10.0.101.21\" --instance-ids \"i-ca12d212 i-5c0ece84\""

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
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-a', '--action', 
        dest="action", 
        default="list",
        choices=['list','running','start','stop','pub','nopub','bigvols']
    )
    parser.add_option('-r', '--region',
        dest="region",
        default="",
    )
    parser.add_option('-i', '--instance-ids',
        dest="instanceIds",
        default="",
    )
    parser.add_option('-p', '--priv-ips',
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

def get_instances():

    for regionIndex in  range(len(ec2regions["Regions"])):
        region = ec2regions["Regions"][regionIndex]["RegionName"]
        ec2regions["Regions"][regionIndex]["showRegion"] = "false"
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
                instances[instId]["instName"] = 'None'

                instances[instId]['state'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["State"]["Name"]
                if ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["StateTransitionReason"]:
                    instances[instId]['stateReason'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["StateTransitionReason"]
                else:
                    instances[instId]['stateReason'] = "NA"

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
                        if ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["Tags"][tag]["Key"] == 'Name':
                            instances[instId]["instName"] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["Tags"][tag]["Value"]
                            break

                if not instances[instId]["instName"]:
                    instances[instId]["instName"] = 'None'

                if (options.action == "running" and ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["State"]["Name"] == "running"):
                    ec2regions["Regions"][regionIndex]["showRegion"] = "true"

                for netInt in range(len(ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"])):
                    # order by device index (ie. eth0, eth1) using
                    intIndex = str(ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["Attachment"]["DeviceIndex"])
                    instances[instId]['interfaces'][intIndex] = {}
                    instances[instId]['interfaces'][intIndex]['privIPs'] = {}
                    instances[instId]['interfaces'][intIndex]['intId'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["NetworkInterfaceId"]
                    instances[instId]['interfaces'][intIndex]['macAddr'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["MacAddress"]
                    instances[instId]['interfaces'][intIndex]['desc'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["Description"]
                    if instances[instId]['interfaces'][intIndex]['desc'] == "":
                        instances[instId]['interfaces'][intIndex]['desc'] = "No description"
                    instances[instId]['interfaces'][intIndex]['index'] = intIndex
                    for intPrivIP in range(len(ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"])):
                        privIP = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]["PrivateIpAddress"]
                        instances[instId]['interfaces'][intIndex]['privIPs'][privIP] = {}
                        instances[instId]['interfaces'][intIndex]['privIPs'][privIP]['privIP'] = privIP
                        instances[instId]['interfaces'][intIndex]['privIPs'][privIP]['pubIp'] = 'None'
                        if 'Association' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]:
                            if 'PublicIp' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]["Association"]:
                                instances[instId]['interfaces'][intIndex]['privIPs'][privIP]['pubIp'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]["Association"]["PublicIp"]
                            
                        if ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["NetworkInterfaces"][netInt]["PrivateIpAddresses"][intPrivIP]["Primary"] == True:
                            instances[instId]['interfaces'][intIndex]['privIPs'][privIP]['primaryIP'] = "Primary"
                        else:
                            instances[instId]['interfaces'][intIndex]['privIPs'][privIP]['primaryIP'] = "Secondary"

                # TODO: get ebs volume IDs. Make function to get volume details and disk sizes.

                if not ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["BlockDeviceMappings"]:
                    continue

                instances[instId]['volName'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["BlockDeviceMappings"][0]["DeviceName"]
                instances[instId]['volId'] = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["BlockDeviceMappings"][0]["Ebs"]["VolumeId"]

                for volRegIndex in  range(len(volumes)):
                    for volIndex in range(len(volumes[volRegIndex]["Volumes"])):
                        if instances[instId]['volId'] == volumes[volRegIndex]["Volumes"][volIndex]["VolumeId"]:
                            instances[instId]['volType'] = volumes[volRegIndex]["Volumes"][volIndex]["VolumeType"]
                            instances[instId]['volSize'] = volumes[volRegIndex]["Volumes"][volIndex]["Size"]

                if (instances[instId]['volSize'] > 100 and options.action == "bigvols"):
                    ec2regions["Regions"][regionIndex]["showRegion"] = "true"



def get_volumes():
    for regionIndex in  range(len(ec2regions["Regions"])):
        region = ec2regions["Regions"][regionIndex]["RegionName"]
        output = subprocess.Popen('aws ec2 describe-volumes --region ' +region, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (ec2JSON, err) = output.communicate()
        global volumes
        if (err != ""):
            print '\nError: Function ' + sys._getframe().f_code.co_name + ' in ' + sys._getframe().f_code.co_filename + err
            sys.exit(0)
        else:
            volumes[regionIndex] = json.loads(ec2JSON)



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

        if (options.action == "running" or options.action == "bigvols"):
            if ec2regions["Regions"][regionIndex]["showRegion"] == "false":
                continue

        if ec2reservations[regionIndex]["Reservations"]:
            print colors.blue + '\n############################\n# Region:',region,'\n############################\n' + colors.default,
        else:
            continue

        for instance in range(len(ec2reservations[regionIndex]["Reservations"])):
            instId = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["InstanceId"]

            #if not ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["BlockDeviceMappings"]:
            #    continue

            if ( options.action == "running" and instances[instId]["state"] != "running"):
                continue
            if ( options.action == "bigvols" and instances[instId]['volSize'] <= 100):
                continue

            if instances[instId]["state"] == "stopped":
                color = colors.red
            elif instances[instId]["state"] == "running":
                color = colors.green
            else:
                color = colors.yellow

            print '  Name:', colors.blue + instances[instId]["instName"] + colors.default ,', Instance ID:',instId
            print '    State:', color + instances[instId]["state"] + colors.default + ', Reason: ' + instances[instId]["stateReason"] 
            print '    KeyName:',ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["KeyName"],', Launch Time:', ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["LaunchTime"]
            if ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["BlockDeviceMappings"]:
                print '    VolumeName:',instances[instId]['volName'],', VolumeId:',instances[instId]['volId'] ,', Type:',instances[instId]['volType'],', Size:',str(instances[instId]['volSize'])
            print '    Primary Priv IP:',instances[instId]["instPrivIP"],', Primary Public IP:',instances[instId]["instPubIP"]
            for intIndex in sorted(instances[instId]['interfaces'].keys()):
                print '      Eth' + intIndex + ':',instances[instId]['interfaces'][intIndex]['desc'],', ID:',instances[instId]['interfaces'][intIndex]['intId'],', MAC:',instances[instId]['interfaces'][intIndex]['macAddr']
                for privIP in instances[instId]['interfaces'][intIndex]['privIPs'].keys():
                    print '        ' + instances[instId]['interfaces'][intIndex]['privIPs'][privIP]['primaryIP'],'Private IP:',privIP,', Public IP:',instances[instId]['interfaces'][intIndex]['privIPs'][privIP]['pubIp']
    
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
get_regions()
get_volumes()
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
