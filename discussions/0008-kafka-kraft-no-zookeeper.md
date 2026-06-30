# Single-node Kafka without ZooKeeper (KRaft) for a self-host — minimal config?

> Posted as a Q&A discussion: https://github.com/faizanxgp/homelab/discussions/33

## Question

Most self-hosted stacks that use Kafka still ship a ZooKeeper container alongside it. On a RAM-constrained box that's two heavy JVMs. Can I run a single-node Kafka without ZooKeeper for a self-host, and what's the minimal config?
## Answer

Yes — use **KRaft mode** (Kafka Raft), GA since Kafka 3.3. One process is both broker and controller; ZooKeeper is gone. Minimal single-node Compose (Bitnami image):

```yaml
kafka:
  image: bitnami/kafka:3.7
  environment:
    KAFKA_CFG_NODE_ID: "0"
    KAFKA_CFG_PROCESS_ROLES: "controller,broker"
    KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: "0@kafka:9093"
    KAFKA_CFG_LISTENERS: "PLAINTEXT://:9092,CONTROLLER://:9093"
    KAFKA_CFG_ADVERTISED_LISTENERS: "PLAINTEXT://kafka:9092"
    KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP: "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT"
    KAFKA_CFG_CONTROLLER_LISTENER_NAMES: "CONTROLLER"
    ALLOW_PLAINTEXT_LISTENER: "yes"
  volumes:
    - ./volumes/kafka:/bitnami/kafka
```

The essentials: a dedicated `CONTROLLER` listener on `:9093`, `PROCESS_ROLES=controller,broker`, and a quorum voter string `nodeId@host:9093`. Advertise `PLAINTEXT://kafka:9092` to in-network clients. That's one JVM instead of two — a real win on small hosts.
