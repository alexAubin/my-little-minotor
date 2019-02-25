# My little Minotor

<img src="https://storage.opensea.io/0x71c118b00759b0851785642541ceb0f4ceea0bd5/13-1550172581.png" width="200" height="200" />

Brutally make sure that some remote services are up and running. 

Will send you an email if something's going wrong.


### Configuration example (yaml)

In `to_monitor.yml`

```yaml
ping:
    - some.domain.tld
    - other.domain.tld
https_200:
    - wikipedia.org
    - your.website.org
dns_resolver:
    # Your favorite DNS resolver which you want to check is up
    - 11.22.33.44
    - 66.77.88.99
free_dns_service:
    # Will test that a specific resolver correctly resolves a specific domain
    - [ 'your.resolver.org', 'some.somain.tld', '12.34.56.78' ]
```

### Cron

```cron
*/10 * * * * some_user cd /path/to/monitoring && python3 monitor.py
```

### Dependencies

- `python3-yaml`
- an SMTP server running on the machine
- currently there's a constrain on running on a yunohost server, could be easily removed
