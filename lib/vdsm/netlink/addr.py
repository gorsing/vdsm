# Copyright 2014 Red Hat, Inc.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#
from ctypes import (CFUNCTYPE, byref, c_char, c_int, c_void_p, sizeof)
from functools import partial

from . import _cache_manager, _nl_cache_get_first, _nl_cache_get_next
from . import _char_proto, _int_char_proto, _int_proto, _void_proto
from . import (_ethtool_uses_libnl3, LIBNL_ROUTE, _nl_addr2str, _nl_af2str,
               _nl_geterror, _pool, _rtnl_scope2str)
from .link import _nl_link_cache, _link_index_to_name

CHARBUFFSIZE = 40  # Increased to fit IPv6 expanded representations


def iter_addrs():
    """Generator that yields an information dictionary for each network address
    in the system."""
    with _pool.socket() as sock:
        with _nl_addr_cache(sock) as addr_cache:
            with _nl_link_cache(sock) as link_cache:  # for index to label
                addr = _nl_cache_get_first(addr_cache)
                while addr:
                    yield _addr_info(link_cache, addr)
                    addr = _nl_cache_get_next(addr)


def _addr_info(link_cache, addr):
    """Returns a dictionary with the address information."""
    index = _rtnl_addr_get_ifindex(addr)
    return {
        'label': (_rtnl_addr_get_label(addr) or
                  _link_index_to_name(link_cache, index)),
        'index': index,
        'family': _addr_family(addr),
        'prefixlen': _rtnl_addr_get_prefixlen(addr),
        'scope': _addr_scope(addr),
        'flags': _addr_flags(addr),
        'address': _addr_local(addr)}


def _addr_flags(addr):
    """Returns the textual representation of the address flags"""
    flags = (c_char * (CHARBUFFSIZE * 2))()
    return frozenset(_rtnl_addr_flags2str(_rtnl_addr_get_flags(addr), flags,
                     sizeof(flags)).split(','))


def _addr_scope(addr):
    """Returns the scope name for which the address is defined."""
    scope = (c_char * CHARBUFFSIZE)()
    return _rtnl_scope2str(_rtnl_addr_get_scope(addr), scope, sizeof(scope))


def _addr_family(addr):
    """Returns the family name of the address."""
    family = (c_char * CHARBUFFSIZE)()
    return _nl_af2str(_rtnl_addr_get_family(addr), family, sizeof(family))


def _addr_local(addr):
    """Returns the textual representation of the address."""
    address = (c_char * CHARBUFFSIZE)()
    return _nl_addr2str(_rtnl_addr_get_local(addr), address, sizeof(address))


# C function prototypes
# http://docs.python.org/2/library/ctypes.html#function-prototypes
# This helps ctypes know the calling conventions it should use to communicate
# with the binary interface of libnl and which types it should allocate and
# cast. Without it ctypes fails when not running on the main thread.
if _ethtool_uses_libnl3():
    _addr_alloc_cache = CFUNCTYPE(c_int, c_void_p, c_void_p)(
        ('rtnl_addr_alloc_cache', LIBNL_ROUTE))

    def _rtnl_addr_alloc_cache(sock):
        """Wraps the new addr alloc cache to expose the libnl1 signature"""
        cache = c_void_p()
        err = _addr_alloc_cache(sock, byref(cache))
        if err:
            raise IOError(-err, _nl_geterror())
        return cache

else:  # libnl-1
    from . import _alloc_cache
    # Change from handle to socket as it is now more accurately called in
    # libnl-3
    _addr_alloc_cache = _void_proto(('rtnl_addr_alloc_cache', LIBNL_ROUTE))

    _rtnl_addr_alloc_cache = partial(_alloc_cache, _addr_alloc_cache)

_nl_addr_cache = partial(_cache_manager, _rtnl_addr_alloc_cache)

_rtnl_addr_get_label = _char_proto(('rtnl_addr_get_label', LIBNL_ROUTE))
_rtnl_addr_get_ifindex = _int_proto(('rtnl_addr_get_ifindex', LIBNL_ROUTE))
_rtnl_addr_get_family = _int_proto(('rtnl_addr_get_family', LIBNL_ROUTE))
_rtnl_addr_get_prefixlen = _int_proto(('rtnl_addr_get_prefixlen', LIBNL_ROUTE))
_rtnl_addr_get_scope = _int_proto(('rtnl_addr_get_scope', LIBNL_ROUTE))
_rtnl_addr_get_flags = _int_proto(('rtnl_addr_get_flags', LIBNL_ROUTE))
_rtnl_addr_get_local = _void_proto(('rtnl_addr_get_local', LIBNL_ROUTE))
_rtnl_addr_flags2str = _int_char_proto(('rtnl_addr_flags2str', LIBNL_ROUTE))
