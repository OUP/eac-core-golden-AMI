# Repository Structure
This pipeline is currently setup in a way where each environment that it is deployted in has it's own branch. If you are making changes to a specific environment or are loking for documentation/procedures for them please switch to the retrospective environment branch. General documentation can be found here in the master.

# Overview
This repository contains the files & templates that will create a GoldenAMI creation CodePipeline created for OUP EAC, this is part of a two-pipeline deployment process. This pipeline will take a standard Amazon Linux 2 AMI, install software, perform security updates and run an Amazon Inspector Security assessment before finally publishing the AMI ID to AWS SSM Parameter Store.

# Pipeline Walkthrough
Below is a brief overview of the pipeline, it's stages and how it interacts with all the files contained inside this repository.

- Source Stage
    - This stage looks to this GitHub repository and will automatically trigger the pipeline upon any commits to the retrospective environment branches
- Build Stage
    - This stage uses CodeBuild with the `buildspec.yml` file to install and build Apache Tomcat & Packer
    - It will then validate and run the `ami-build/packer.json` file which will create an AMI with security updates installed & the built Apache Tomcat, Java 8 installed
    - This AMI ID will then be published to the SSM Parameter Store to be used in the Scan Stage
- Scan Stage
    - This stage runs a lambda function with the `ami-build/lambdas/InspectorRun.py` code to perform an AWS Inspector Security Assessment
    - It does this by taking the AMI ID published in the previous stage, creating an instance from it, performing an Inspector assessment & outputting the report via SNS
        - Note: The report is sent to an SNS topic which triggers a second lambda already created, which formats it, and then sends it to another topic which sends it via email
- Deploy Stage
    - This stage uses CodeBuild with the `buildspec_deploy.yml` file to perform a final deploy of the AMI ID
    - It takes the AMI ID from the Build Stage and publishes it to a final SSM Parameter as well as publishing an event to EventBridge when complete


# Pipeline Update Procedure
Procedures for updating already deployed versions of this pipeline can be found in the retrospective environment branches.

# Fresh Deployment Procedure/Requirements
Please follow the below instructions prior to a brand-new deployment of this pipeline. Current CloudFormation deployment parameters are listed in the `configs` folder of this repository. Please ensure these are kept up to date with any parameter changes.

### Documentation
- Create a new branch in this repository with the branch name being the environment you are deploying to (i.e dev, stage, prod)
- Copy the files from one of the current environment branches and update as necessary
- Two files of note which will need updated:
    - readme.md file
    - /configs/environment-name.json (environment-name being replaced with your new environment name)

### File Upload
- Create/locate a Source S3 bucket (this will be used to hold the files used in the deployment)
- Create a prefix in the bucket with the same name as the pipeline will be called
- Upload the three Cloudformation templates into the created bucket/prefix
- Move the `InspectorRun.py` file to a zip folder and upload this to the ROOT of the S3 bucket

### SSM Parameters 
- Check the SSM Parameter store and make sure it already has the parameters created that the stack will use
- Note down the Parameter name format and affix as these will need to be input as CF Parameters upon deployment
    - For example the /EAC-CommonComponents-common/ is used in the Dev account. This will require the following CF Parameter:
        - UpstreamStack: EAC-CommonComponents-common

### GitHub Parameters
- Make sure you have the correct GitHub details prior to deployment. You will need
    - Repository Name, Branch Name, Repository Owner & Authorisation Token (Auth token soon to be removed in place of GitHub app)

### Deployment
- Navigate to CloudFormation and select Create Stack > With new resources (standard)
- In the specify a template section paste the S3 URL of the master.yml template > Next
- Enter all of the parameters with the data gathered in the Requirements section > Next > Next
- Accept the IAM Capability warnings and click 'Create Stack'

# Useful Links
- [CHQ GDrive Folder](https://drive.google.com/drive/folders/1ZFyiNBvl1q3CWFzWcuzOgRQRKIH3K3ue)
- [CoreBuilder Pipeline Repository](https://github.com/OUP/eac-core-pipeline/tree/infra)
- [CHQ Jira Ticket](https://cirrushq.atlassian.net/browse/OUPEAC-5043)