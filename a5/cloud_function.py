from google.cloud import monitoring_v3
import base64
import time
from datetime import datetime
import logging
import csv
import io
from google.cloud import storage
from google.cloud.storage import Blob

PROJECT_ID = "pe-training"  # Set project id


def upload_file_obj_to_bucket(bucket_name, object_path, file_obj, content_type=None):
    """
    Uploads file to bucket.
    :param bucket_name: Name of bucket
    :param object_path: Path where object will be uploaded to bucket
    :param file_obj: File like object to be uploaded
    :return: None
    """
    try:
        client = storage.Client(project="pe-training")
        bucket = client.get_bucket(bucket_name)  # Create bucket object
        blob = Blob(object_path, bucket)  # Create blob of object
        blob.upload_from_file(file_obj, content_type=content_type)  # Upload to bucket
    except Exception as e:
        logging.error("Error while uploading file")
        logging.error(e)


def cloud_monitoring_report(event, context):
    """
    Creates a report of average daily CPU utilization of every instance for each day in the past one week.
    :param event: Not used
    :param context: Not used
    :return: None
    """
    # https://cloud.google.com/monitoring/custom-metrics/reading-metrics
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(PROJECT_ID)  # Reports metrics for specific project.
    interval = monitoring_v3.types.TimeInterval()
    now = time.time()
    interval.end_time.seconds = int(now)
    interval.end_time.nanos = int((now - interval.end_time.seconds) * 10 ** 9)  # Find nanoseconds offset.
    interval.start_time.seconds = int(now - 604800)  # 604800 seconds = 7 days
    interval.start_time.nanos = interval.end_time.nanos
    aggregation = monitoring_v3.types.Aggregation()
    aggregation.alignment_period.seconds = 86400  # 86400 seconds = 1 day
    aggregation.per_series_aligner = monitoring_v3.enums.Aggregation.Aligner.ALIGN_MEAN
    # Take mean of CPU utilization in one day.

    results = client.list_time_series(
        project_name,
        'metric.type = "compute.googleapis.com/instance/cpu/utilization"',
        interval,
        monitoring_v3.enums.ListTimeSeriesRequest.TimeSeriesView.FULL,
        aggregation)
    csvstring = io.StringIO()  # Create a file like object which can be uploaded to storage.
    headers = ["Instance ID", "Instance Type", "Instance Zone", "Date 1", "Usage", "Date 2", "Usage", "Date 3", "Usage",
               "Date 4", "Usage", "Date 5", "Usage", "Date 6", "Usage", "Date 7", "Usage"]
    writer = csv.writer(csvstring, quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(headers)
    for result in results:
        # if len(result.points) >= 5:
        # Minimum of five days data to prevent excessive logs in testing (about 5 instances fulfil this criteria)
        row = [result.resource.labels["instance_id"], result.resource.type, result.resource.labels["zone"]]
        for point in result.points:
            row.append(datetime.utcfromtimestamp(int(point.interval.start_time.seconds)).strftime('%Y-%m-%d'))
            #  Convert UNIX timestamp to human readable format.
            row.append(point.value.double_value)  # CPU Utilization.
        writer.writerow(row)
    logging.info(csvstring.getvalue())
    csvstring.seek(0)  # Seek pointer back to start of filelike object
    upload_file_obj_to_bucket("kaustubhtest", f"{datetime.now():%Y-%m-%d}.csv", csvstring, "text/csv")
    # TODO: Send Email with this information
