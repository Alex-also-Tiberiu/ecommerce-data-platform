# Order Producer Guide

## Overview
`order-producer` is a Spring Boot service exposing `POST /orders` on port `8082`.  
Each request is converted into an `OrderCreated` event and published to Kafka topic `order-created`.

## Prerequisites
From repository root:

```powershell
docker-compose up -d
```

This starts Kafka and supporting services.

## Run the Producer
From `order-producer`:

```powershell
.\mvnw.cmd spring-boot:run
```

The API will be available at `http://localhost:8082/orders`.

## Run Spark Streaming Consumer
From repository root:

```powershell
docker compose --profile spark up spark-stream
```

Keep this terminal open to see:
- valid parsed events
- invalid events
- daily aggregates (orders count and revenue)

This mode is reproducible and avoids local Windows Spark setup (`winutils`, `HADOOP_HOME`).

## Send Sample Orders via API
Use prepared payloads from:
`order-producer/sample-order-requests.jsonl`

From repository root:

```powershell
Get-Content order-producer\sample-order-requests.jsonl | ForEach-Object {
  Invoke-RestMethod -Method Post -Uri "http://localhost:8082/orders" -ContentType "application/json" -Body $_
}
```

## Single Request Example
```powershell
$body = '{"customer_id":"CUST-123","items":[{"product_id":"P1","quantity":2,"unit_price":10.5}],"price":21.0}'
Invoke-RestMethod -Method Post -Uri "http://localhost:8082/orders" -ContentType "application/json" -Body $body
```

## Stop Services
From repository root:

```powershell
docker-compose down
```

If you started the Spark profile, stop it with:

```powershell
docker compose --profile spark down
```
