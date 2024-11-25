from client import  Client


# Init a stelar client
stelar = Client('https://klms.stelar.gr/stelar',username='admin',password='stelartuc')

dpetrou = stelar.admin.get_user_by_id("dpetrou")

for user in stelar.admin.get_users():
    print(f"User ID: {user['id']} | Name: {user['fullname']} | Username: {user['username']}")