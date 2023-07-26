#!/usr/bin/env python3

import argparse
import hashlib
import json
import random
import re
import socket
from typing import Dict
from http.server import HTTPServer, SimpleHTTPRequestHandler
from tabulate import tabulate
import pandas as pd
from collections import defaultdict

NUM_SERVERS = 150
SERVER_SET = ['10.58.1.%d' % i for i in range(1, NUM_SERVERS + 1)]
IP_REGEX = r'/10\.58\.1\.[0-9]{1,3}$'
SERVICES = [
    'PermissionsService',
    'AuthService',
    'MLService',
    'StorageService',
    'TimeService',
    'GeoService',
    'TicketService',
    'RoleService',
    'IdService',
    'UserService',
    'RoleService',
]


def _server_stats(ip: str) -> Dict[str, str]:
    ip_u = ip.encode('utf-8')
    service_idx = int(hashlib.md5(ip_u).hexdigest(), 16) % len(SERVICES)
    service_name = SERVICES[service_idx]
    stats= {
        'ip': ip,
        'service': service_name,
        #'cpu': f'{random.randint(0, 100)}%',
        #'memory': f'{random.randint(0, 100)}%',
    }

    """if stats['cpu'] > '75%' or stats['memory'] > '75%':
        stats['status'] = 'Unhealthy'
        return stats

    stats['status'] = 'Healthy'
    """

    return stats


def _all_server_stats():
    all_stats = [_server_stats(server) for server in SERVER_SET]
    df = pd.DataFrame(all_stats)
    table = tabulate(df, headers='keys', tablefmt='psql')
    return table

def calculate_average_server_stats():
    all_stats = [_server_stats(server) for server in SERVER_SET]
    service_stats = defaultdict(list)

    # collect cpu and memory usage for each service
    for server in all_stats:
        service_name = server['service']
        cpu_usage = int(server['cpu'].rstrip('%'))
        memory_usage = int(server['memory'].rstrip('%'))
        service_stats[service_name].append((cpu_usage, memory_usage))

    # calculate the average for each service
    averages = []
    for service_name, stats in service_stats.items():
        cpu_average = sum([s[0] for s in stats]) / len(stats)
        memory_average = sum([s[1] for s in stats]) / len(stats)
        averages.append({'service': service_name, 'cpu_average': f'{cpu_average:.2f}%', 'memory_average': f'{memory_average:.2f}%' })

    df = pd.DataFrame(averages)
    table = tabulate(df, headers='keys', tablefmt='psql')
    return table


def services_with_few_health_instances():
    status_data = [_server_stats(server) for server in SERVER_SET]

    service_stats = {}
    for stat in status_data:
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

    return table


class HTTPServerV6(HTTPServer):
    address_family = socket.AF_INET6


class CPXHandler(SimpleHTTPRequestHandler):
    def _invalid_endpoint(self):
        self.send_response(400)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps({'error': 'Invalid IP'}), 'utf-8'))

    def _json(self, data: str):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(data), 'utf-8'))

    def do_GET(self):
        ip_match = re.match(IP_REGEX, self.path)
        if self.path == '/servers':
            self._json(SERVER_SET)
        elif self.path == '/status':
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(_all_server_stats(), 'utf-8'))
        elif self.path == '/services':
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(calculate_average_server_stats(), 'utf-8'))
        elif self.path == '/service-health':
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(services_with_few_health_instances(), 'utf-8'))
        elif ip_match:
            ip = ip_match.group().replace('/', '')
            if ip not in SERVER_SET:
                self._invalid_endpoint()
            else:
                self._json(_server_stats(ip))
        else:
            self._invalid_endpoint()


def main(port: int, protocol: int):
    if protocol == 6 and not socket.has_ipv6:
        print("Falling back to IPv4")

    if protocol == 6 and socket.has_ipv6:
        httpd = HTTPServerV6(('::', port), CPXHandler)
        httpd.serve_forever()

    else:
        httpd = HTTPServer(('0.0.0.0', port), CPXHandler)
        httpd.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="the port on which to run", type=int)
    parser.add_argument("--protocol", help="which IP version to use, 4 for IPv4, 6 for IPv6",
                        type=int, choices=[4, 6], default=6)
    args = parser.parse_args()
    main(args.port, args.protocol)