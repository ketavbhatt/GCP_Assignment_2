from google.cloud import monitoring_v3
import base64
import time
from datetime import datetime
import logging

PROJECT_ID = "pe-training"  # Set project id


def cloud_monitoring_report(event, context):
    """
    Creates a report of average daily CPU utilization of every instance for each day in the past one week.
    :param event: Not used
    :param context: Not used
    :return: None
    """
    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(PROJECT_ID)  # Reports metrics for specific project.
    interval = monitoring_v3.types.TimeInterval()
    now = time.time()
    interval.end_time.seconds = int(now)
    interval.end_time.nanos = int(
        (now - interval.end_time.seconds) * 10 ** 9)  # Find nanoseconds offset.
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
    for result in results:
        if len(result.points) >= 5:  # Minimum of five days to prevent too much log generation in testing
            for point in result.points:
                logging.info(point.value.double_value)  # CPU Utilization value
                logging.info(
                    datetime.utcfromtimestamp(int(point.interval.start_time.seconds)).strftime('%Y-%m-%d %H:%M:%S'))
                logging.info(
                    datetime.utcfromtimestamp(int(point.interval.end_time.seconds)).strftime('%Y-%m-%d %H:%M:%S'))
                # Convert UNIX timestamp to human readable format
            logging.info("instance_type={}".format(result.resource.type))  # Type of instance
            logging.info("instance_id={}".format(result.resource.labels["instance_id"]))  # ID of instance
            logging.info("zone={}".format(result.resource.labels["zone"]))  # Zone of instance
        # TODO: Send Email with this information
