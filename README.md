# E-Commerce Data Platform

A comprehensive data engineering project that demonstrates the integration of modern technologies for real-time and batch data processing.
This project simulates a production-grade data pipeline for an e-commerce platform, inspired by large-scale logistics companies. It ingests order events via Kafka, processes them using Spark, orchestrates workflows with Airflow and loads curated data into a data warehouse for analytics.

## Platform Startup (Current)

1. Start infrastructure (Kafka, Zookeeper, Postgres, Kafka UI, topic init):
```powershell
docker-compose up -d
```

2. Start the producer API:
```powershell
cd order-producer
.\mvnw.cmd spring-boot:run
```

3. In another terminal, start Spark streaming (Docker profile):
```powershell
cd ..
docker compose --profile spark up spark-stream
```

4. Send sample orders:
```powershell
Get-Content order-producer\sample-order-requests.jsonl | ForEach-Object {
  Invoke-RestMethod -Method Post -Uri "http://localhost:8082/orders" -ContentType "application/json" -Body $_
}
```

5. Stop services:
```powershell
docker compose --profile spark down
docker-compose down
```

## Architecture

```
Data Sources
    ↓
Kafka (Message Broker)
    ↓
┌───────────────┬──────────────────┐
│   Batch Job   │  Streaming Job   │
│   (Spark)     │   (Spark)        │
└───────────────┴──────────────────┘
    ↓
Data Warehouse (PostgreSQL)
    ↓
Analytics and Reporting
```

## Components

- **order-producer**: Java application that generates orders and sends them to Kafka
- **spark-jobs**: Spark jobs for batch and streaming processing
- **airflow**: Data pipeline orchestration
- **warehouse**: Database and data schema
- **kafka**: Kafka topic configuration
- **docs**: Technical documentation

## Quick Start

1. Start the services:
```bash
docker-compose up -d
```

2. Start the Order Producer (from `order-producer/` directory):
```bash
mvn spring-boot:run
```

3. Consult the documentation in `docs/` for details on architecture and data model

## Documentation

- **[Order Producer](docs/ORDER_PRODUCER.md)** - Complete guide to the Kafka producer, testing, retry strategy, and logging

## Technologies

- Apache Kafka
- Apache Spark
- Apache Airflow
- PostgreSQL
- Docker
- Java 17+
- Python 3.8+


## Docker Commands

```powershell
docker-compose up -d
docker compose --profile spark up spark-stream -d
docker compose --profile spark down
docker-compose down
```
