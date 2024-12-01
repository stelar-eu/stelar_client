from .model import Resource, STELARUnknownError
from .base import BaseAPI
from .endpoints import APIEndpointsV1
import stelar_client.mutils as s3
from requests import HTTPError
from minio.error import S3Error
import traceback


class S3API(BaseAPI):
    def download_resource(self, resource: Resource, localpath: str) -> bool:
        """
        Downloads an object from the S3 instance the KLMS is working with.
        The method fetches the URL pointed by the Resource object and tries to
        download the object into a local file. You need to make sure that have 
        the permission to access the object, otherwise

        Args:
            resource (Resource): A Resource object containing the S3 URL of the object.
            localpath (str): The path to store the file downloaded from MinIO.

        Returns:    
            True: File downloaded succesfully.
            False: Error occured. Possibly an exception will be raised.

        Raises: 
            STELARUnknownError (Exception): In case an error occured. 
        """
        try:    
            response = self.request("GET", APIEndpointsV1.S3_CREDENTIALS)
            if response.status_code == 200:
                credentials = response.json()['result']['creds']
                s3_url = credentials.get("S3Url")
                addr = resource.url.replace("s3://","")               
                resp = s3.init_client(s3_url,credentials.get("AccessKeyId"), credentials.get("SecretAccessKey"), stoken=credentials.get("SessionToken"))
                if "error" in resp:
                    raise STELARUnknownError(str(resp))
                resp = s3.get_object(addr, localpath)
                if "error" not in resp:
                    return True
                return False
        except (S3Error, HTTPError) as e:
            traceback.print_exc()
            raise STELARUnknownError(f"Error: {str(e)}")
        except Exception as e:
            traceback.print_exc()
            raise STELARUnknownError("An unexpected error occurred while retrieving object stats.")
    

    def stat_resource_file(self, resource: Resource):
        """
        Retrieves metadata for an object from the S3 instance the KLMS is working with.
        
        This method fetches the URL pointed by the Resource object and retrieves
        the object statistics such as size and other metadata.

        Arguments:
        resource -- A Resource object containing the S3 URL of the object.

        Returns:
        A dictionary containing object metadata, or None if an error occurs.
        """
        try:
            response = self.request("GET", APIEndpointsV1.S3_CREDENTIALS)
            if response.status_code == 200:
                credentials = response.json()['result']['creds']
                s3_url = credentials.get("S3Url")
                addr = resource.url.replace("s3://", "")
                s3.init_client(
                    s3_url,
                    credentials.get("AccessKeyId"),
                    credentials.get("SecretAccessKey"),
                    stoken=credentials.get("SessionToken")
                )
                stat_response = s3.stat_object(addr)
                if "error" not in stat_response:
                    return stat_response
                else:
                    raise S3Error(f"Error retrieving object stats: {stat_response['message']}")
        except (S3Error, HTTPError) as e:
            traceback.print_exc()
            raise STELARUnknownError(f"Error: {str(e)}")
        except Exception as e:
            traceback.print_exc()
            raise STELARUnknownError("An unexpected error occurred while retrieving object stats.")
    

    def stat_resource_file(self, resource: Resource):
        """
        Retrieves metadata for an object from the S3 instance the KLMS is working with.
        
        This method fetches the URL pointed by the Resource object and retrieves
        the object statistics such as size and other metadata.

        Arguments:
        resource -- A Resource object containing the S3 URL of the object.

        Returns:
        A dictionary containing object metadata, or None if an error occurs.
        """
        try:
            response = self.request("GET", APIEndpointsV1.S3_CREDENTIALS)
            if response.status_code == 200:
                credentials = response.json()['result']['creds']
                s3_url = credentials.get("S3Url")
                addr = resource.url.replace("s3://", "")
                s3.init_client(
                    s3_url,
                    credentials.get("AccessKeyId"),
                    credentials.get("SecretAccessKey"),
                    stoken=credentials.get("SessionToken")
                )
                stat_response = s3.stat_object(addr)
                if "error" not in stat_response:
                    return stat_response
                else:
                    raise S3Error(f"Error retrieving object stats: {stat_response['message']}")
        except (S3Error, HTTPError) as e:
            traceback.print_exc()
            raise STELARUnknownError(f"Error: {str(e)}")
        except Exception as e:
            traceback.print_exc()
            raise STELARUnknownError("An unexpected error occurred while retrieving object stats.")

    def stream_resource(self, resource: Resource, chunk_size: int = 32 * 1024):
        """
        Context manager for streaming an object from the S3 instance in chunks.
        
        Args:
            resource (Resource): A Resource object containing the S3 URL of the object.
            chunk_size (int): Size of each chunk to stream, default is 32KB.

        Yields:
            Stream of bytes in the form of chunks.
        """
        try:
            response = self.request("GET", APIEndpointsV1.S3_CREDENTIALS)
            if response.status_code == 200:
                credentials = response.json()['result']['creds']
                s3_url = credentials.get("S3Url")
                addr = resource.url.replace("s3://", "")
                s3.init_client(
                    s3_url,
                    credentials.get("AccessKeyId"),
                    credentials.get("SecretAccessKey"),
                    stoken=credentials.get("SessionToken")
                )
                
                # Create a generator for streaming
                generator = s3.stream_object(addr, chunk_size=chunk_size)
                
                # Context management for proper cleanup
                class StreamContext:
                    def __enter__(self):
                        return generator

                    def __exit__(self, exc_type, exc_val, exc_tb):
                        try:
                            generator.close()
                        except Exception:
                            pass

                return StreamContext()
        except (S3Error, HTTPError) as e:
            traceback.print_exc()
            raise STELARUnknownError(f"Error: {str(e)}")
        except Exception as e:
            traceback.print_exc()
            raise STELARUnknownError("An unexpected error occurred while streaming the object.")