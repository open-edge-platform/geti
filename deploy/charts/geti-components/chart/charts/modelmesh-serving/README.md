# modelmesh-serving


## Creating OVMS inference service guide

In order to deploy a modelmesh inference service with OV model loaded, follow these steps:
1. Train a model on the platform
2. Download OV model
3. Create a python venv, install awscli:
   `pip install awscli`
4. Create port-forward to seaweed-fs:
   `kubectl port-forward -n impt services/impt-seaweed-fs 8333:8333 &`
5. Get seaweed fs credentials: 
   `kubectl get secret -n impt impt-seaweed-fs -o jsonpath='{.data.admin_access_key}' | base64 -d`
   `kubectl get secret -n impt impt-seaweed-fs -o jsonpath='{.data.admin_secret_key}' | base64 -d`
6. Configure awscli (provide access/secret key when prompted):
   `aws configure`
7. Upload OV model to seaweed-fs:
   `aws s3 cp --recursive <path to downloaded model>/ s3://modelmesh/ovms_test_model --endpoint-url http://localhost:8333`
8. Create an `inference-service.yaml` file with following content:
```
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: example-ovms
  annotations:
    serving.kserve.io/deploymentMode: ModelMesh
spec:
  predictor:
    model:
      modelFormat:
        name: openvino_ir
      storage:
        key: modelmesh
        path: ovms_test_model
```
9. Create InferenceService by running:
```
kubectl apply -f inference-service.yaml
```
10. Modelmesh inference service pods should start afterwards, and load model from seaweed-fs for inference
11. use gRPC client from `for_developers/modelmesh_grpc_client` to perform inference on deployed model