def test_fetch_users(testcli):
    # Fetch all users via the API
    raw_users = testcli.GET("v1/users").json()["result"]

    # Fetch all users via the client
    users = testcli.users[::]

    # Check that the number of users is the same
    assert len(users) == len(raw_users)

    raw_user_names = {u["username"] for u in raw_users}
    user_names = {u.username for u in users}

    assert raw_user_names == user_names


def test_update_dummy_user_name(testcli):
    c = testcli
    du = c.users["dummy_user2"]

    assert du.first_name == "Foo"
    assert du.last_name == "Manchu"

    du.first_name = "Bar"
    assert du.first_name == "Bar"
    assert du.last_name == "Manchu"
    assert du.fullname == "Bar Manchu"

    du.first_name = "Foo"
    assert du.fullname == "Foo Manchu"


def test_update_dummy_user_email(testcli):
    c = testcli
    du = c.users["dummy_user2"]

    assert du.email == "dumb2@dumbville.com"
    assert du.email_verified is True

    du.email = "dumb_2@dumbville.com"
    assert du.email_verified is True

    du.email = "dumb2@dumbville.com"
    assert du.email_verified is True

    du.email_verified = False
    assert du.email_verified is False
    du.email_verified = True


def test_read_only_username(testcli):
    c = testcli
    du = c.users["dummy_user2"]

    assert du.username == "dummy_user2"


def test_read_roles(testcli):
    c = testcli
    roles = c.users.roles()

    assert all(r in roles for r in ["admin", "pushers", "pullers"])


def test_read_user_roles(testcli):
    c = testcli
    du = c.users["dummy_user2"]

    du.set_roles([])
    assert du.roles == ()
    assert len(du.roles) == 0

    du.add_role("pushers")

    assert du.roles == ("pushers",)
    assert len(du.roles) == 1

    du.set_roles(["pullers", "pushers"])

    assert set(du.roles) == set(("pullers", "pushers"))
    assert len(du.roles) == 2

    du.remove_role("pushers")
    assert du.roles == ("pullers",)
    assert len(du.roles) == 1
