import os
import json
import mlflow
import requests
from jinja2 import Template
from mlflow.tracking import MlflowClient


def ab_deployment(
    name, namespace, secret_name,
    model_a_name, model_a_version,
    model_b_name, model_b_version,
    model_a_traffic=50):

    client = MlflowClient()

    model_a_run_id = next(mv.run_id for mv in client.search_model_versions(f"name='{model_a_name}'") if mv.version == f"{model_a_version}")
    model_a_artifact_uri = mlflow.get_run(model_a_run_id).info.artifact_uri

    model_b_run_id = next(mv.run_id for mv in client.search_model_versions(f"name='{model_b_name}'") if mv.version == f"{model_b_version}")
    model_b_artifact_uri = mlflow.get_run(model_b_run_id).info.artifact_uri

    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "ab_deployment.json.j2")

    body = Template(open(filename).read()).render(
        name=name,
        namespace=namespace,
        secret_name=secret_name,
        model_a_name=model_a_name,
        model_a_artifact_uri=model_a_artifact_uri,
        model_b_name=model_b_name,
        model_b_artifact_uri=model_b_artifact_uri,
        model_a_traffic=model_a_traffic,
    )

    token = open("/var/run/secrets/kubernetes.io/serviceaccount/token").read()
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://kubernetes.default.svc.cluster.local"
    endpoint = f"/apis/machinelearning.seldon.io/v1alpha2/namespaces/{namespace}/seldondeployments?fieldManager=kubectl-create"

    return requests.post(
        url=url+endpoint,
        json=json.loads(body),
        headers=headers,
        verify=False,
        timeout=30
    )


def ab_undeployment(name, namespace):
    token = open("/var/run/secrets/kubernetes.io/serviceaccount/token").read()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = "https://kubernetes.default.svc.cluster.local"
    endpoint = f"/apis/machinelearning.seldon.io/v1/namespaces/{namespace}/seldondeployments/{name}"

    return requests.delete(
        url=url+endpoint,
        headers=headers,
        verify=False,
        timeout=30
    )
