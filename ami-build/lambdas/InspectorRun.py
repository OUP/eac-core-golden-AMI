import os
import json
import boto3
import time

class InspectorRun():
    def __init__(self):
        self.message = ''
        self.job = ''
    def create_instances(self,ami_id,subnet_id):
        ec2 = boto3.resource('ec2')
        tags = [{ 'Key': 'Inspector', 'Value': 'Yes' }]
        ec2result = ec2.create_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro',
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': tags
                }
            ],
            SubnetId = subnet_id,
            UserData="\n".join(
            [
                "#!/bin/bash",
                "wget https://d1wk0tztpsntt1.cloudfront.net/linux/latest/install",
                "bash install",
                "/etc/init.d/awsagent start"
            ]
            )
        )
        return ec2result
    def create_subscription(self,session,assessmentTemplate,assessmentTopic):
        inspector = session.client('inspector')
        codepipeline = session.client('codepipeline')
        eventsub = inspector.list_event_subscriptions(
            resourceArn=assessmentTemplate,
            maxResults = 100
            )
        if not eventsub['subscriptions']:
            try:
                inspector.subscribe_to_event(
                    resourceArn=assessmentTemplate,
                    event='ASSESSMENT_RUN_COMPLETED',
                    topicArn=assessmentTopic
                )
            except Exception as e:
                codepipeline.put_job_failure_result(jobId=self.job, failureDetails={'type':'JobFailed', 'message': 'failed to subscribe to event: %s' % (e)})
        else:
            print('event already exists - continuing')
    def wait_instances(self,results):
        instanceIds = []
        for result in results:
            result.wait_until_running()
            result.reload()
            instanceIds.append(result.id)
        return instanceIds
    def wait_agents(self,session,instances,assessmentTarget):
        inspector = session.client('inspector')
        codepipeline = session.client('codepipeline')
        max_retries = 5
        retries = 0
        while True:
            healthy = False
            print("looking for inspector agents")
            agents = inspector.preview_agents(
                previewAgentsArn=assessmentTarget,
            )
            for agent in agents['agentPreviews']:
                for instance in instances:
                    if agent['agentId'] in instance:
                        print("found matching agent for ec2 instance %s. health state: %s" % (instance,agent['agentHealth']))
                        if 'HEALTHY' in agent['agentHealth']:
                            healthy = True
                            break
                    else:
                        print("agent id: %s found that was not started by this pipeline run" % (agent['agentId']) )
            if healthy:
                break
            time.sleep(5)
            retries = retries + 1
            if retries == max_retries:
                print("max retries suceeded - failing job")
                codepipeline.put_job_failure_result(jobId=self.job, failureDetails={'type':'JobFailed', 'message': 'max retries for agent to become healthy exceeded'})
                for instance in instances:
                    instance.terminate()
                break
    def get_ami_id(self,session,location):
        ssm = session.client('ssm')
        amiId = ssm.get_parameter(Name=location, WithDecryption=False)['Parameter']['Value']
        return amiId
    def go(self):
        session = boto3.Session()
        codepipeline = session.client('codepipeline')
        inspector = session.client('inspector')
        subnetId = self.message['subnet']
        assessmentTemplate = self.message['assessmentTemplate']
        assessmentTarget = self.message['assessmentTarget']
        assessmentTopic = self.message['assessmentTopic']
        amiLocation = self.message['amiIdLocation']

        amiId = self.get_ami_id(session,amiLocation)
        instances = self.create_instances(amiId,subnetId)
        instance_ids = self.wait_instances(instances)
        self.wait_agents(session,instance_ids,assessmentTarget)
        self.create_subscription(session,assessmentTemplate,assessmentTopic)

        try:
            inspector.start_assessment_run(
                assessmentTemplateArn=assessmentTemplate,
            )
            codepipeline.put_job_success_result(jobId=self.job, currentRevision={'revision': self.job, 'changeIdentifier': self.job}, executionDetails={'summary': 'Job completed successfully', 'percentComplete': 100})
        except Exception as e:
            codepipeline.put_job_failure_result(jobId=self.job, failureDetails={'type':'JobFailed', 'message': 'failed to run inspector - %s' % (e)})
            for instance in instance_ids:
                instance.terminate()

def lambda_handler(event,context):
    InspectRun = InspectorRun()
    InspectRun.message = json.loads(event['CodePipeline.job']['data']['actionConfiguration']['configuration']['UserParameters'])
    InspectRun.job = event["CodePipeline.job"]["id"]
    InspectRun.go()