### Objective: Interact with AWS CLI to list, stop, and start ec2 instances and get and release public IP addresses for specified private IP addresses
###
### Requirements: 
1. python v 2.6 or later for subprocess and json
2. AWS cli installed and configured on local host
### 
### Usage: ./aws-ec2.py <action|> <instanceIds|privateIPs|>
#### Actions:

  list - list all instances in all regions, all instances in a region by specifying region, or instance(s) in a region by specifying region and instance(s). See examples
  
  running - same as list but only for running instances
  
  start|stop - start or stop ec2 instance(s)
  
  pub|nopub - get or release public IP(s) for specified private IP(s)
	
####  1. LIst EC2 instances
  
    ./aws-ec2.py --action list
  
    ./aws-ec2.py -a list --region us-west-1
           
    ./aws-ec2.py -a list -r us-west-1 --instance-ids "i-ca12d212 i-5c0ece84"

#### 2. Start|stop EC2 instances

    ./aws-ec2.py -a start -r us-west-1 --instance-ids "i-ca12d212 i-5c0ece84"
  
    ./aws-ec2.py -a stop -r us-west-1 --instance-ids "i-ca12d212 i-5c0ece84"

#### 3. get|release elastic IP(s) for private IP(s)

    ./aws-ec2.py -a pub -r us-west-1 --priv-ips "10.0.1.226 10.0.101.21" --instance-ids "i-ca12d212 i-5c0ece84"

    ./aws-ec2.py -a nopub -r us-west-1 --priv-ips "10.0.1.226 10.0.101.21" --instance-ids "i-ca12d212 i-5c0ece84"

#### Example EC2 instance output
```
\############################\
\# Region: us-west-1\
\############################\
  Name: TS-122018-bigiq , Instance ID: i-0cf42a22424e3a1ad , State: stopped\
  KeyName: jw-keypair , Launch Time: 2019-10-26T17:40:28.000Z\
  Primary Priv IP: 10.0.1.139 , Primary Public IP: None\
    Eth0: Primary network interface , ID: eni-0793873a91ed2bb4a , MAC: 02:06:37:9d:92:e0\
      IP Addresses:\
      Primary: True , Private IP: 10.0.1.139 , Public IP: None\
	  
