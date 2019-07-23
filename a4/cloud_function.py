from google.cloud import vision
from google.cloud import datastore
import logging


def store_objects_in_datastore(uri, objects):
    """
    Store object information in datastore.
    :param uri: The path to the image in Google Cloud Storage (gs://bucket-name/object-path)
    :param objects: Objects localized in the uploaded image
    :return: None
    """
    client = datastore.Client()
    for i, object in enumerate(objects):
        identifier = "{}/{}".format(uri, i)
        key = client.key('KaustubhObjectDetection', identifier)  # Kind='KaustubhObjectDetection', identifier=identifier
        entity = datastore.Entity(key=key)
        odict = {
            'name': object.name,
            'confidence': object.score
        }
        vertices = []
        for vertex in object.bounding_poly.normalized_vertices:
            vertices.append("({},{})".format(vertex.x, vertex.y))  # Lists cannot be nested, so stored as single string
        odict['vertices'] = vertices
        entity.update(odict)  # Add properties to entity.
        client.put(entity)  # Add entity to cloud datastore.


def localize_objects(uri):
    """
    Localize objects in the image on Google Cloud Storage.
    :param uri: The path to the file in Google Cloud Storage (gs://bucket-name/object-path).
    :return: List of objects localized in the uploaded image.
    """
    logging.info(uri)
    client = vision.ImageAnnotatorClient()

    image = vision.types.Image()
    image.source.image_uri = uri  # Set uri to bucket location.
    try:
        objects = client.object_localization(image=image).localized_object_annotations  # Localize objects in image.
    except Exception as e:
        logging.error("Error while localizing objects in image")
        logging.error(e)
        return

    logging.info('Number of objects found: {}'.format(len(objects)))
    for object in objects:  # Log information regarding every object.
        logging.info('\n{} (confidence: {})'.format(object.name, object.score))
        logging.info('Normalized bounding polygon vertices: ')
        for vertex in object.bounding_poly.normalized_vertices:
            logging.info(' - ({}, {})'.format(vertex.x, vertex.y))

    return objects


def trigger(event, context):
    """
    Background Cloud Function to be triggered by Cloud Storage.
    This generic function logs relevant object detection data and stores it in google cloudstore
     when a file is changed.
    :param event: The Cloud Functions event payload.
    :param context: Metaevent of triggering event.
    :return: None
    """
    logging.info(event)
    logging.info(context)
    # https://cloud.google.com/vision/docs/supported-files
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Complete_list_of_MIME_types
    allowed_types = {'image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/webp', 'image/vnd.microsoft.icon',
                     'application/pdf', 'image/tiff'}  # set of allowed content types.
    if event['contentType'] in allowed_types:
        uri = "gs://{}/{}".format(event['bucket'], event['name'])  # gs://bucket-name/object-path
        objects = localize_objects(uri)
        if len(objects) > 0:  # Store in datastore only if objects are localized.
            store_objects_in_datastore(uri, objects)
    else:
        logging.info("Invalid file content type")
