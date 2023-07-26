import click
import requests
import pandas as pd
import random
import time
from tabulate import tabulate


@click.group()
def cli():
    pass


def retry(max_attempts=3, wait_seconds=5):
    """
    :param max_attempts:
    :param wait_seconds:
    :return:
    retry operation with a decorator implemented so that the retry operation can be referenced with ease.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 1
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    click.echo(f"Attempt {attempt}/{max_attempts} failed with error: {e}")
                    attempt += 1
                    time.sleep(wait_seconds)
            click.echo(f"Function failed after {max_attempts} attempts.")
            return None
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


@cli.command()
@click.option('--port', type=int, default=80)
@retry()
def get_status(port):
    """
    retrieve the details of all servers
    :param port:
    :return:
    """
    servers = requests.get(f'http://0.0.0.0:{port}/servers').json()
    status = []
    for server in servers:
        server = requests.get(f'http://0.0.0.0:{port}/{server}').json()
        status.append(server)

    df = pd.DataFrame(status)
    table = tabulate(df, headers='keys', tablefmt='psql')
    click.echo(table)

    return status


@cli.command()
@click.option('--port', type=int, default=80)
@retry()
def unhealthy_status(port):
    """
    retrieve all servers with unhealthy status
    :param port:
    :return:
    """
    servers = requests.get(f'http://0.0.0.0:{port}/servers').json()
    status = []
    for server in servers:
        server = requests.get(f'http://0.0.0.0:{port}/{server}').json()
        server['cpu'] = f'{random.randint(0, 100)}%'
        server['memory'] = f'{random.randint(0, 100)}%'
        status.append(server)

    click.echo(status)
    service_stats = {}

    for stat in status:
        if stat['status'] == 'Unhealthy':
            continue
        service_name = stat['service']
        if service_name not in service_stats:
            service_stats[service_name] = []
        service_stats[service_name].append(stat['ip'])

    services_with_few_health = {}

    for service_name, ips in service_stats.items():
        healthy_instances = len(ips)
        if healthy_instances <= 2:
            services_with_few_health[service_name] = ips

    df = pd.DataFrame(services_with_few_health)
    table = tabulate(df, headers='keys', tablefmt='psql')

    click.echo(table)


@cli.command()
@click.option('--port', type=int, default=80)
@click.option('--interval', type=int, default=5)
@retry()
def current_status(port, interval):
    while True:
        servers = requests.get(f'http://0.0.0.0:{port}/servers').json()
        status = []
        for server in servers:
            server_status = requests.get(f'http://0.0.0.0:{port}/{server}').json()
            status.append(server_status)

        df = pd.DataFrame(status)
        table = tabulate(df, headers='keys', tablefmt='psql')
        click.clear()
        click.echo(table)

        time.sleep(interval)


if __name__ == '__main__':
    cli()
