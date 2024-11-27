from client import  Client
from model import Dataset, Resource


stelar = Client("https://klms.stelar.gr/stelar",username="admin",password="stelartuc", version="v2")

resource1 = Resource("s3://path/path/foo1.txt","TXT","Resource 1")
resource2 = Resource("s3://path/path/foo2.txt","TXT","Resource 2")
resource3 = Resource("s3://path/path/foo3.txt","TXT","Resource 3")
resource4 = Resource("s3://path/path/foo4.txt","TXT","Resource 4")
resource5 = Resource("s3://path/path/foo5.txt","TXT","Resource 5")



dataset = stelar.catalog.get_dataset("339e01a1-8979-4b6b-bda9-0bd151bc69d0")

print(dataset)