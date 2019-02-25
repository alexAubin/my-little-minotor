#!/usr/bin/python3

import os
import requests
from subprocess import Popen, PIPE
import json
import yaml
import smtplib

FAILURE_FILE = "/tmp/monitor-failures.json"

if "search" in open("/etc/resolv.conf").read():
    print("Having a 'sarch' entry in /etc/resolv.conf mades DNS resoluton unreliable")
if not os.path.exists("/etc/yunohost"):
    print("This is not a YunoHost server. No mail will actually be sent.")
    server = "localhost"
else:
    server = open("/etc/yunohost/current_host").read().strip()
send_alert_from = "monitor@" + server
send_alert_to = "root@" + server

# FIXME : should do the checks both in ipv4 and ipv6


def main():

    # Assert that we're connected to internet... Finish silently if not
    # (might change to non-silent if deployed to an actual server)
    if check_ping("wikipedia.org") is not None:
        return

    failures = monitor()
    failures_report = save_failures(failures)
    alert_if_needed(failures_report)


def monitor():

    to_monitor = yaml.load(open("to_monitor.yml"))

    failures = {"ping": (check_ping(url) for url in to_monitor["ping"]),
                "https_200": (check_https_200(url) for url in to_monitor["https_200"]),
                "dns_resolver": (check_dns_resolver(resolver) for resolver in to_monitor["dns_resolver"]),
                "free_dns_service": (check_free_dns_service(*infos) for infos in to_monitor["free_dns_service"])
    }

    failures = {k: (e for e in gen if e is not None) for k, gen in failures.items()}

    return failures


def save_failures(failures):

    if os.path.exists(FAILURE_FILE):
        existing_failures = json.loads(open(FAILURE_FILE).read())
    else:
        existing_failures = {}

    updated_failures = {k: {} for k in failures.keys()}

    for category, reports in failures.items():
        for target, message in reports:
            existing_failure = existing_failures.get(category, {}).get(target, {})
            count = existing_failure.get("count", 0) + 1
            messages = existing_failure.get("messages")
            messages = set(messages) if messages else set()
            messages.add(message)
            updated_failures[category][target] = {
                "count": count,
                "messages": list(messages)
            }

    with open(FAILURE_FILE, "w") as f:
        json.dump(updated_failures, f)

    return updated_failures


def alert_if_needed(failures):

    for category, reports in failures.items():
        alerts = [r for r in reports.items() if r[1]["count"] % 3 == 0]
        for target, infos in alerts:

            subject = "[monitoring] Check %s for %s is failing" % (category, target)
            body = target + " :\n" + "\n".join(infos["messages"])

            if not os.path.exists("/etc/yunohost"):
                print(message)
                continue
            
            open("/tmp/monitoring-body", "w").write(body)
            os.system("mail -s '%s' %s < /tmp/monitoring-body" % (subject, send_alert_to))


def check_https_200(url):

    try:
        r = requests.get("https://" + url, timeout=15)
    except Exception as e:
        return (url, str(e))
    if r.status_code != 200:
        return (url, "returns %s" % r.status_code)
    else:
        return None


def check_ping(hostname):

    it_pings = any(os.system("ping -c 1 -w 500 %s >/dev/null 2>&1" % hostname) == 0
                   for retry in range(3))
    return None if it_pings else (hostname, "does not answer pings")


def check_dns_resolver(resolver):
    cmd = "dig +short @%s wikipedia.org" % resolver
    p = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    if p.returncode == 0:
        return None
    else:
        err = out.decode("utf-8").strip() + err.decode("utf-8").strip()
        return (resolver, "does not seem to resolve domain names properly : %s"
                % err)


def check_free_dns_service(resolver, hostname, expected_result):
    cmd = "dig +short @%s %s" % (resolver, hostname)
    p = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    out = out.decode("utf-8").strip()
    if out == expected_result:
        return None
    else:
        if p.returncode == 0:
            return (resolver, "does not seem to resolve %s to %s" % (hostname, expected_result))
        else:
            err = out + err.decode("utf-8").strip()
            return (resolver, "does not seem to work properly : %s" % err)


main()
