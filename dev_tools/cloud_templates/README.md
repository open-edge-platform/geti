<!---
Copyright (C) 2022-2025 Intel Corporation
LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
-->

## Introduction

Cloud deployment automation templates are placed here. Templates complement manual deployment guide lines for installation of Geti.

### AWS CloudFormation

Creating a key pair directly within a CloudFormation template is not supported because AWS CloudFormation does not have a native resource
type for creating EC2 key pairs. Key pairs are typically created manually through the AWS Management Console, AWS CLI, or AWS SDKs before
launching instances with CloudFormation.

You can use the AWS CLI to create a key pair before deploying your CloudFormation stack. Run the following commands assuming you use Linux machine:

```
aws ec2 create-key-pair --key-name MyKeyPair --query 'KeyMaterial' --output text > MyKeyPair.pem
chmod 400 MyKeyPair.pem
mv MyKeyPair.pem ~/.ssh/
```

Run the following command, replacing <region> with your desired AWS region:

```
aws ec2 describe-images --region <region> --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" --query "Images[*].[ImageId,Name]" --output text
```

The owner ID 099720109477 is Canonical's AWS account ID, which publishes official Ubuntu AMIs.

Use the following command to SSH into your instance, replacing <public_ip> with the instance's public IP:

```
ssh -i ~/.ssh/MyKeyPair.pem ubuntu@<public_ip>
```

The username ubuntu is used for Ubuntu AMIs. If you're using a different AMI, the username might differ (e.g., ec2-user for Amazon Linux).
