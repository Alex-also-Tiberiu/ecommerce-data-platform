# Task checklist day-by-day (realistic)

## 🗓️ Week 1 — Foundations (Kafka + Java)

### Day 1

* define `OrderCreated` event schema
* fields: `order_id`, `customer_id`, `items`, `price`, `timestamp`

### Day 2

* Spring Boot producer
* endpoint `/orders`
* produce event to Kafka

### Day 3

* setup Kafka (docker-compose)
* topic with partitions >1

### Day 4

* idempotency
* logging
* retry

### Day 5

* manual tests
* basic documentation

🎯 Output: real events flowing

---

## 🗓️ Week 2 — Spark (processing)

### Day 6

* setup Spark local
* read static data (file)

### Day 7

* Spark batch job
* basic transformations

### Day 8

* read from Kafka
* JSON parsing

### Day 9

* aggregations (orders per day, revenue)

### Day 10

* write to Postgres
* error handling

🎯 Output: transformed and persisted data

---

## 🗓️ Week 3 — Airflow (orchestration)

### Day 11

* Airflow concepts (DAG, task, operator)

### Day 12

* first static DAG

### Day 13

* Spark batch task

### Day 14

* retry + scheduling

### Day 15

* logging + basic alerting

🎯 Output: controlled and observable pipeline

---

## 🗓️ Week 4 — Cleanup & quality

### Day 16

* warehouse schema (fact + dimension)

### Day 17

* data quality checks (null, duplicates)

### Day 18

* analytics queries ready

### Day 19

* architecture documentation

### Day 20

* README refinement + diagram

🎯 Output: project completed
