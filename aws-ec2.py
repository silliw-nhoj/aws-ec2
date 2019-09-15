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
# 		start|stop - start or stop ec2 instance(s)
# 		pub|nopub - get or release public IP(s) for private IP(s)
# 	instance Ids: List ec2 instance Ids to stop or start. If more than one, coma separated with no spaces
# 	Private IPs: List private IPs to get or release public IPs for. If more than one, coma separated with no spaces
# 	
# 1. LIst EC2 instances
# 	Example: ./aws-ec2.py
# 	
# 2. Start|stop EC2 instances
# 	Example:	./aws-ec2.py start i-ca12d212,i-5c0ece84
# 				./aws-ec2.py stop i-ca12d212,i-5c0ece84
# 
# 3. get|release elastic IP(s) for private IP(s)
# 	Example:	./aws-ec2.py pub 172.31.34.25,172.31.34.100,172.31.34.123
# 				./aws-ec2.py nopub 172.31.34.25,172.31.34.100,172.31.34.123
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
    )
    parser.add_option('--priv-ips',
        dest="privIps",
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
        output = subprocess.Popen('aws ec2 describe-instances --region ' +region, stdout=subprocess.PIPE, shell=True)
        (ec2JSON, err) = output.communicate()
        #global ec2reservations
        ec2reservations[regionIndex] = json.loads(ec2JSON)


def get_regions():
    output = subprocess.Popen('aws ec2 describe-regions --region-names ' +options.region, stdout=subprocess.PIPE, shell=True)
    (ec2JSON, err) = output.communicate()
    global ec2regions
    ec2regions = json.loads(ec2JSON)
    return;
    
def show_instances():
    for regionIndex in range(len(ec2regions["Regions"])):
        region = ec2regions["Regions"][regionIndex]["RegionName"]
        print '\n' + colors.blue + '############################\n# Region:',region,'\n############################' + colors.default,
        for instance in range(len(ec2reservations[regionIndex]["Reservations"])):
            instId = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["InstanceId"]
            state = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["State"]["Name"]
            if 'PrivateIpAddress' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]:
                instPrivIP = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["PrivateIpAddress"]
            else:
                instPrivIP = 'None'
            instances[instId] = {}
            instances[instId]['interfaces'] = {}
            instances[instId]['Region'] = region
            
            if 'PublicIpAddress' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]:
                instPubIP = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["PublicIpAddress"]
            else:
                instPubIP = 'None'
            

            if 'Tags' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]:
                for tag in range(len(ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["Tags"])):
                    if 'Name' in ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["Tags"][tag]["Key"]:
                        instName = ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["Tags"][tag]["Value"]
            else:
                instName = 'None'

            if not instName:
                instName = 'None'
            
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
            
            if state == "stopped":
                color = colors.red
            elif state == "running":
                color = colors.green
            else:
                color = colors.yellow

            print '\n  Name:', colors.blue + instName + colors.default ,'- Instance ID:',instId,'- State:', color + state + colors.default
            print '    KeyName:',ec2reservations[regionIndex]["Reservations"][instance]["Instances"][0]["KeyName"]
            print '    Primary Priv IP:',instPrivIP,'- Primary Public IP:',instPubIP
            for intId in instances[instId]['interfaces'].keys():
                print '\tInterface:',instances[instId]['interfaces'][intId]['desc'],'- ID:',instances[instId]['interfaces'][intId]['intId'],'- MAC:',instances[instId]['interfaces'][intId]['macAddr']
                print '\t  IP Addresses:'
                for privIP in instances[instId]['interfaces'][intId]['privIPs'].keys():
                    print '\t  Primary:',instances[instId]['interfaces'][intId]['privIPs'][privIP]['primaryIP'],'- Private IP:',privIP,'- Public IP:',instances[instId]['interfaces'][intId]['privIPs'][privIP]['pubIp']
    
    return;

def stop_start_instance():
    FNULL = open(os.devnull, 'w')
    subprocess.call('aws ec2 ' + options.action + '-instances --instance-ids ' + options.instanceIds + ' --region ' + options.region, stdout=FNULL, shell=True)
    # if options.action == 'stop':
    #     allocId = assocId = ''
    #     for instId in options.instanceIds:
    #         output = subprocess.Popen('aws ec2 describe-addresses --filters \"Name=instance-id,Values=' + instId +'\"', stdout=subprocess.PIPE, shell=True)
    #         (elaIPInfo, err) = output.communicate()
    #         elaIPs = json.loads(elaIPInfo)
    #         if elaIPs['Addresses']:
    #             for elaIP in range(len(elaIPs['Addresses'])):
    #                 if 'PublicIp' in elaIPs['Addresses'][elaIP]:
    #                     print '* Releasing elastic IP',elaIPs['Addresses'][elaIP]['PublicIp'],'from private IP',elaIPs['Addresses'][elaIP]['PrivateIpAddress']
    #                     subprocess.call('aws ec2 disassociate-address --association-id ' + elaIPs['Addresses'][elaIP]['AssociationId'], stdout=FNULL, shell=True)
    #                     subprocess.call('aws ec2 release-address --allocation-id ' + elaIPs['Addresses'][elaIP]['AllocationId'], stdout=FNULL, shell=True)
    return;

def get_pub_addr():
    FNULL = open(os.devnull, 'w')
    output = subprocess.Popen('aws ec2 describe-network-interfaces', stdout=subprocess.PIPE, shell=True)
    (netIntInfo, err) = output.communicate()
    netInts = json.loads(netIntInfo)    
    for priIP in command_args.priIPs:
        output = subprocess.Popen('aws ec2 allocate-address', stdout=subprocess.PIPE, shell=True)
        (allocatedAddrInfo, err) = output.communicate()
        allocAddr = json.loads(allocatedAddrInfo)
        #allocAddr['AllocationId']

        if 'NetworkInterfaces' in netInts:
            for netInt in range(len(netInts['NetworkInterfaces'])):
                for IPIdx in range(len(netInts['NetworkInterfaces'][netInt]['PrivateIpAddresses'])):
                    if priIP in netInts['NetworkInterfaces'][netInt]['PrivateIpAddresses'][IPIdx]['PrivateIpAddress']:
                        allocId = allocAddr['AllocationId']
                        pubIp = allocAddr['PublicIp']
                        netIntId = netInts['NetworkInterfaces'][netInt]['NetworkInterfaceId']
                        print '* assigning public IP address', pubIp, 'to network interface', netIntId, 'private IP', priIP
                        subprocess.call('aws ec2 associate-address --allocation-id ' + allocId + ' --network-interface-id ' + netIntId + ' --private-ip-address ' + priIP, stdout=FNULL, shell=True)
    return;
    
def del_pub_addr():
    print '\nAction:',command_args.action,'- private IP(s):',' '.join(command_args.priIPs),'\n'
    FNULL = open(os.devnull, 'w')
    for priIP in command_args.priIPs:
        output = subprocess.Popen('aws ec2 describe-addresses --filters \"Name=private-ip-address,Values=' + priIP + '\"', stdout=subprocess.PIPE, shell=True)
        (elaIPInfo, err) = output.communicate()
        elaIPs = json.loads(elaIPInfo)
        for i in range(len(elaIPs['Addresses'])):
            pubIP = elaIPs['Addresses'][i]['PublicIp']
            assocId = elaIPs['Addresses'][i]['AssociationId']
            allocId = elaIPs['Addresses'][i]['AllocationId']
            print '* Releasing elastic IP', pubIP, 'from private IP', priIP
            subprocess.call('aws ec2 disassociate-address --association-id ' + assocId, stdout=FNULL, shell=True)
            subprocess.call('aws ec2 release-address --allocation-id ' + allocId, stdout=FNULL, shell=True)
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
