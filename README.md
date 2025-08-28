# Graph Data Processing Pipeline — Phase 2 (Kafka + Kubernetes + Neo4j)

## Goal
Send trip events to Kafka → sink into Neo4j via Kafka Connect → run analytics against the live graph.

## Steps

### 0) Start Minikube
```bash
minikube start --memory=4096 --cpus=4
```

### 1) Deploy Zookeeper + Kafka (default namespace)
```bash
kubectl apply -f phase2/zookeeper-setup.yaml
kubectl apply -f phase2/kafka-setup.yaml
kubectl get pods,svc
```

You should see `zookeeper-service` and `kafka-service` with ports `2181`, `9092`, `29092`.

### 2) Install Neo4j via Helm (with GDS)
```bash
helm repo add neo4j https://helm.neo4j.com/neo4j
helm install my-neo4j neo4j/neo4j -f phase2/neo4j-values.yaml
kubectl get pods,svc
```

Ensure your `neo4j-values.yaml` sets a password (e.g., `changeme`) and enables the GDS plugin.

**Option A (values format that supports 'plugins'):**
```yaml
neo4j:
  password: changeme
  plugins:
    - graph-data-science
```

**Option B (via env var):**
```yaml
env:
  - name: NEO4J_PLUGINS
    value: '["graph-data-science"]'
```

### 3) Deploy Kafka → Neo4j Connector
Keep all resources in the same namespace (`default`) for simplicity.

Kafka bootstrap should match your service:
```
CONNECT_BOOTSTRAP_SERVERS=kafka-service:29092
```

Neo4j URI should match your service name:
```
"neo4j.server.uri": "bolt://my-neo4j:7687"
```

If you created a custom Service named `neo4j-service`:
```
"neo4j.server.uri": "bolt://neo4j-service:7687"
```

Password via env substitution:
```
"neo4j.authentication.basic.username": "neo4j",
"neo4j.authentication.basic.password": "${env:NEO4J_PASSWORD}"
```

### 4) Access Neo4j in the cluster
```bash
kubectl port-forward svc/my-neo4j 7474:7474 7687:7687
```

Neo4j Browser: [http://localhost:7474](http://localhost:7474)  
Credentials: `(neo4j / your password)`

### 5) Produce data and analyze
Send trip messages to Kafka (use your producer, or `kafkacat`/`kafka-console-producer`), then run:
```bash
python phase2/interface.py
```

You should see new nodes/relationships appearing and algorithm results updating accordingly.

## Expected Outcomes

### After Phase 1 ingestion:
- Nodes labeled `Location` (IDs as `name` property), edges labeled `TRIP` with `distance`, `fare`, `pickup_dt`, `dropoff_dt`.
- PageRank returns influential locations; BFS returns reachable targets from a given start.

### After Phase 2 streaming:
- New trips published to Kafka are transformed by the connector and persisted into Neo4j in near real-time.
- Running analytics again will reflect the new graph state.

## Troubleshooting

### Pods Pending / CrashLoopBackOff:
- Check resources: `minikube status`, bump memory/CPU.
- Inspect with: `kubectl describe pod <name>`

### Connector cannot resolve services:
- Keep everything in the `default` namespace, or use FQDN:
  ```
  kafka-service.default.svc.cluster.local:29092
  my-neo4j.default.svc.cluster.local:7687
  ```

### Neo4j auth errors:
- Ensure the password in Neo4j, your env (`NEO4J_PASSWORD`), and the connector JSON all match.

### GDS procedures not found:
- Ensure the plugin is enabled in `neo4j-values.yaml` (see examples above).
- Restart the pod if you change plugin config:
  ```bash
  helm upgrade my-neo4j neo4j/neo4j -f phase2/neo4j-values.yaml
  ```

### Can’t open Neo4j Browser:
- Port-forward: `kubectl port-forward svc/my-neo4j 7474:7474 7687:7687`
- Or run: `minikube service list`


**Note:** Never commit real tokens or passwords. If you ever did, rotate them and scrub history (`git filter-repo` or `BFG`).
