import logging
import math

import click
import pandas as pd
import pendulum

from src.hubstaff import HubstaffOrgClient
from src.util import create_mock_org_client, build_employee_project_stats_data_struct

logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s')
logger = logging.getLogger(__name__)


def validate_date(ctx, param, value):
    if value is None:
        return pendulum.yesterday()
    try:
        value = pendulum.from_format(str(value), "DD-MM-YYYY")
    except ValueError as e:
        raise click.BadParameter(f"Date format incorrect: {e}")
    else:
        return value


@click.group()
def cli():
    pass


@cli.command(
    help="Generate a table that displays how much time an employee worked on each project for a specific day"
)
@click.option(
    "-debug",
    help="Turn debug logging on",
    is_flag=True,
    default=False)
@click.option(
    "-test",
    help="Test mode. Will use static test data to generate table",
    is_flag=True,
    default=False,
)
@click.option(
    "-config",
    help="Path to config file",
    default=None)
@click.option(
    "-unit",
    help="Unit of time to use for table (rounds down to nearest integer)",
    default="seconds",
    type=click.Choice(["seconds", "minutes", "hours", "days"]),
    show_default=True
)
@click.option(
    "-date",
    help="Set a single date (24 hour period) for the table's time frame. Format: DD-MM-YYYY. Default is yesterday.",
    callback=validate_date,
    default=None,
)
@click.option(
    "-emp_ref",
    help="What type of reference to use for employees in the table",
    default="name",
    type=click.Choice(["id", "name", "email"]),
    show_default=True
)
@click.option(
    "-proj_ref",
    help="What type of reference to use for projects in the table",
    default="name",
    type=click.Choice(["id", "name"]),
    show_default=True
)
@click.option(
    "-format",
    help="The output format of the table",
    default="html",
    type=click.Choice(["html"]),
    show_default=True
)
def table(debug, test, config, unit, date, emp_ref, proj_ref, format):
    if debug:
        logger.setLevel(logging.DEBUG)
    if test:
        hs_org = create_mock_org_client()
    else:
        hs_org = HubstaffOrgClient(conf_path=config)
    start = date.start_of("day").to_iso8601_string()
    end = date.end_of("day").to_iso8601_string()
    logger.info(f"time frame: {start} - {end}")
    table_ds, projects, users = build_employee_project_stats_data_struct(hs_org, start, end, emp_ref, proj_ref)
    if format == 'html':
        df = pd.DataFrame(data=table_ds)
        df.index = projects
        df.columns = users
        df = df.applymap(lambda x: math.floor(getattr(pendulum.duration(seconds=x), f"total_{unit}")()))
        print(df.to_html())
    # elif format == 'email':
    #     ...


if __name__ == '__main__':
    cli()
