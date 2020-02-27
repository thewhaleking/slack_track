import datetime
import os
import sqlite3
from textwrap import dedent
from typing import Iterable, Iterator, Tuple


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class DatabaseTools:
    def __init__(self, db_name, column_names):
        self.con = sqlite3.connect(os.path.join(FILE_PATH, db_name), check_same_thread=False)
        self.con.isolation_level = None
        self.cursor = self.con.cursor()
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS Slack {column_names}")
        self.con.commit()

    def get_table_column_names(self, table: str) -> list:
        self.cursor.execute(f"PRAGMA table_info({table});")
        return [x[1] for x in self.cursor]

    def get_only_valid_col_names(self, table: str, col_names: Iterable[str]) -> Iterator[str]:
        """
        Compares a group of column names against valid column names for that table as produced from the the
        SQLite PRAGMA table_info function for the specified table.
        :param table: The name of the table for which to check the column names.
        :param col_names: An iterable (list, set, tuple, etc.) from which you would like to check the validity against
                          the table's column names.
        :return: Filter for all of the matches.
        """
        table_cols = self.get_table_column_names(table)
        return filter(lambda x: x in table_cols, col_names)

    def get_data_from_previous_run(self, *attrs) -> Iterator:
        """
        Retrieves the table data for the previous run from the db.
        :param attrs: The column name(s) to retrieve the data for (e.g. "name", "deleted", etc.). If not attrs are
                      specified, pulls all columns with "*".
        :return: Iterator of the sqlite cursor.
        """
        today = datetime.date.today()
        self.cursor.execute("SELECT DISTINCT date FROM Slack WHERE date != ?", (today,))
        sorted_dates = sorted(x[0] for x in self.cursor)
        if not sorted_dates:
            raise ValueError("Does not appear to have an data from a previous time.")
        else:
            selection = "*" if not attrs else ",".join(self.get_only_valid_col_names("Slack", attrs))
            if not selection:
                raise ValueError("No valid column names specified. To get all columns, leave argument empty")
            else:
                self.cursor.execute(f"SELECT {selection} FROM Slack WHERE date = ?", (sorted_dates[-1],))
                return (x for x in self.cursor)

    def compare_current_and_previous_datasets(self, *attrs) -> Tuple[set, set]:
        """
        Compares the previous two runs (where the most recent is usually the "current" run) of the script. Does the
        comparison by utilizing the set.differences of the two. This works well when comparing a few attributes, such as
        name and deleted, but doesn't work well when comparing all columns.
        :param attrs: The column names to compare between the two runs (e.g. "name", "deleted", etc.). If no attrs are
                      specified, pulls all columns with "*".
        :return: Tuple of the set differences, with 0 being difference between current and previous, and 1 being
                 difference between previous and current. See: set.difference() documentation for an explanation.
        """
        selection = "*" if not attrs else ",".join(self.get_only_valid_col_names("Slack", attrs))
        self.cursor.execute(f"SELECT {selection} FROM Slack WHERE date = ?", (datetime.date.today(),))
        todays_data = set(self.cursor)
        previous_data = set(self.get_data_from_previous_run(*attrs))
        return (
            todays_data.difference(previous_data),
            previous_data.difference(todays_data),
        )

    def get_users_created_and_deleted_since_last_run(self) -> str:
        """
        Mainly just a demo function. Outputs a string with three groups: new users, users whose accounts have been
        deactivated since the last run, and users whose accounts have been reactivated since the last run.
        """
        first_group, second_group = self.compare_current_and_previous_datasets("name", "deleted")
        fg_dict = {x[0]: x[1] for x in first_group}
        sg_dict = {x[0]: x[1] for x in second_group}
        first_group_users = set(fg_dict.keys())
        second_group_users = set(sg_dict.keys())
        new_users = first_group_users.difference(second_group_users)
        changed_status_users = second_group_users.difference(new_users)
        reactivated_users = {x for x in changed_status_users if sg_dict[x] == 1}
        deleted_users = {x for x in changed_status_users if sg_dict[x] == 0}
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
                    new_users,
                    deleted_users,
                    reactivated_users)
                ))
        return output
