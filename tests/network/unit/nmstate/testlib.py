#
# Copyright 2019-2020 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#

import pytest

from vdsm.network import nmstate

IPv4_FAMILY = 4
IPv6_FAMILY = 6
IFACE0 = 'eth0'
IFACE1 = 'eth1'
IFACE2 = 'eth2'
TESTNET1 = 'testnet1'
TESTNET2 = 'testnet2'
TESTBOND0 = 'testbond0'
DEFAULT_MTU = 1500
VLAN101 = 101
VLAN102 = 102
IPv4_ADDRESS1 = '192.0.2.1'
IPv4_GATEWAY1 = '192.0.2.254'
IPv4_NETMASK1 = '255.255.255.0'
IPv4_PREFIX1 = 24
IPv6_ADDRESS1 = 'fdb3:84e5:4ff4:55e3::1'
IPv6_PREFIX1 = 64
IPv4_ADDRESS2 = '192.0.3.1'
IPv4_NETMASK2 = '255.255.255.0'
IPv4_PREFIX2 = 24
IPv6_ADDRESS2 = 'fdb3:84e5:4ff4:88e3::1'
IPv6_PREFIX2 = 64
IPv6_GATEWAY = 'fdb3:84e5:4ff4:55e3::ffee'
DNS_SERVERS1 = ['1.2.3.4', '5.6.7.8']
DNS_SERVERS2 = ['9.10.11.12', '13.14.15.16']


parametrize_bridged = pytest.mark.parametrize(
    'bridged', [False, True], ids=['bridgeless', 'bridged']
)
parametrize_vlanned = pytest.mark.parametrize(
    'vlanned', [False, True], ids=['without-vlan', 'with-vlan']
)


def sort_by_name(ifaces_states):
    ifaces_states.sort(key=lambda d: d['name'])


def create_ethernet_iface_state(name, include_type=False, mtu=DEFAULT_MTU):
    state = {nmstate.Interface.NAME: name, nmstate.Interface.STATE: 'up'}
    if include_type:
        state[nmstate.Interface.TYPE] = nmstate.InterfaceType.ETHERNET
    if mtu is not None:
        state[nmstate.Interface.MTU] = mtu
    return state


def create_bond_iface_state(name, mode, slaves, mtu=DEFAULT_MTU, **options):
    state = {
        nmstate.Interface.NAME: name,
        nmstate.Interface.TYPE: 'bond',
        nmstate.Interface.STATE: 'up',
        'link-aggregation': {'mode': mode, 'slaves': slaves},
    }
    if mtu is not None:
        state[nmstate.Interface.MTU] = mtu
    if options:
        state['link-aggregation']['options'] = options
    return state


def create_bridge_iface_state(
    name, port, state='up', mtu=DEFAULT_MTU, options=None
):
    bridge_state = {
        nmstate.Interface.NAME: name,
        nmstate.Interface.STATE: state,
    }

    if state == 'up':
        bridge_state[nmstate.Interface.TYPE] = 'linux-bridge'
        bridge_state[nmstate.Interface.MTU] = mtu
    if port:
        bridge_state[nmstate.LinuxBridge.CONFIG_SUBTREE] = {
            'port': [{'name': port}]
        }
    if options:
        bridge_state['bridge']['options'] = options
    return bridge_state


def generate_bridge_options(stp_enabled):
    return {'stp': {'enabled': stp_enabled}}


def create_vlan_iface_state(base, vlan, mtu=DEFAULT_MTU):
    return {
        nmstate.Interface.NAME: base + '.' + str(vlan),
        nmstate.Interface.TYPE: 'vlan',
        nmstate.Interface.STATE: 'up',
        nmstate.Interface.MTU: mtu,
        'vlan': {'id': vlan, 'base-iface': base},
    }


def disable_iface_ip(*ifaces_states):
    ip_disabled_state = create_ipv4_state()
    ip_disabled_state.update(create_ipv6_state())
    for iface_state in ifaces_states:
        iface_state.update(ip_disabled_state)


def create_ipv4_state(
    address=None, prefix=None, dynamic=False, default_route=False
):
    state = {nmstate.Interface.IPV4: {nmstate.InterfaceIP.ENABLED: False}}
    if dynamic:
        state[nmstate.Interface.IPV4] = {
            nmstate.InterfaceIP.ENABLED: True,
            nmstate.InterfaceIP.DHCP: True,
            nmstate.InterfaceIP.AUTO_DNS: default_route,
            nmstate.InterfaceIP.AUTO_GATEWAY: default_route,
            nmstate.InterfaceIP.AUTO_ROUTES: default_route,
        }
    elif address and prefix:
        state[nmstate.Interface.IPV4] = {
            nmstate.InterfaceIP.ENABLED: True,
            nmstate.InterfaceIP.ADDRESS: [
                {
                    nmstate.InterfaceIP.ADDRESS_IP: address,
                    nmstate.InterfaceIP.ADDRESS_PREFIX_LENGTH: prefix,
                }
            ],
            nmstate.InterfaceIP.DHCP: False,
        }
    return state


def create_ipv6_state(
    address=None, prefix=None, dynamic=False, default_route=False
):
    state = {nmstate.Interface.IPV6: {nmstate.InterfaceIP.ENABLED: False}}
    if dynamic:
        state[nmstate.Interface.IPV6] = {
            nmstate.InterfaceIP.ENABLED: True,
            nmstate.InterfaceIP.DHCP: True,
            'autoconf': True,
            nmstate.InterfaceIP.AUTO_DNS: default_route,
            nmstate.InterfaceIP.AUTO_GATEWAY: default_route,
            nmstate.InterfaceIP.AUTO_ROUTES: default_route,
        }
    elif address and prefix:
        state[nmstate.Interface.IPV6] = {
            nmstate.InterfaceIP.ENABLED: True,
            nmstate.InterfaceIP.ADDRESS: [
                {
                    nmstate.InterfaceIP.ADDRESS_IP: address,
                    nmstate.InterfaceIP.ADDRESS_PREFIX_LENGTH: prefix,
                }
            ],
            nmstate.InterfaceIP.DHCP: False,
            nmstate.InterfaceIPv6.AUTOCONF: False,
        }
    return state


def get_routes_config(gateway, next_hop, ipv6gateway=None, state=None):
    routes = [_create_default_route(gateway, next_hop, IPv4_FAMILY, state)]
    if ipv6gateway:
        routes.append(
            _create_default_route(ipv6gateway, next_hop, IPv6_FAMILY, state)
        )
    return {nmstate.Route.CONFIG: routes}


def _create_default_route(gateway, next_hop, family, state=None):
    destination = '0.0.0.0/0' if family == IPv4_FAMILY else '::/0'
    route_state = {
        nmstate.Route.DESTINATION: destination,
        nmstate.Route.NEXT_HOP_ADDRESS: gateway,
        nmstate.Route.NEXT_HOP_INTERFACE: next_hop,
        nmstate.Route.TABLE_ID: nmstate.Route.USE_DEFAULT_ROUTE_TABLE,
    }
    if state:
        route_state[nmstate.Route.STATE] = state
    return route_state


def create_bonding_config(slaves):
    return {TESTBOND0: {'nics': slaves, 'switch': 'legacy'}}


def create_network_config(
    if_type,
    if_name,
    bridged,
    static_ip_configuration=None,
    dynamic_ip_configuration=None,
    vlan=None,
    mtu=None,
    default_route=False,
    gateway=None,
    ipv6gateway=None,
    nameservers=None,
):
    network_config = _create_interface_network_config(if_type, if_name)
    network_config.update(
        _create_bridge_network_config(bridged, stp_enabled=False)
    )
    network_config.update(static_ip_configuration or {})
    network_config.update(dynamic_ip_configuration or {})
    network_config.update({'vlan': vlan} if vlan is not None else {})
    network_config.update({'mtu': mtu} if mtu is not None else {})
    network_config.update({'defaultRoute': default_route})
    network_config.update({'gateway': gateway} if gateway else {})
    network_config.update({'ipv6gateway': ipv6gateway} if ipv6gateway else {})
    network_config.update(
        {'nameservers': nameservers} if nameservers is not None else {}
    )
    return network_config


def _create_interface_network_config(if_type, if_name):
    return {if_type: if_name, 'switch': 'legacy'}


def _create_bridge_network_config(bridged, stp_enabled):
    network_config = {'bridged': bridged}
    if bridged:
        network_config['stp'] = stp_enabled
    return network_config


def create_static_ip_configuration(
    ipv4_address, ipv4_netmask, ipv6_address, ipv6_prefix_length
):
    ip_config = {}
    if ipv4_address and ipv4_netmask:
        ip_config['ipaddr'] = ipv4_address
        ip_config['netmask'] = ipv4_netmask
    if ipv6_address and ipv6_prefix_length:
        ip_config['ipv6addr'] = ipv6_address + '/' + str(ipv6_prefix_length)
    return ip_config


def create_dynamic_ip_configuration(dhcpv4, dhcpv6, ipv6autoconf):
    dynamic_ip_config = {}
    if dhcpv4:
        dynamic_ip_config['bootproto'] = 'dhcp'
    if dhcpv6:
        dynamic_ip_config['dhcpv6'] = True
    if ipv6autoconf:
        dynamic_ip_config['ipv6autoconf'] = True
    return dynamic_ip_config
