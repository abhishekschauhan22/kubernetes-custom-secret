from kubernetes import client, config
from  aws import getParameterValue
import base64, os, time


def list_namespaces(core_api_instance):
    try:
        namespaces = core_api_instance.list_namespace().items
        namespace_list = []
        for namespace in namespaces:
            namespace_list.append(namespace.metadata.name)
        return namespace_list
    except Exception as e:
        print("Exception when calling CoreV1Api->list_namespace: %s\n" % e)

def read_custom_resource(custom_api_instance, core_api_instance, apps_api_instance, namespaces):

    # Specify the resource details
    group = 'custom.io'  # The API group of the custom resource
    version = 'v1'          # The version of the custom resource
    plural = 'customsecrets' # The plural name of the custom resource

    try:
        for namespace in namespaces:
            custom_resources = custom_api_instance.list_namespaced_custom_object(group, version, namespace, plural)
            for resource in custom_resources['items']:
                object_data = {}
                object_data['Name'] = resource['metadata']['name']
                object_data['Uid'] = resource['metadata']['uid']
                object_data['Namespace'] = namespace
                print(f"Checking for customsecret '{resource['metadata']['name']}' in namespace '{namespace}'.")
                object_data['Secrets'] = {}
                for pair in resource['spec']['secrets']:
                    object_data['Secrets'][pair['name']] = getParameterValue(pair['value'])
                create_secret(core_api_instance, apps_api_instance, object_data['Name'], object_data['Namespace'], object_data['Uid'], object_data['Secrets'])
    except Exception as e:
        print("Exception when calling CustomObjectsApi->list_namespaced_custom_object: %s\n" % e)

def create_secret(core_api_instance, apps_api_instance, secret_name, namespace, uid, data):
    RESTART_DEPLOYMENT = os.getenv("AUTO_RESTART_DEPLOYMENT", 'false')
    encoded_data = {key: base64.b64encode(value.encode()).decode() for key, value in data.items()}
    try:
        existing_secret = core_api_instance.read_namespaced_secret(secret_name, namespace)
        if existing_secret.data != encoded_data: 
            existing_secret.data = encoded_data
            response = core_api_instance.replace_namespaced_secret(secret_name, namespace, existing_secret)
            print(f"Secret '{secret_name}' updated in namespace '{namespace}'.")
            if RESTART_DEPLOYMENT.lower() == 'true':
                deployments_list = list_deployments_by_annotation(apps_api_instance, namespace, 'custom.io/custom-secret', secret_name)
                for deployment in deployments_list:
                    restart_deployment(apps_api_instance, namespace, deployment)
        else:
            print(f"Secret '{secret_name}' is unchanged in namespace '{namespace}'.")
    except client.rest.ApiException as e:
        if e.status == 404:
            secret_body = {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": secret_name,
                    "ownerReferences": [
                        {
                            "apiVersion": "custom.io/v1",
                            "kind": "CustomSecret",
                            "name": secret_name,
                            "uid": uid,
                            "controller": True,
                            "blockOwnerDeletion": True
                        }
                    ]
                },
                "data": encoded_data
            }

            try:
                api_response = core_api_instance.create_namespaced_secret(namespace, secret_body)
                print(f"Secret '{secret_name}' created in namespace '{namespace}'.")
            except Exception as e:
                    print("Exception when calling CoreV1Api->create_namespaced_secret: %s\n" % e)
        else:
            print(f"Error reading Secret '{secret_name}': {e}")

def list_deployments_by_annotation(apps_api_instance, namespace, annotation_key, secret_name):
    deployments = apps_api_instance.list_namespaced_deployment(namespace)
    annotated_deployments = []
    for deployment in deployments.items:
        annotations = deployment.metadata.annotations
        if annotations and annotation_key in annotations and annotations[annotation_key] == secret_name:
            annotated_deployments.append(deployment.metadata.name)
    return annotated_deployments

def restart_deployment(apps_api_instance, namespace, deployment_name):
    patch = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "timestamp": str(time.time())
                    }
                }
            }
        }
    }
    apps_api_instance.patch_namespaced_deployment(deployment_name, namespace, patch)

    print(f"Deployment '{deployment_name}' in namespace '{namespace}' restarted.")