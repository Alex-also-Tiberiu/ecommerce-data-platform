"""Batch Spark job to inspect and aggregate local order data."""

import logging
import sys

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import avg, col, count, size, sum as spark_sum
from pyspark.sql.types import ArrayType, DoubleType, LongType, StringType, StructField, StructType

DEFAULT_INPUT_PATH = "spark-jobs/data/orders.json"
DEFAULT_HIGH_VALUE_THRESHOLD = 200.0
DEFAULT_APP_LOG_LEVEL = "INFO"
APP_NAME = "OrderProcessingBatch"
SPARK_INTERNAL_LOG_LEVEL = "ERROR"

# Runtime constants (edit here if needed)
INPUT_PATH = DEFAULT_INPUT_PATH
HIGH_VALUE_THRESHOLD = DEFAULT_HIGH_VALUE_THRESHOLD
APP_LOG_LEVEL = DEFAULT_APP_LOG_LEVEL


def configure_logger(level: str) -> logging.Logger:
    """Create and configure logger for the job."""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logging.getLogger("py4j").setLevel(logging.ERROR)
    logging.getLogger("py4j.java_gateway").setLevel(logging.ERROR)
    return logging.getLogger(APP_NAME)


def get_order_schema() -> StructType:
    """Return explicit schema for local order input."""
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
    """Initialize Spark session for local execution."""
    spark = (
        SparkSession.builder.appName(APP_NAME)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(SPARK_INTERNAL_LOG_LEVEL)
    suppress_internal_spark_logs(spark)
    return spark


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


def load_orders(spark: SparkSession, input_path: str, schema: StructType) -> DataFrame:
    """Load order JSON using explicit schema."""
    return spark.read.option("multiLine", "true").schema(schema).json(input_path)


def validate_orders(df: DataFrame, logger: logging.Logger) -> None:
    """Fail fast when mandatory fields are missing."""
    required_columns = ["order_id", "customer_id", "items", "price"]
    missing_columns = [name for name in required_columns if name not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    null_critical_rows = df.filter(
        col("order_id").isNull() | col("customer_id").isNull() | col("price").isNull()
    ).count()
    if null_critical_rows > 0:
        raise ValueError(f"Found {null_critical_rows} rows with null critical fields.")

    logger.info("Validation passed for required columns and critical null checks.")


def compute_revenue_by_customer(df: DataFrame) -> DataFrame:
    """Aggregate order count and revenue metrics by customer."""
    return (
        df.groupBy("customer_id")
        .agg(
            spark_sum("price").alias("total_revenue"),
            count("order_id").alias("order_count"),
            avg("price").alias("avg_order_value"),
        )
        .orderBy(col("total_revenue").desc())
    )


def compute_summary(df: DataFrame) -> DataFrame:
    """Compute global summary metrics over all orders."""
    return df.agg(
        count("order_id").alias("total_orders"),
        spark_sum("price").alias("total_revenue"),
        avg("price").alias("avg_order_value"),
    )


def compute_multi_item_orders(df: DataFrame) -> DataFrame:
    """Return orders containing more than one item."""
    return (
        df.withColumn("item_count", size(col("items")))
        .filter(col("item_count") > 1)
        .select("order_id", "customer_id", "item_count", "price")
    )


def compute_high_value_orders(df: DataFrame, threshold: float) -> DataFrame:
    """Return orders with price above the configured threshold."""
    return (
        df.filter(col("price") > threshold)
        .select("order_id", "customer_id", "price")
        .orderBy(col("price").desc())
    )


def run_job() -> int:
    """Execute the batch analytics flow and print result snapshots."""
    logger = configure_logger(APP_LOG_LEVEL)
    spark = create_spark_session()

    try:
        logger.info("Starting batch job. input_path=%s", INPUT_PATH)
        orders = load_orders(spark, INPUT_PATH, get_order_schema())
        validate_orders(orders, logger)

        logger.info("Input preview")
        orders.show(truncate=False)
        logger.info("Input schema")
        orders.printSchema()

        logger.info("Revenue by customer")
        compute_revenue_by_customer(orders).show(truncate=False)

        logger.info("Global summary")
        compute_summary(orders).show(truncate=False)

        logger.info("Orders with multiple items")
        compute_multi_item_orders(orders).show(truncate=False)

        logger.info("High-value orders with threshold %.2f", HIGH_VALUE_THRESHOLD)
        compute_high_value_orders(orders, HIGH_VALUE_THRESHOLD).show(
            truncate=False
        )

        logger.info("Batch job completed successfully.")
        return 0
    except Exception as exc:
        logger.exception("Batch job failed: %s", exc)
        return 1
    finally:
        spark.stop()


def main() -> None:
    """CLI entrypoint."""
    sys.exit(run_job())


if __name__ == "__main__":
    main()
