from .client import  Client
from .model import Dataset, Resource, Policy
import yaml


stelar = Client("https://klms.stelar.gr/stelar",username="admin",password="stelartuc")

resource1 = Resource("s3://path/path/foo1.txt","TXT","Resource 1")
resource2 = Resource("s3://path/path/foo2.txt","TXT","Resource 2")
resource3 = Resource("s3://path/path/foo3.txt","TXT","Resource 3")
resource4 = Resource("s3://path/path/foo4.txt","TXT","Resource 4")
resource5 = Resource("s3://path/path/foo5.txt","TXT","Resource 5")

resources = [resource1,resource2,resource3,resource4,resource5]

# resource_obj = stelar.catalog.get_resource("af6b1ad0-4daf-4c10-9d07-59b93d8d0915")
# print(f"The resource is dirty: {resource_obj.is_dirty()}")

# resource_obj.url = "s3://path/path/fooUpdated.pdf"
# resource_obj.format = "PDF"
# resource_obj.name = "Resource 2 updated"

# print(f"The resource is dirty: {resource_obj.is_dirty()}")

# stelar.catalog.patch_resource(resource_obj)

# print(resource_obj.name)

new_dataset = Dataset("STELAR dataset non dirty 6","Somes notes fore the Dataset",["STELAR","Testing"])
stelar.catalog.create_dataset(new_dataset)

# for resource in resources:
#     stelar.catalog.publish_dataset_resource(new_dataset,resource)
# print(f"The new dataset is dirty: {new_dataset.is_dirty()}")

new_dataset.title = "STELAR dataset dirty"
new_dataset.notes = "added notes,dirty af"
new_dataset.tags = ["STELAR","Testing","VeryDIRTY"]

# print(f"The new dataset is dirty: {new_dataset.is_dirty()}")
# # print(new_dataset.changes())

stelar.catalog.patch_datasets(new_dataset)

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




#########################################################
################### POLICY TESTING ######################
#########################################################

# Test for policy listing
# policy_list = stelar.admin.get_policy_list()
# for item in policy_list:
#     print(item)

# Get policy info
# policy_obj = stelar.admin.get_policy_info("active")
# print(policy_obj.policy_uuid)
# print(yaml.dump(policy_obj.policy_content,default_flow_style=False,default_style='"'))
# print(policy_obj.policy_familiar_name)


# Get policy representation
# stelar.admin.get_policy_representation("active")


# Create policy object and then call create policy method
yaml_string = """
roles:
  - name: "chief_operations_officer"
    permissions:
      - action: "read,write"
        resource: "operations/*"
      - action: "read,write"
        resource: "training/materials/*"
  - name: "training_manager"
    permissions:
      - action: "read,write"
        resource: "training/*"
      - action: "read"
        resource: "operations/reports/*"
  - name: "finance_manager"
    permissions:
      - action: "read,write"
        resource: "finance/*"
      - action: "read"
        resource: "operations/plans/*"
      - action: "read"
        resource: "operations/logs/*"
  - name: "logistics_coordinator"
    permissions:
      - action: "read,write"
        resource: "operations/plans/*"
      - action: "read"
        resource: "operations/reports/daily/*"
      - action: "write"
        resource: "operations/logs/*"
  - name: "intern"
    permissions:
      - action: "read,write"
        resource: "training/materials/*"
      - action: "read"
        resource: "finance/expenses/Q1/*"
"""
# policy_obj = Policy("My new Policy 2",yaml_string)
policy_obj_2 = Policy("My updated Policy","/home/nibakats/Downloads/final_project-20240930T174310Z-001/final_project/finance_model_v2.yaml")

# stelar.admin.create_policy(policy_obj)
stelar.admin.create_policy(policy_obj_2)

print(policy_obj_2.policy_familiar_name)
print(policy_obj_2.policy_content)
print(policy_obj_2.policy_uuid)

# yaml_repr = yaml.dump(policy_obj.policy_content)
# print(yaml_repr)
# print(type(yaml_repr))