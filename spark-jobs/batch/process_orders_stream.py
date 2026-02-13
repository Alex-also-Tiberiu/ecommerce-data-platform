"""Spark Structured Streaming job for OrderCreated events from Kafka."""

import logging
import os
import sys
from typing import Tuple

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    col,
    count,
    date_trunc,
    from_json,
    sum as spark_sum,
    to_timestamp,
)
from pyspark.sql.types import (
    ArrayType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)

APP_NAME = "OrderCreatedStreaming"
DEFAULT_BOOTSTRAP_SERVERS = "localhost:9093"
DEFAULT_TOPIC = "order-created"
DEFAULT_CHECKPOINT_ROOT = "spark-jobs/checkpoints/order-created"
DEFAULT_TRIGGER_SECONDS = 10
DEFAULT_APP_LOG_LEVEL = "INFO"

# Runtime constants (edit here if needed)
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", DEFAULT_BOOTSTRAP_SERVERS)
TOPIC = os.getenv("TOPIC", DEFAULT_TOPIC)
STARTING_OFFSETS = os.getenv("STARTING_OFFSETS", "latest")
CHECKPOINT_ROOT = os.getenv("CHECKPOINT_ROOT", DEFAULT_CHECKPOINT_ROOT)
TRIGGER_SECONDS = int(os.getenv("TRIGGER_SECONDS", str(DEFAULT_TRIGGER_SECONDS)))
APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", DEFAULT_APP_LOG_LEVEL)
SPARK_INTERNAL_LOG_LEVEL = os.getenv("SPARK_INTERNAL_LOG_LEVEL", "ERROR")


def configure_logger(level: str) -> logging.Logger:
    """Configure script logger."""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logging.getLogger("py4j").setLevel(logging.ERROR)
    logging.getLogger("py4j.java_gateway").setLevel(logging.ERROR)
    return logging.getLogger(APP_NAME)


def get_order_schema() -> StructType:
    """Schema aligned with OrderCreated Java DTO and JSON schema."""
    item_schema = StructType(
        [
            StructField("product_id", StringType(), True),
            StructField("quantity", DoubleType(), True),
            StructField("unit_price", DoubleType(), True),
        ]
    )
    return StructType(
        [
            StructField("order_id", StringType(), True),
            StructField("correlation_id", StringType(), True),
            StructField("customer_id", StringType(), True),
            StructField("items", ArrayType(item_schema), True),
            StructField("price", DoubleType(), True),
            StructField("timestamp", LongType(), True),
        ]
    )


def create_spark_session() -> SparkSession:
    """Create Spark session for local streaming."""
    spark = (
        SparkSession.builder.appName(APP_NAME)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(SPARK_INTERNAL_LOG_LEVEL)
    suppress_internal_spark_logs(spark)
    return spark


def read_kafka_stream(
    spark: SparkSession, bootstrap_servers: str, topic: str, starting_offsets: str
) -> DataFrame:
    """Read raw Kafka stream for a single topic."""
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", bootstrap_servers)
        .option("subscribe", topic)
        .option("startingOffsets", starting_offsets)
        .load()
    )


def parse_orders(raw_stream: DataFrame, schema: StructType) -> Tuple[DataFrame, DataFrame]:
    """Parse Kafka JSON payload and split valid/invalid events."""
    with_payload = raw_stream.selectExpr(
        "CAST(value AS STRING) AS payload",
        "CAST(key AS STRING) AS message_key",
        "timestamp AS kafka_timestamp",
    )

    parsed = with_payload.withColumn("order", from_json(col("payload"), schema))

    valid_orders = (
        parsed.filter(col("order").isNotNull())
        .select("order.*", "message_key", "kafka_timestamp")
        .withColumn(
            "event_timestamp",
            to_timestamp((col("timestamp") / 1000).cast("double")),
        )
    )

    invalid_orders = parsed.filter(col("order").isNull()).select(
        "payload", "message_key", "kafka_timestamp"
    )

    return valid_orders, invalid_orders


def build_daily_aggregates(valid_orders: DataFrame) -> DataFrame:
    """Compute daily order count and revenue."""
    return (
        valid_orders.withColumn("event_day", date_trunc("day", col("event_timestamp")))
        .groupBy("event_day")
        .agg(
            count("order_id").alias("orders_count"),
            spark_sum("price").alias("daily_revenue"),
        )
        .orderBy(col("event_day").desc())
    )


def suppress_internal_spark_logs(spark: SparkSession) -> None:
    """Reduce Spark/Kafka/Hadoop logger noise in the console."""
    jvm = spark._jvm
    log_manager = jvm.org.apache.log4j.LogManager
    level = jvm.org.apache.log4j.Level.ERROR

    noisy_loggers = [
        "org",
        "akka",
        "org.apache.spark",
        "org.apache.kafka",
        "org.apache.hadoop",
        "org.sparkproject",
        "io.netty",
    ]
    for logger_name in noisy_loggers:
        log_manager.getLogger(logger_name).setLevel(level)

    # This shutdown warning is common on Windows due to temp-dir race cleanup.
    log_manager.getLogger("org.apache.spark.util.ShutdownHookManager").setLevel(
        jvm.org.apache.log4j.Level.FATAL
    )


def run_stream() -> int:
    """Start streaming queries and keep process alive."""
    logger = configure_logger(APP_LOG_LEVEL)
    spark  = create_spark_session()

    try:
        logger.info(
            "Starting stream bootstrap_servers=%s topic=%s offsets=%s",
            BOOTSTRAP_SERVERS,
            TOPIC,
            STARTING_OFFSETS,
        )

        raw_stream = read_kafka_stream(
            spark=spark,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            topic=TOPIC,
            starting_offsets=STARTING_OFFSETS,
        )
        valid_orders, invalid_orders = parse_orders(raw_stream, get_order_schema())
        daily_aggregates = build_daily_aggregates(valid_orders)

        valid_query = (
            valid_orders.writeStream.outputMode("append")
            .format("console")
            .option("truncate", "false")
            .option("numRows", 20)
            .option(
                "checkpointLocation",
                f"{CHECKPOINT_ROOT}/valid-orders",
            )
            .trigger(processingTime=f"{TRIGGER_SECONDS} seconds")
            .queryName("valid_orders_stream")
            .start()
        )

        invalid_query = (
            invalid_orders.writeStream.outputMode("append")
            .format("console")
            .option("truncate", "false")
            .option("numRows", 20)
            .option(
                "checkpointLocation",
                f"{CHECKPOINT_ROOT}/invalid-orders",
            )
            .trigger(processingTime=f"{TRIGGER_SECONDS} seconds")
            .queryName("invalid_orders_stream")
            .start()
        )

        aggregate_query = (
            daily_aggregates.writeStream.outputMode("complete")
            .format("console")
            .option("truncate", "false")
            .option("numRows", 20)
            .option(
                "checkpointLocation",
                f"{CHECKPOINT_ROOT}/daily-aggregates",
            )
            .trigger(processingTime=f"{TRIGGER_SECONDS} seconds")
            .queryName("daily_aggregates_stream")
            .start()
        )

        logger.info("Streaming queries started. Press Ctrl+C to stop.")
        spark.streams.awaitAnyTermination()

        valid_query.stop()
        invalid_query.stop()
        aggregate_query.stop()
        return 0
    except Exception as exc:
        logger.exception("Streaming job failed: %s", exc)
        return 1
    finally:
        spark.stop()


def main() -> None:
    """CLI entrypoint."""
    sys.exit(run_stream())


if __name__ == "__main__":
    main()
