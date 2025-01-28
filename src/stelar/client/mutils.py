"""

Author: Petrou Dimitrios 
Organization: Athena Research Center
Project Name:  STELAR EU 
Project Info: https://stelar-project.eu/

"""

from minio import Minio
import traceback
from minio.error import S3Error, InvalidResponseError
import traceback
import os


mclient: Minio = None

def init_client(minio_url: str, access_id: str, secret_key: str, stoken: str = None):
    """
    Instantiates and initializes a MinIO client with the given credentials and attributes.
    Args:
        minio_url (str): The URL for the MinIO server.
        access_id (str): Access key ID for MinIO.
        secret_key (str): Secret key for MinIO.
        stoken (str, optional): Session token, if required.
        secure (bool, optional): Whether to use HTTPS. Default is True.
    Returns:
        Minio: A MinIO client instance, or an error dictionary if initialization fails.
    """
    global mclient
    sanitized_url = minio_url.replace("http://", "").replace("https://", "")
    try:
        mclient = Minio(sanitized_url, access_key=access_id, secret_key=secret_key, session_token=stoken, secure=True)
        return mclient
    except Exception as e:
        return {
            "error": "Could not initialize MinIO client",
            "message": str(e)
        }
    
def put_object(object_path: str, file_path: str):
    """
    Uploads an object to the specified bucket using a combined object path.
    Args:
        object_path (str): The full path to the bucket and object in the format "bucket_name/object_name".
        file_path (str): Path to the local file to be uploaded.
        mclient (Minio): The Minio client
    Returns:
        dict: A success message or an error dictionary if upload fails.
    """
    global mclient
    if not mclient:
        return {"error": "MinIO client is not initialized."}

    try:
        if not os.path.isfile(file_path):
            return {"error": f"The specified file does not exist: {file_path}"}
        
        # Split object_path into bucket and object name
        bucket_name, object_name = object_path.split('/', 1)
        file_stat = os.stat(file_path)
        with open(file_path, 'rb') as file_data:
            mclient.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_stat.st_size
            )
        return {"message": f"Object '{object_name}' successfully uploaded to bucket '{bucket_name}'."}

    except (S3Error, InvalidResponseError) as e:
        return {
            "error": "Could not upload the object to MinIO",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    except Exception as e:
        return {
            "error": "An unexpected error occurred while uploading the object",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    


def get_object(object_path: str, file_path: str):
    """
    Downloads an object from the specified bucket using a combined object path.
    Args:
        object_path (str): The full path to the bucket and object in the format "bucket_name/object_name".
        file_path (str): The local path where the downloaded object should be saved.
    Returns:
        dict: A success message or an error dictionary if download fails.
    """
    if not mclient:
        return {"error": "MinIO client is not initialized."}

    try:
        # Split object_path into bucket and object name
        bucket_name, object_name = object_path.split('/', 1)
   
        response = mclient.get_object(bucket_name, object_name)
        with open(file_path, 'wb') as file_data:
            for d in response.stream(32 * 1024):
                file_data.write(d)
        response.close()
        response.release_conn()
        
        return {"message": f"Object '{object_name}' successfully downloaded from bucket '{bucket_name}' to '{file_path}'."}

    except (S3Error, InvalidResponseError) as e:
        return {
            "error": "Could not download the object from MinIO",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    except Exception as e:
        return {
            "error": "An unexpected error occurred while downloading the object",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


def stream_object(object_path: str, chunk_size: int = 32 * 1024):
    """
    Streams an object from MinIO in chunks.
    Args:
        object_path (str): The full path to the bucket and object in the format "bucket_name/object_name".
        chunk_size (int): Size of each chunk to read, default is 32KB.
    Yields:
        bytes: A chunk of the object's data.
    """
    if not mclient:
        return {"error": "MinIO client is not initialized."}

    try:
        bucket_name, object_name = object_path.split('/', 1)
        response = mclient.get_object(bucket_name, object_name)
        for chunk in response.stream(chunk_size):
            yield chunk
        response.close()
        response.release_conn()
    except (S3Error, InvalidResponseError) as e:
        yield {
            "error": "Could not stream the object from MinIO",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    except Exception as e:
        yield {
            "error": "An unexpected error occurred while streaming the object",
            "message": str(e),
            "traceback": traceback.format_exc()  
        }
    
    
def stat_object(object_path: str):
    """
    Retrieves metadata of an object from MinIO, such as size and other attributes.
    Args:
        object_path (str): The full path to the bucket and object in the format "bucket_name/object_name".
    Returns:
        dict: Metadata of the object or an error dictionary if the operation fails.
    """
    if not mclient:
        return {"error": "MinIO client is not initialized."}

    try:
        bucket_name, object_name = object_path.split('/', 1)
        stat = mclient.stat_object(bucket_name, object_name)
        return {
            "bucket_name": bucket_name,
            "object_name": object_name,
            "size": stat.size,
            "etag": stat.etag,
            "last_modified": stat.last_modified,
            "content_type": stat.content_type,
        }
    except (S3Error, InvalidResponseError) as e:
        return {
            "error": "Could not retrieve object stats from MinIO",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    except Exception as e:
        return {
            "error": "An unexpected error occurred while retrieving object stats",
            "message": str(e),
            "traceback": traceback.format_exc()
        }