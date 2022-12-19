import json
import os
from collections import OrderedDict
from unittest.mock import MagicMock


def create_mock_org_client():
    d = os.path.realpath(os.path.dirname(__file__))
    d = os.path.join(d, "data/test_data.json")
    with open(d, "r") as file:
        test_data = json.load(file)

    def create_data_func(data_type, data_id_loc):
        def func(*args, **kwargs):
            if data_id_loc:
                if args:
                    data_id = str(args[data_id_loc[0]])
                elif kwargs:
                    data_id = str(kwargs[data_id_loc[1]])
                return test_data[data_type][data_id]
            return test_data[data_type]
        return func

    mock_org_client = MagicMock()
    mock_org_client.get_projects = create_data_func(
        data_type="projects", data_id_loc=None
    )
    mock_org_client.get_project_activity = create_data_func(
        data_type="project_activity", data_id_loc=(0, "project_id")
    )
    return mock_org_client


def build_employee_project_stats_data_struct(hs_org, s, e, emp_ref, proj_ref):
    def create_user_dict(data):
        d = {}
        for item in data:
            d[item["id"]] = {"email": item["email"], "name": item["name"]}
        return d

    ds = OrderedDict()
    user_info_dict = {}
    projects = []
    users = []
    i = 0
    for project_page in iter(hs_org.get_projects()):
        for project in project_page["projects"]:
            d = {}
            for activity_page in iter(
                hs_org.get_project_activity(
                    project["id"], s, e, additional_params={"include": "users"}
                )
            ):
                user_info_dict = create_user_dict(activity_page["users"])
                for activity in activity_page["daily_activities"]:
                    user_id = activity["user_id"]
                    tracked = activity["tracked"]
                    d[user_id] = d.setdefault(user_id, 0) + tracked
            if d:
                for k, v in ds.items():
                    if k not in d:
                        ds[k].append(0)
                    else:
                        ds[k].append(d.pop(k))
                for k, v in d.items():
                    ds[k] = [0] * i + [v]
                    users.append(user_info_dict[k].get(emp_ref, k))
                i += 1
                projects.append(project[proj_ref])
    return ds, projects, users
