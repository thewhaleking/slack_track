from collections import Counter
from datetime import datetime
import json
from time import sleep

import pandas as pd
import plotly.express as px
import plotly.graph_objs
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from slack_track import CONFIG


class User:
    def __init__(self, user: dict):
        self.active = not user["deleted"]
        self.updated = datetime.fromtimestamp(user["updated"]).date()
        self.name = user["name"]
        self.team = user.get("profile", {}).get("title", "")
        self.org = self.team.split("-")[0]
        self.bot = user.get("is_bot", True)
        iso = self.updated.isocalendar()
        self.updated_week = datetime.strptime(f"{iso[0]}-W{str(iso[1]).zfill(2)}-1", "%Y-W%W-%w")

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def deactivated_week(member):
    iso = member.updated.isocalendar()
    return datetime.strptime(f"{iso[0]}-W{str(iso[1]).zfill(2)}-1", "%Y-W%W-%w")


def get_all_users(cursor=None, members=None):
    if not members:
        members = []

    def retry():
        try:
            return web_client.users_list(cursor=cursor).data
        except SlackApiError:
            sleep(5)
            print('sleeping')
            return retry()

    init_data = retry()
    if init_data["response_metadata"]["next_cursor"]:
        return get_all_users(init_data["response_metadata"]["next_cursor"], members + init_data["members"])
    else:
        return members + init_data["members"]


web_client = WebClient(CONFIG["slack_token"])
data = get_all_users()
with open("users.json", "w+") as d:
    json.dump(data, d)
members = [User(user) for user in data]
current_members = [x for x in members if x.active and x.bot is False]
all_orgs = list(set(x.org for x in current_members if " " not in x.org and x.org))
deactivated_members = [x for x in members if not x.active and x.bot is False]
current_orgs = [sum(x.org == org for x in current_members) for org in all_orgs]
attrition_orgs = [sum(x.org == org for x in deactivated_members) for org in all_orgs]


# for member in sorted(deactivated_members, key=lambda x: x.updated):
#     print(member.name, member.updated)


def org_d() -> plotly.graph_objs.Figure:
    df = pd.DataFrame({"active": current_orgs, "deactivated": attrition_orgs, "name": all_orgs})
    df = df[(df.name.isin(["null", "no", "Jesspatch"]) == False) & (df.active > 1)]
    fig = px.bar(df, y=["active", "deactivated"], x="name")
    return fig


def weekly_d() -> plotly.graph_objs.Figure:
    weekly_deacs = Counter([deactivated_week(m) for m in deactivated_members])
    df = pd.DataFrame.from_dict(weekly_deacs, orient="index").reset_index()
    df.sort_values("index", inplace=True)
    fig = px.line(df, x="index", y=0)
    return fig


def weekly_and_org() -> plotly.graph_objs.Figure:
    weekly_deacs = [(x, Counter(m.updated_week for m in deactivated_members if m.org == x)) for x in all_orgs]
    d = [
        {
            "org": org, "date": date, "count": count
        } for (org, counter) in weekly_deacs for (date, count) in counter.items()
    ]
    df = pd.DataFrame.from_records(
        d + [
            {
                "org": "ALL", "date": date, "count": count
            } for (date, count) in Counter(
                m.updated_week for m in deactivated_members if m.org not in ["null", "no", "Jesspatch"]
                and m.updated_week > datetime(2021, 1, 1)
            ).items()
        ]
    )
    df.sort_values("date", inplace=True)
    df = df[(df.org.isin(["null", "no", "Jesspatch"]) == False)]
    fig = px.line(df, x='date', y='count', color='org', markers=True)
    return fig
