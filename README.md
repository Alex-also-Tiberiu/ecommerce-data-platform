# E-Commerce Data Platform

A comprehensive data engineering project that demonstrates the integration of modern technologies for real-time and batch data processing.
This project simulates a production-grade data pipeline for an e-commerce platform, inspired by large-scale logistics companies. It ingests order events via Kafka, processes them using Spark, orchestrates workflows with Airflow and loads curated data into a data warehouse for analytics.

## Initialization Order

1️⃣ Kafka<br>
2️⃣ Spring Boot Producer<br>
3️⃣ Spark batch (file)<br>
4️⃣ Spark Kafka<br>
5️⃣ Postgres<br>
6️⃣ Airflow<br>

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


## Docker commands

1. Start
```bash
docker-compose up -d
```

2. Stop everything
```bash
docker-compose down
```
3. Delete volumes/networks (optional)
```bash
docker volume prune -f
```