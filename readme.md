# Warning
This is the `infra` branch of this repository. The readme for this branch as been written for the infra environment, if you are working on a different environment, please switch to the correct branch for your retrospective environment.

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

## Pipeline files/config update
If any of the pipeline configuration files have been updated, including the buildspec's or the packer files commit the changes to the retrospective environment branch and the pipeline will automatically trigger and run with the updated configs.

## CloudFormation Stack Update
Please follow the below instructions prior to a CloudFormation Stack update of an already deployed version of this pipeline.

- Update the parameter list in the `configs/infra.json` folder with any new or updated parameters
- Commit any CloudFormation template changes to the `cf-templates` folder of this repository
- Upload the CloudFormation Templates into into the `eac-core-golden-ami` folder of the S3 bucket defined in the SourceBucket parameter of the `/configs/infra.json` file.
- Deploy changes manually through CLI or Console (as there is no pipeline builder pipeline for this project)

## Lambda Code Update
If the Lambda code has been updated, please commit the code to the `/ami-build/lambdas/` folder and then add the lambda code file to a zip folder and upload it into the ROOT of the S3 bucket defined in the SourceBucket parameter of the `/configs/infra.json` file.

# Fresh Deployment Procedure/Requirements
Please follow the steps listed in the master branch of this repository for instructions on how to perform a deployment of this pipeline to a new environment.

# Useful Links
- [CHQ GDrive Folder](https://drive.google.com/drive/folders/1ZFyiNBvl1q3CWFzWcuzOgRQRKIH3K3ue)
- [CoreBuilder Pipeline Repository](https://github.com/OUP/eac-core-pipeline/tree/infra)
- [CHQ Jira Ticket](https://cirrushq.atlassian.net/browse/OUPEAC-5043)