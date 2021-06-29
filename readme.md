# Overview
This repository contains the files & templates that will create a GoldenAMI creation CodePipeline created for OUP EAC.

# Deployment Requirments
Please follow the below instructions prior to deployment:

### File Upload
- Create a Source S3 bucket (this will be used to hold the files used in the deployment)
- Create a prefix in the bucket with the same name as the pipeline will be called
- Upload the three Cloudformation templates into the created bucket/prefix
- Move the InspectorRun.py file to a zip folder and upload this to the ROOT of the S3 bucket

### SSM Parameters 
- Check the SSM Parameter store and make sure it already has the parameters created that the stack will use
- Note down the Parameter name formatr and affix as these will need to be input as CF Parameters upon deployment
    - For example the /EAC-CommonComponents-common/ is used in the Dev account. This will require the following CF Parameters:
        - UpstreamStack: EAC-CommonComponents
        - Environment: common

### GitHub Parameters
- Make sure you have the correct GitHub details prior to deployment. You will need
    - Repository Name, Branch Name, Respository Owner & Authorisation Token


# Deployment
- Navigate to CloudFormation and select Create Stack > With new resources (standard)
- In the specify a template section paste the S3 URL of the master.yml template > Next
- Enter all of the parameters with the data gathered in the Requirements section > Next > Next
- Accept the IAM Capability warnings and click 'Create Stack'

## Sample Parameters for EAC-Dev New Account
Stack Name: EAC-Core-GoldenAMI-Pipeline
Project: eac-core
Environment: common
UpstreamStack: EAC-CommonComponents
CodeBuildEnvironment: Default
Repo: eac-core-golden-AMI
repo owner: OUP
AuthToken: GenerateYourOwnAuthToken
Branch: master
PipelineName: eac-core-pipeline
SourceBucket: eac-core-golden-ami-pipeline