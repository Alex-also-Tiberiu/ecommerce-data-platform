# Order Producer Documentation

## Overview

The Order Producer is a Spring Boot application that:
- Generates OrderCreated events with unique identifiers
- Sends events to Kafka with guaranteed durability (`acks: all`)
- Implements idempotent producer semantics to prevent duplicates
- Includes exponential backoff retry strategy
- Provides structured logging with correlation IDs for end-to-end tracing

## Features Implemented

### 1. Idempotency
- `enable.idempotence: true` ensures Kafka deduplicates messages
- `orderId` serves as the message key for partitioning
- Prevents duplicate orders in case of network retries

### 2. Retry Strategy with Exponential Backoff
- **retries**: 3 attempts
- **retry.backoff.ms**: 100ms initial backoff
- **retry.backoff.max.ms**: 32s maximum backoff
- **delivery.timeout.ms**: 120s total timeout

Backoff sequence: 100ms → 200ms → 400ms → (capped at 32s)

### 3. Structured Logging
- **correlationId**: Unique identifier per HTTP request for end-to-end tracing
- **orderId**: Business identifier for the order
- **timing**: Duration measurements for latency tracking
- **partition/offset**: Kafka metadata for debugging

## Configuration

See `order-producer/src/main/resources/application.yaml`:

```yaml
spring:
  kafka:
    producer:
      acks: all                    # Wait for broker acknowledgment
      retries: 3                   # Retry attempts
      enable.idempotence: true     # Enable deduplication
      retry.backoff.ms: 100        # Initial backoff
      retry.backoff.max.ms: 32000  # Max backoff
      delivery.timeout.ms: 120000  # Total timeout (2 minutes)
      compression.type: snappy     # Message compression

logging:
  level:
    com.panda: DEBUG               # Application logs
    org.springframework.kafka: DEBUG # Kafka client logs
```

## API Endpoints

### POST /orders

Creates a new order and sends it to Kafka.

**Request Body:**
```json
{
  "customer_id": "CUST-123",
  "items": [
    {
      "product_id": "P1",
      "quantity": 2,
      "unit_price": 10.5
    },
    {
      "product_id": "P2",
      "quantity": 4,
      "unit_price": 12.5
    }
  ],
  "price": 71.0
}
```

**Response (201 Created):**
```json
{
  "message": "Order created successfully",
  "order_id": "ORD-ABC123DEF456",
  "correlation_id": "a1b2c3d4-e5f6-47g8-h9i0-j1k2l3m4n5o6"
}
```

## Testing

### Prerequisites

Ensure Kafka is running:
```bash
docker-compose up -d
sleep 30  # Wait for Kafka to be ready
```

### Test 1: Successful Order Creation

```bash
curl -X POST http://localhost:8082/orders \
  -H "Content-Type: application/json" \
  -d '{
  "customer_id": "CUST-123",
  "items": [
    {
      "product_id": "P1",
      "quantity": 2,
      "unit_price": 10.5
    }
  ],
  "price": 21.0
}'
```

**Expected Response:**
```
HTTP 201 Created
{
  "message": "Order created successfully",
  "order_id": "ORD-...",
  "correlation_id": "..."
}
```

**Expected Log Output:**
```
INFO  Order request received - correlationId: abc123, customerId: CUST-123
DEBUG Preparing to send event - correlationId: abc123, orderId: ORD-..., size: 287 bytes
INFO  Event sent to Kafka - correlationId: abc123, orderId: ORD-..., partition: 0, offset: 42, durationMs: 145
INFO  Order created successfully - correlationId: abc123, orderId: ORD-..., durationMs: 150
```


## Understanding Logs

| Log Field | Purpose |
|-----------|---------|
| `correlationId` | Unique request identifier for end-to-end tracing |
| `orderId` | Business identifier for the order |
| `customerId` | Customer identifier from the request |
| `partition` | Kafka partition assigned to the message |
| `offset` | Message offset in the Kafka topic |
| `durationMs` | Latency measurement (lower is better) |
| `size` | Message size in bytes |

## Troubleshooting

**Issue: "Connection to node -1 could not be established"**
- Kafka is not running or not accessible at `localhost:9093`
- Solution: `docker-compose up -d` and wait 30 seconds

**Issue: "delivery timeout exceeded"**
- Producer couldn't reach Kafka within 120 seconds
- This is expected behavior when Kafka is offline
- Solution: Ensure Kafka is running before sending requests

**Issue: No logs visible**
- Check logging level in `application.yaml`
- Ensure `com.panda: DEBUG` is configured
- Restart the application after config changes
