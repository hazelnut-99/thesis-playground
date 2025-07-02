# calculate_stats.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, min, max, sum, count, countDistinct, lit, avg
import json
import os

# Define a new local directory for Spark
# Make sure this directory exists and has sufficient space
# Your /nfs/hongshu path seems suitable. Let's create a dedicated Spark temp directory within it.
spark_local_directory = "/nfs/hongshu/spark_tmp"

# Create this directory if it doesn't exist
if not os.path.exists(spark_local_directory):
    os.makedirs(spark_local_directory, exist_ok=True)
    print(f"Created Spark local directory: {spark_local_directory}")


# Create a SparkSession
spark = SparkSession.builder \
    .appName("CSVFileStatistics") \
    .master("local[*]") \
    .config("spark.driver.memory", "200g") \
    .config("spark.local.dir", spark_local_directory) \
    .getOrCreate()

file_path = "/nfs/hongshu/traces/cluster12.csv"

# Read the CSV file into a DataFrame
df = spark.read.csv(file_path, header=True, inferSchema=True)

# Rename columns for easier access (optional)
df = df.withColumnRenamed("clock_time", "clock_time") \
       .withColumnRenamed("object_id", "object_id") \
       .withColumnRenamed("object_size", "object_size") \
       .withColumnRenamed("next_access_vtime", "next_access_vtime")

# Calculate common aggregates in one go for efficiency
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

# Get first and last clock_time
first_clock_time_row = df.agg(min("clock_time")).collect()
first_clock_time = first_clock_time_row[0][0] if first_clock_time_row and first_clock_time_row[0][0] is not None else 0

last_clock_time_row = df.agg(max("clock_time")).collect()
last_clock_time = last_clock_time_row[0][0] if last_clock_time_row and last_clock_time_row[0][0] is not None else 0

time_span = last_clock_time - first_clock_time if first_clock_time is not None and last_clock_time is not None else 0

# Handle potential division by zero for time_span
qps = (number_of_requests / time_span) if time_span > 0 else 0

# Number of unique objects
number_of_objects = df.select(countDistinct("object_id")).collect()[0][0]

# Sum of object sizes for unique objects (number_of_obj_GiB)
unique_objects_df = df.groupBy("object_id").agg(min("object_size").alias("unique_obj_size"))
total_obj_size_bytes = unique_objects_df.agg(sum("unique_obj_size")).collect()[0][0]

# Convert bytes to GiB (1 GiB = 1024 * 1024 * 1024 bytes)
bytes_to_gib = 1024 * 1024 * 1024
number_of_req_GiB = total_req_size_bytes / bytes_to_gib
number_of_obj_GiB = total_obj_size_bytes / bytes_to_gib

# Compulsory miss ratios
compulsory_miss_ratio_req = number_of_objects / number_of_requests if number_of_requests > 0 else 0
compulsory_miss_ratio_byte = number_of_obj_GiB / number_of_req_GiB if number_of_req_GiB > 0 else 0

# Frequency Mean
frequency_df = df.groupBy("object_id").agg(count("*").alias("frequency"))
frequency_mean = frequency_df.agg(avg("frequency")).collect()[0][0]

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

# Define the output file path
output_file_path = "/nfs/hongshu/traces/analysis_json/cluster12.oracleGeneral.zst_analysis.json"

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