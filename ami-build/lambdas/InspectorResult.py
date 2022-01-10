import json
import os
import boto3
import sys

class InspectorResult():
    def __init__(self):
        self.message = ''
        self.notify = ''
    def get_findings(self,session,assessment_run):
        finding_arns = []
        inspector = session.client('inspector')
        paginator = inspector.get_paginator('list_findings')
        for findings in paginator.paginate(maxResults=5000,assessmentRunArns=[assessment_run]):
            for finding_arn in findings['findingArns']:
                finding_arns.append(finding_arn)
        return finding_arns
    def describe_findings(self,session,finding_arns):
        inspector = session.client('inspector')
        for finding_arn in finding_arns:
            finding = inspector.describe_findings(findingArns=[finding_arn])
        return finding['findings']
    def get_ami_id(self,session,instance_id):
        ec2 = session.client('ec2')
        reservations = ec2.describe_instances(InstanceIds=[instance_id])['Reservations']
        for reservation in reservations:
            for instance in reservation['Instances']:
                image_id = instance['ImageId']
                return image_id
        return None
    def get_ami_name(self,session,ami_id):
        ec2 = session.client('ec2')
        images = ec2.describe_images(ImageIds=[ami_id])['Images']
        for image in images:
            return image['Name']
        return None
    def get_agents(self,session,assessment_run):
        inspector = session.client('inspector')
        response = inspector.list_assessment_run_agents(
            assessmentRunArn=assessment_run
        )
        return response['assessmentRunAgents']
    def kill_instances(self,session,instance_ids):
        ec2 = session.client('ec2')
        for instance_id in instance_ids:
            print("Terminating instance: %s" % (instance_id))
            ec2.terminate_instances(InstanceIds=[instance_id])
    def get_report(self,session,ami_names,results):
        sns = session.client('sns')
        body = "\n".join([
            "Inspector - Run Report",
            "The findings from your assessment run can be found below",
            "This assessment ran for the following list of AMIs: %s" % (ami_names),
            results
            ])
            
        try:
            sns.publish(
                TopicArn=self.notify,    
                Message=body
            )
        except Exception as e:
            print(e)
            sys.exit(-1)

    def go(self):
        session = boto3.Session()
        message = self.message
        instance_ids = set()
        ami_names = set()
        finding_messages = []

        assessment_run = message['run']
        finding_message_template = "\n{}" * 4 + "\n"
        finding_arns = self.get_findings(session,assessment_run)
        findings = self.describe_findings(session,finding_arns)
        for finding in findings:
            instance_id = finding['assetAttributes']['agentId']
            ami_id = self.get_ami_id(session,instance_id)
            ami_name = self.get_ami_name(session,ami_id)
            instance_ids.add(instance_id)
            finding_message = finding_message_template.format(
                finding.get('severity'),
                finding.get('title'),
                finding.get('description').replace('\t', ''),
                finding.get('recommendation')
            )
            
            finding_messages.append(finding_message)
            ami_names.add("%s-%s" % (ami_name,ami_id)) 
        if not instance_ids:
            agents = self.get_agents(session,assessment_run)
            for agent in agents:
                instance_id = agent['agentId']
                instance_ids.add(instance_id)
                ami_id = self.get_ami_id(session,instance_id)
                ami_name = self.get_ami_name(session,ami_id)
                ami_names.add("%s-%s" % (ami_name,ami_id))
            results = "There were no issues found on this AMI"
        else:
            results = "".join(finding_messages)

        # terminate instances after inspector results are through
        self.kill_instances(session,instance_ids)
        self.get_report(session,ami_names,results)

def lambda_handler(event, context):
    if 'Records' in event:
        Inspect = InspectorResult()
        Inspect.message = json.loads(event['Records'][0]['Sns']['Message'])
        if 'run' in Inspect.message:
            Inspect.notify = os.environ.get('NotificationSNSTopic')
            Inspect.go()
        else:
            print('lambda has no run input. exiting.')
    else:
        print('lambda has malformed input')
        sys.exit(-1)