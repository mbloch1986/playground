#!/usr/bin/python
# -*- coding: utf8 -*-

from ansible.module_utils.basic import *

DOCUMENTATION = '''
---
module: stack_manager_config
Ansible module for creating Stack Manager config
'''

EXAMPLES = '''
- name: Create Stack Manager configuration
  stack_manager_config:
    Stack_prefix: "AEM63-Full-Set"
    Stack_name: "Stack-Manager"
    S3Bucket: "AEM-Bucket"
    S3Folder: "AEM63/StackManager"
    TaskStatusTopicArn: arn:aws:sns:region:account-id:TaskStatusTopicArn
    SSMServiceRoleArn: arn:aws:iam::account-id:role/role-name
    S3BucketSSMOutput: "AEM-Bucket"
    S3PrefixSSMOutput: "AEM63/StackManager/SSMOutput"
    BackupTopicArn: "arn:aws:sns:region:account-id:BackupTopicArn"
    DynamoDBTableName: "AEM63-Full-Set-Stack-Manager-Table"
    State: present
  register: result

- name: Delete Stack Manager configuration
  stack_manager_config:
    Stack_prefix: "AEM63-Full-Set"
    Stack_name: "Stack-Manager"
    S3Bucket: "AEM-Bucket"
    S3Folder: "AEM63/StackManager"
    state: absent
  register: result
'''



import os
import sys
from ansible.module_utils.basic import *

try:
    import boto3
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import json
    HAS_JSON = True
except ImportError:
    HAS_JSON = False


# Set variables
tmp_file = '/tmp/templist.json'

# AWS resources
#s3_client = boto3.resource('s3')
#cloudformation_client = boto3.resource('cloudformation')
#s3_bucket = s3_client.Bucket(s3_bucket) 

def s3_upload(tmp_file, stack_prefix):
    config_path = 'stack-manager/config.json'
    upload_path = stack_prefix + '/' + config_path
    s3_bucket.upload_file(tmp_file, upload_path)

def create_config(argument_spec):
    stack_prefix = argument_spec['Stack_prefix']
    stack_name = argument_spec['stack_name']
    s3bucket = argument_spec['S3Bucket']
    s3folder = argument_spec['S3Folder']
    taskstatustopicarn = argument_spec['TaskStatusTopicArn']
    ssmservicerolearn = argument_spec['SSMServiceRoleArn']
    s3bucketssmoutput = argument_spec['S3BucketSSMOutput']
    s3prefixssmoutput = argument_spec['S3PrefixSSMOutput']
    backuptopicarn = argument_spec['BackupTopicArn']
    dynamodbtablename = argument_spec['DynamoDBTableName']
   
   # Get Stack information
    cloudformation_client = boto3.resource('cloudformation')
    stack_outputs = cloudformation_client.Stack(stack_name + '-' + stack_prefix).outputs

    # Create dict for run_cmd
    ec2_run_command = {
            "ec2_run_command": {\
                    "cmd-output-bucket": s3bucketssmoutput,\
                    "cmd-output-prefix": s3prefixssmoutput,\
                    "status-topic-arn": taskstatustopicarn,\
                    "ssm-service-role-arn": taskstatustopicarn,\
                    "dynamodbtablename": dynamodbtable\
                    }}

    # Create dict for task mapping
    messenger_task_mapping = {
            "DeployArtifacts": "deploy-artifacts",
            "ManageService": "manage-service",
            "OfflineSnapshot": "offline-snapshot",
            "ExportPackage": "export-package",
            "ExportPackages": "export-packages",
            "DeployArtifact": "deploy-artifact",
            "OfflineCompaction": "offline-compaction",
            "PromoteAuthor": "promote-author",
            "ImportPackage": "import-package",
            'WaitUntilReady': "wait-until-ready",
            "EnableCrxde": "enable-crxde",
            "RunAdhocPuppet": "run-adhoc-puppet",
            "LiveSnapshot": "live-snapshot",
            "DisableCrxde": "disable-crxde",
            }
    messenger_config_list = {
        messenger_task_mapping[output['OutputKey']]: output['OutputValue']
        for output in stack_outputs
    }
    messenger_dict = dict()
    messenger_dict['document_mapping'] = messenger_config_list

    # Create dict for offline snapshot
    offline_snapshot ={
            "offline_snapshot": {
                "min-publish-instances": 2,\
                "sns-topic-arn": backuparn
            }
    }

    # Create config dict
    ec2_run_command.update(messenger_dict)
    ec2_run_command.update(offline_snapshot

    # Create temp configuration
    with open(tmp_file, 'w') as file:
            json.dump( ec2_run_command, file, indent=2)


def delete_config():
    os.remove(tmp_file)

def main():
    argument_spec = config_argument()
    argument_spec.update = {
            "Stack_prefix": {"required": True, "type": "str"},
            "Stack_name": {"required": True, "type": "str" },
            "S3Bucket": {"required": True, "type": "str"},
            "S3Folder": {"required": True, "type": "str"},
            "TaskStatusTopicArn": {"required": True, "type": "str"},
            "SSMServiceRoleArn": {"required": True, "type": "str"},
            "S3BucketSSMOutput": {"required": True, "type": "str"},
            "S3PrefixSSMOutput": {"required": True, "type": "str"},
            "BackupTopicArn": {"required": True, "type": "str"},
            "DynamoDBTableName": {"required": True, "type": "str"},
            "state": {
                "default": "present",
                "choices": ['present', 'absent'],
                "type": 'str'
        },
    }

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    if not HAS_JSON:
        module.fail_json(msg='json required for this module')

    choice_map = {
        "present": create_config,
        "absent": delete_config,
        }
    
    is_error, has_changed, result = choice_map.get(
            module.params['state'])(module.params)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Deleting config", meta=result) 
    
if __name__ == '__main__':  
    main()
