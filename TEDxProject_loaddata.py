###### TEDx-Load-Aggregate-Model
######

import sys
import json
import pyspark
from pyspark.sql.functions import col, collect_list, array_join, struct

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

##### FROM FILES
tedx_dataset_path = "s3://tedxprojectdata/tedx_dataset.csv"


###### READ PARAMETERS
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

##### START JOB CONTEXT AND JOB
sc = SparkContext()


glueContext = GlueContext(sc)
spark = glueContext.spark_session


    
job = Job(glueContext)
job.init(args['JOB_NAME'], args)


#### READ INPUT FILES TO CREATE AN INPUT DATASET
tedx_dataset = spark.read \
    .option("header","true") \
    .option("quote", "\"") \
    .option("escape", "\"") \
    .csv(tedx_dataset_path)
    
tedx_dataset.printSchema()


#### FILTER ITEMS WITH NULL POSTING KEY
count_items = tedx_dataset.count()
count_items_null = tedx_dataset.filter("idx is not null").count()

print(f"Number of items from RAW DATA {count_items}")
print(f"Number of items from RAW DATA with NOT NULL KEY {count_items_null}")



## READ TAGS DATASET
tags_dataset_path = "s3://tedxprojectdata/tags_dataset.csv"
tags_dataset = spark.read.option("header","true").csv(tags_dataset_path)

## READ WATCH NEXT DATASET
watch_next_dataset_path = "s3://tedxprojectdata/watch_next_dataset.csv"
watch_next_dataset = spark.read.option("header","true").csv(watch_next_dataset_path)


# CREATE THE AGGREGATE MODEL, ADD TAGS TO TEDX_DATASET AND WATCH NEXT
tags_dataset_agg = tags_dataset.groupBy(col("idx").alias("idx_ref")).agg(collect_list("tag").alias("tags"))
tags_dataset_agg.printSchema()
tedx_dataset_agg = tedx_dataset.join(tags_dataset_agg, tedx_dataset.idx == tags_dataset_agg.idx_ref, "left") \
    .drop("idx_ref")
tedx_dataset_agg.printSchema()

watch_next_dataset_agg = watch_next_dataset.select(col("idx"), struct( col("watch_next_idx"), col("url") ).alias("watch_next")).groupBy(col("idx").alias("idx_ref_one")).agg(collect_list("watch_next").alias("watch_next_list"))
watch_next_dataset_agg.printSchema()

## FINAL AGGREGATE MODEL
tedx_dataset_agg_total = tedx_dataset_agg.join(watch_next_dataset_agg, tedx_dataset_agg.idx == watch_next_dataset_agg.idx_ref_one, "left") \
 .drop("idx_ref_one").select(col("idx").alias("_id"), col("*")).drop("idx")
tedx_dataset_agg_total.printSchema()




mongo_uri = "mongodb://mycluster-shard-00-00-8imd2.mongodb.net:27017,mycluster-shard-00-01-8imd2.mongodb.net:27017"

write_mongo_options = {
    "uri": mongo_uri,
    "database": "unibg_tedx",
    "collection": "tedz_data",
    "username": "admin",
    "password": "xxx",
    "ssl": "true",
    "ssl.domain_match": "false"}
from awsglue.dynamicframe import DynamicFrame
tedx_dataset_dynamic_frame = DynamicFrame.fromDF(tedx_dataset_agg_total, glueContext, "nested")

glueContext.write_dynamic_frame.from_options(tedx_dataset_dynamic_frame, connection_type="mongodb", connection_options=write_mongo_options)
