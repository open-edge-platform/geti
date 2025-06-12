# flyte-core

Source: https://github.com/flyteorg/flyte

This is a modified helm chart of flyte-core, with platform-specific features (like seaweed-fs support) added.

Refer to https://github.com/flyteorg/flyte/tree/master/charts/flyte-core for chart configuration and docs.

In order to connect to flyte with flytectl, setup port forwarding first:
```bash
kubectl -n flyte port-forward svc/flyteadmin 30081:81 &
kubectl -n impt port-forward svc/impt-seaweed-fs 8333:8333 &
```

After setting up port-forward, flytectl should be working with default configuration settings. If you will see connection errors, make sure that admin.endpoint field in ~/.flyte/config.yaml is set to dns:///localhost:30081.

## Accessing flyte web UI console

In order to connect to flyte with Flyte console, setup port forwarding first:
```bash
kubectl -n flyte port-forward svc/flyteadmin 30080:80 &
kubectl port-forward -n flyte svc/flyteconsole 8080:80 &
```

After port forwarding is set, you should be able to access Flyte console on `localhost:8080/console` address.

*It is required to disable CORS in your browser to allow Flyte Console access to the Flyte Admin API*
