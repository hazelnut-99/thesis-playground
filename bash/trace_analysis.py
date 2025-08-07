from pyspark.sql import SparkSession
from pyspark.sql.functions import col, min, max, sum, count, avg, first
import json
import os

# Set Spark local directory
spark_local_directory = "/dev/shm/spark_tmp"
if not os.path.exists(spark_local_directory):
    os.makedirs(spark_local_directory, exist_ok=True)
    print(f"Created Spark local directory: {spark_local_directory}")

# Create SparkSession
spark = SparkSession.builder \
    .appName("CSVFileStatistics") \
    .master("local[*]") \
    .config("spark.driver.memory", "250g") \
    .config("spark.local.dir", spark_local_directory) \
    .config("spark.sql.shuffle.partitions", "2") \
    .config("spark.shuffle.compress", "true") \
    .config("spark.io.compression.codec", "lz4") \
    .getOrCreate()

cluster_name = "cluster12"
file_path = f"/nfs/hongshu/traces/{cluster_name}.csv"

# Read CSV and drop unnecessary columns
df = spark.read.csv(file_path, header=True, inferSchema=True).drop("next_access_vtime")

# Get first and last clock_time by sorting
first_row = df.first()
last_row = df.tail(1)[0] if df.count() > 0 else None

first_clock_time = first_row["clock_time"] if first_row else 0
last_clock_time = last_row["clock_time"] if last_row else 0
time_span = last_clock_time - first_clock_time if first_row and last_row else 0

# Aggregate request-level statistics
agg_results = df.agg(
    count("*").alias("number_of_requests"),
    min("object_size").alias("min_req_size"),
    max("object_size").alias("max_req_size"),
    sum("object_size").alias("total_req_size_bytes")
).collect()[0]

number_of_requests = agg_results["number_of_requests"]
min_req_size = agg_results["min_req_size"]
max_req_size = agg_results["max_req_size"]
total_req_size_bytes = agg_results["total_req_size_bytes"]

qps = (number_of_requests / time_span) if time_span > 0 else 0

# Group by object_id ONCE for all unique object stats
unique_objects_df = df.groupBy("object_id").agg(
    first("object_size").alias("unique_obj_size"),
    count("*").alias("frequency")
)

number_of_objects = unique_objects_df.count()
total_obj_size_bytes = unique_objects_df.agg(sum("unique_obj_size")).collect()[0][0]
frequency_mean = unique_objects_df.agg(avg("frequency")).collect()[0][0]

# Convert bytes to GiB
bytes_to_gib = 1024 * 1024 * 1024
number_of_req_GiB = total_req_size_bytes / bytes_to_gib
number_of_obj_GiB = total_obj_size_bytes / bytes_to_gib

# Compulsory miss ratios
compulsory_miss_ratio_req = number_of_objects / number_of_requests if number_of_requests > 0 else 0
compulsory_miss_ratio_byte = number_of_obj_GiB / number_of_req_GiB if number_of_req_GiB > 0 else 0

# Format results
results = {
    "number_of_requests": number_of_requests,
    "min_req_size": min_req_size,
    "max_req_size": max_req_size,
    "qps": round(qps, 4),
    "number_of_objects": number_of_objects,
    "number_of_req_GiB": round(number_of_req_GiB, 4),
    "number_of_obj_GiB": round(number_of_obj_GiB, 4),
    "compulsory_miss_ratio_req": round(compulsory_miss_ratio_req, 4),
    "compulsory_miss_ratio_byte": round(compulsory_miss_ratio_byte, 4),
    "time_span": time_span,
    "frequency_mean": round(frequency_mean, 4)
}

print(results)

# Define the output file path
output_file_path = f"/nfs/hongshu/traces/analysis_json/{cluster_name}.oracleGeneral.zst_analysis.json"

# Create parent directories if they don't exist
output_dir = os.path.dirname(output_file_path)
if not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

# Dump results to JSON file
try:
    with open(output_file_path, 'w') as f:
        json.dump(results, f, indent=4)
    print(f"Results successfully dumped to: {output_file_path}")
except Exception as e:
    print(f"Error dumping results to JSON file: {e}")

# Stop the SparkSession
spark.stop()