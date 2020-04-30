"""
Edit this file with whatever reports you would like to run each time the main slack_track.py file runs.
The reports.main function will be executed by slack_track's main function.
The reports.main function takes a DatabaseTools object as an argument, so can be directly interacted with, rather
than having to construct a second object to use to run reports.

The functions in here (besides main) are purely for demonstration purposes. They might work perfectly fine with
your Slack instance, or they might not work at all. They're here simply as guidelines to craft your own reports, and
thus should only be used as building blocks.
"""
from datetime import date
from textwrap import dedent

from utils.database_tools import DatabaseTools


def match_other_columns(db: DatabaseTools, column_data, column_name: str, *column_attrs):
    """
    Gets other columns matching a given datum for a column. Essentially used to get other info on a user, based on
    a specific match.
    Example: match_other_columns(db, "bhimes", "name", "real_name", "title") might produce
             [("Benjamin Himes", "Autonomy Hardware Engineer")]
    """
    q = ", ".join(column_attrs)
    db.cursor.execute(f"SELECT DISTINCT {q} FROM Slack WHERE {column_name} = ?",
                      (column_data,))
    return [x for x in db.cursor]


def get_users_created_and_deleted_since_last_run(db: DatabaseTools) -> str:
    """
    Outputs a string with three groups: new users, users whose accounts have been deactivated since the
    last run, and users whose accounts have been reactivated since the last run.
    """
    first_group, second_group = db.compare_current_and_previous_datasets("name", "deleted")
    fg_dict = {x[0]: x[1] for x in first_group}
    sg_dict = {x[0]: x[1] for x in second_group}
    first_group_users = set(fg_dict.keys())
    second_group_users = set(sg_dict.keys())
    new_users = first_group_users.difference(second_group_users)
    changed_status_users = second_group_users.difference(new_users)
    reactivated_users = {x for x in changed_status_users if sg_dict[x] == 1}
    deleted_users = {x for x in changed_status_users if sg_dict[x] == 0}

    def format_cols(name: str):
        # for demonstration purposes only, your Slack instance might have different field names here
        cols = match_other_columns(db, name, "name", "name", "real_name", "title")
        return map(lambda x: " | ".join(x), cols)

    output = dedent(
        """
        New Users:
        {}


        Deleted Users
        {}


        Reactivated Users:
        {}
        """
    ).format(*map(lambda x: "\n".join(x), (
        *map(format_cols, new_users),
        *map(format_cols, deleted_users),
        *map(format_cols, reactivated_users))
                  ))
    return output


def write_reports():
    with open("reports.txt", "a+") as reports_file:
        reports_file.write(f"{date.today()} Report:\n")
        users = get_users_created_and_deleted_since_last_run(db)
        reports_file.write(users)
        reports_file.write("\n\n")


def main(db: DatabaseTools):
    write_reports()
