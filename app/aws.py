import boto3

def getParameterValue(parameter_name):
    try:
        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        parameter_value = response['Parameter']['Value']
        return parameter_value
    except Exception as e:
        print("Exception retrieving ssm parameter value: %s\n" % e)