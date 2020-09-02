import traceback

import requests
from fauxfactory import gen_mac
from fauxfactory import gen_string
from nailgun import entities

fdqn = ''

# from nailgun.config import ServerConfig
# auth=('', '')
# server_config = ServerConfig(auth=auth, url=fdqn, verify=False).save()
# exit()


try:
    # Get default location, organization, for discovery from settings
    # This is used in cleanup to restore the prior settings of satellite
    prior_discovery_auto = entities.Setting().search(query={'search': 'name="discovery_auto"'})[0]
    prior_discovery_loc = entities.Setting().search(query={'search': 'name="discovery_location"'})[
        0
    ]
    prior_discovery_org = entities.Setting().search(
        query={'search': 'name="discovery_organization"'}
    )[0]

    # Here use fixture
    org = entities.Organization(name="org1").create()
    loc = entities.Location(name="loc1").create()

    discovery_auto_settings_id = (
        entities.Setting().search(query={'search': 'name="discovery_auto"'})[0].id
    )
    discovery_loc_settings_id = (
        entities.Setting().search(query={'search': 'name="discovery_location"'})[0].id
    )
    discovery_org_settings_id = (
        entities.Setting().search(query={'search': 'name="discovery_organization"'})[0].id
    )

    entities.Setting(id=discovery_auto_settings_id, value=True).update(fields=['value'])
    entities.Setting(id=discovery_org_settings_id, value=org.read().name).update(fields=['value'])
    entities.Setting(id=discovery_loc_settings_id, value=loc.read().name).update(fields=['value'])

    media = entities.Media(name="media1", organization=[org], location=[loc]).create(
        create_missing=True
    )

    arch = entities.Architecture(name="arch1").create()
    part = entities.PartitionTable(name="part1").create(create_missing=True)

    os = entities.OperatingSystem(
        name="os1", ptable=[part], medium=[media], architecture=[arch]
    ).create(create_missing=True)

    # domain needs to be in good url format
    domain = entities.Domain(name="sample.com", organization=[org], location=[loc],).create(
        create_missing=True
    )

    subnet = entities.Subnet(
        name="subnet1",
        network="1.1.1.1",
        mask="255.255.255.0",
        domain=[domain],
        organization=[org],
        location=[loc],
    ).create(create_missing=True)

    group = entities.HostGroup(
        name="group1",
        medium=media,
        operatingsystem=os,
        organization=[org],
        location=[loc],
        architecture=arch,
        ptable=part,
        domain=domain,
        subnet=subnet,
        root_pass="somepass",
    ).create(create_missing=True)

    rule = entities.DiscoveryRule(
        name="rule1",
        hostgroup=group,
        search_="ip != 2.2.2.2",
        hostname="<%= @host.facts['hostname'] %>",
        organization=[org],
        location=[loc],
    ).create(create_missing=True)

    headers = {
        'content-type': 'application/json',
    }

    macaddress = gen_mac(multicast=False)
    hostName = gen_string('alpha', length=10)

    data = {
        "facts": {
            "interfaces": "eth3",
            "ipaddress_eth3": "1.1.1.38",
            "netmask_eth3": "255.255.255.0",
            "macaddress_eth3": macaddress,
            "discovery_bootif": macaddress,
            "hostname": hostName,
        }
    }

    response = requests.post(
        '{fdqn}:443/api/v2/discovered_hosts/facts'.format(fdqn=fdqn),
        headers=headers,
        data=str(data),
        verify=False,
    )

    hostNameFromResponse = (
        entities.Host()
        .search(query={'search': 'name="{hostName}"'.format(hostName=hostName)})[0]
        .read()
        .name
    )

    assert hostName == hostNameFromResponse


except Exception:
    traceback.print_exc()

input("Press Enter to teardown...")

try:
    entities.DiscoveryRule().search(query={'search': 'name="rule1"'})[0].delete()
except Exception:
    pass

try:
    entities.HostGroup().search(query={'search': 'name="group1"'})[0].delete()
except Exception:
    pass

try:
    subnet = entities.Subnet().search(query={'search': 'name="subnet1"'})[0]
    subnet.domain = []
    subnet.update(["domain"])
    subnet.delete()
except Exception:
    pass

try:
    entities.Domain().search(query={'search': 'name="sample.com"'})[0].delete()
except Exception:
    pass

try:
    entities.OperatingSystem().search(query={'search': 'name="os1"'})[0].delete()
except Exception:
    pass
try:
    entities.PartitionTable().search(query={'search': 'name="part1"'})[0].delete()
except Exception:
    pass

try:
    entities.Architecture().search(query={'search': 'name="arch1"'})[0].delete()
except Exception:
    pass

try:
    entities.Media().search(query={'search': 'name="media1"'})[0].delete()
except Exception:
    pass

try:
    entities.Organization().search(query={'search': 'name="org1"'})[0].delete()
except Exception:
    pass

try:
    entities.Location().search(query={'search': 'name="loc1"'})[0].delete()
except Exception:
    pass


# Teardown

try:
    entities.Setting(id=discovery_auto_settings_id, value=prior_discovery_auto.value).update(
        fields=['value']
    )
except Exception:
    pass

try:
    entities.Setting(id=discovery_org_settings_id, value=prior_discovery_org.value).update(
        fields=['value']
    )
except Exception:
    pass

try:
    entities.Setting(id=discovery_loc_settings_id, value=prior_discovery_loc.value).update(
        fields=['value']
    )
except Exception:
    pass
