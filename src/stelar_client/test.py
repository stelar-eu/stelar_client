from client import  Client
from model import Dataset, Resource


stelar = Client("https://klms.stelar.gr/stelar",username="admin",password="stelartuc", version="v2")

resource1 = Resource("s3://path/path/foo1.txt","TXT","Resource 1")
resource2 = Resource("s3://path/path/foo2.txt","TXT","Resource 2")
resource3 = Resource("s3://path/path/foo3.txt","TXT","Resource 3")
resource4 = Resource("s3://path/path/foo4.txt","TXT","Resource 4")
resource5 = Resource("s3://path/path/foo5.txt","TXT","Resource 5")

resources = [resource1,resource2,resource3,resource4,resource5]


resource_obj = stelar.catalog.get_resource("af6b1ad0-4daf-4c10-9d07-59b93d8d0915")
print(f"The resource is dirty: {resource_obj.is_dirty()}")

resource_obj.url = "s3://path/path/fooUpdated.pdf"
resource_obj.format = "PDF"
resource_obj.name = "Resource 2 updated"

print(f"The resource is dirty: {resource_obj.is_dirty()}")

stelar.catalog.patch_resource(resource_obj)

print(resource_obj.name)

# new_dataset = Dataset("STELAR dataset non dirty 6","Somes notes fore the Dataset",["STELAR","Testing"])
# stelar.catalog.create_dataset(new_dataset)

# for resource in resources:
#     stelar.catalog.publish_dataset_resource(new_dataset,resource)
# print(f"The new dataset is dirty: {new_dataset.is_dirty()}")

# new_dataset.title = "STELAR dataset dirty"
# new_dataset.notes = "added notes,dirty af"
# new_dataset.tags = ["STELAR","Testing","VeryDIRTY"]

# print(f"The new dataset is dirty: {new_dataset.is_dirty()}")
# # print(new_dataset.changes())

# stelar.catalog.patch_datasets(new_dataset)

# json_obj = {"package_metadata":{}}
# for key,value in new_dataset.changes().items():
#     json_obj['package_metadata'][key] = value[1]

# print(json_obj)



# stelar.catalog.create_dataset(new_dataset)


# print(f"ID is: {new_dataset.id}")

# print(stelar.catalog.get_dataset(new_dataset.id))

# dataset_object_list = stelar.catalog.get_datasets()

# for object in dataset_object_list:
#     print(object.id)
# print(json_print)

# resources_object_list = stelar.catalog.get_dataset_resources("dimitris","profile")

# for object in resources_object_list:
#     print(object)

# deleted_dataset = stelar.catalog.delete_dataset("test_data_api_123123")

# resource_obj = stelar.catalog.get_resource("88d67200-f518-4458-a6c3-fc4f2b38bb2b")

# print(resource_obj.modified_date)

# resource_is_deleted = stelar.catalog.delete_resource("88d67200-f518-4458-a6c3-fc4f2b38bb2b")
# print(resource_is_deleted)