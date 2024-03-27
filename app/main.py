from kubernetes import client, config
import k8s as k
import time, os

def main():
    # config.load_kube_config()
    config.load_incluster_config()
    core_api_instance = client.CoreV1Api()
    custom_api_instance = client.CustomObjectsApi()
    apps_api_instance = client.AppsV1Api()
    namespaces = k.list_namespaces(core_api_instance)       # List namespaces
    print(f"Namespaces detected: {','.join(namespaces)}")

    k.read_custom_resource(custom_api_instance, core_api_instance, apps_api_instance, namespaces)

if __name__ == '__main__':
    while True:
        main()
        time.sleep(int(os.getenv("FETCH_TIME_INTERVAL", 60)))