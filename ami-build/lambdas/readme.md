# Inspector Security Assessment Process

This stage of the pipeline consists of two Lambda functions and two SNS Topics. The order of the functions is as follows:

`AmazonInspectorRun` Lambda > SNSTopic1 > `InspectorResult` Lambda > SNSTopic2

## InspectorRun Lambda

The first Lambda function `AmazonInspectorRun` is created as part of this pipeline, and will take some parameters from the Pipeline, importantly the AMIID. It will then launch a temporary EC2 instance using that AMI, install the AmazonInspector Agent through the instance user data, and run an Amazon inspector report using the inspector template defined in the `cf-templates/master.yml` on lines 103-105 (which are pulled from SSM Parameter Store).

Once the Inspector Assessment has completed the Lambda function will then pass the report on to the SNS Topic in the template mentioned above.

## InsepctorResult Lambda

The second Lambda Function is triggered by the SNS Topic that the InsepctorRun lambda publishes the SecurityReport to. It will take the report, extract key information, format it, and then publish it to a second SNS topic which will then email the processed report to it's participants. 

Once that has been completed the Lambda fucntion deletes the EC2 instance that was setup in the first lambda function to be used for testing.

Note: This lambda function is created as part of a wider core components CloudFormation Stack and is not created or managed by this pipeline. The source code of the Lambda has been uploaded to `ami-build/lambdas/InspectorResult.py` for visability purposes.