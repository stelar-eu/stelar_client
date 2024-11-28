from client import  Client
from model import Dataset, Resource


stelar = Client("https://klms.stelar.gr/stelar",username="admin",password="stelartuc", version="v2")

resource1 = Resource("s3://path/path/foo1.txt","TXT","Resource 1")
resource2 = Resource("s3://path/path/foo2.txt","TXT","Resource 2")
resource3 = Resource("s3://path/path/foo3.txt","TXT","Resource 3")
resource4 = Resource("s3://path/path/foo4.txt","TXT","Resource 4")
resource5 = Resource("s3://path/path/foo5.txt","TXT","Resource 5")

resources = [resource1,resource2,resource3,resource4,resource5]



# new_dataset = Dataset("Nikolakis ananeomenos","Somes notes fore the Dataset",["STELAR","Testing"])
# stelar.catalog.create_dataset(new_dataset)

# for resource in resources:
#     stelar.catalog.publish_dataset_resource(new_dataset,resource)
# print(f"The new dataset is dirty: {new_dataset.is_dirty()}")

# new_dataset.title = "Ananeomenos Nikolakis"

# print(f"The new dataset is dirty: {new_dataset.is_dirty()}")
# stelar.catalog.create_dataset(new_dataset)


# print(f"ID is: {new_dataset.id}")

# print(stelar.catalog.get_dataset(new_dataset.id))

# dataset_object_list = stelar.catalog.get_datasets()

# for object in dataset_object_list:
#     print(object.id)
# print(json_print)

resources_object_list = stelar.catalog.get_dataset_resources("dimitris","profile")

for object in resources_object_list:
    print(object)
# print(json_print)