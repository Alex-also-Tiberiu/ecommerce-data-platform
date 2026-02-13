# `process_orders.py` Example Output

This file contains an indicative execution output for:

```powershell
python spark-jobs\batch\process_orders.py
```

## Input preview

```text
+--------+--------------+-----------+-------------------------------------+-------+-------------+
|order_id|correlation_id|customer_id|items                                |price  |timestamp    |
+--------+--------------+-----------+-------------------------------------+-------+-------------+
|ORD-001 |corr-001      |CUST-123   |[{P1, 1.0, 1499.99}, {P2, 2.0, 50.0}]|1599.99|1704067200000|
|ORD-002 |corr-002      |CUST-123   |[{P3, 1.0, 149.99}]                  |149.99 |1704153600000|
|ORD-003 |corr-003      |CUST-456   |[{P4, 1.0, 299.99}]                  |299.99 |1704240000000|
|ORD-004 |corr-004      |CUST-789   |[{P5, 1.0, 159.99}, {P6, 1.0, 19.99}]|179.98 |1704326400000|
|ORD-005 |corr-005      |CUST-456   |[{P7, 1.0, 49.99}]                   |49.99  |1704412800000|
+--------+--------------+-----------+-------------------------------------+-------+-------------+
```

## Input schema

```text
root
 |-- order_id: string (nullable = true)
 |-- correlation_id: string (nullable = true)
 |-- customer_id: string (nullable = true)
 |-- items: array (nullable = true)
 |    |-- element: struct (containsNull = true)
 |    |    |-- product_id: string (nullable = true)
 |    |    |-- quantity: double (nullable = true)
 |    |    |-- unit_price: double (nullable = true)
 |-- price: double (nullable = true)
 |-- timestamp: long (nullable = true)
```

## Revenue by customer

```text
+-----------+-------------+-----------+---------------+
|customer_id|total_revenue|order_count|avg_order_value|
+-----------+-------------+-----------+---------------+
|CUST-123   |1749.98      |2          |874.99         |
|CUST-456   |349.98       |2          |174.99         |
|CUST-789   |179.98       |1          |179.98         |
+-----------+-------------+-----------+---------------+
```

## Global summary

```text
+------------+-------------+---------------+
|total_orders|total_revenue|avg_order_value|
+------------+-------------+---------------+
|5           |2279.94      |455.988        |
+------------+-------------+---------------+
```

## Orders with multiple items

```text
+--------+-----------+----------+-------+
|order_id|customer_id|item_count|price  |
+--------+-----------+----------+-------+
|ORD-001 |CUST-123   |2         |1599.99|
|ORD-004 |CUST-789   |2         |179.98 |
+--------+-----------+----------+-------+
```

## High-value orders (`threshold = 250.00`)

```text
+--------+-----------+-------+
|order_id|customer_id|price  |
+--------+-----------+-------+
|ORD-001 |CUST-123   |1599.99|
|ORD-003 |CUST-456   |299.99 |
+--------+-----------+-------+
```
