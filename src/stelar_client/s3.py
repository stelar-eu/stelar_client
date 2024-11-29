from model import Resource, STELARUnknownError
from base import BaseAPI
from endpoints import APIEndpointsV1
import mutils as s3
from requests import HTTPError



class S3API(BaseAPI):
    def store_file_from_s3(self, resource: Resource, localpath: str):
        try:    
            response = self.request("GET", APIEndpointsV1.S3_CREDENTIALS)
            if response.status_code == 200:
                credentials = response.json()['result']['creds']
                s3_url = credentials.get("S3Url")
                addr = resource.url.replace("s3://","")               
                s3.init_client(s3_url,credentials.get("AccessKeyId"), credentials.get("SecretAccessKey"), stoken=credentials.get("SessionToken"))
                s3.get_object(addr, localpath)
                return s3_url + "/" + addr
        except HTTPError as he:
            raise STELARUnknownError("STELAR unknown Error")