### Objective: Interact with AWS CLI to list, stop, and start ec2 instances and get and release public IP addresses for specified private IP addresses
###
### Requirements: 
1. python v 2.6 or later for subprocess and json
2. AWS cli installed and configured on local host
### 
### Usage: ./aws-ec2.py <action|> <instanceIds|privateIPs|>
#### Actions:

  list - list all instances in all regions, all instances in a region by specifying region, or instance(s) in a region by specifying region and instance(s). See examples
  
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
