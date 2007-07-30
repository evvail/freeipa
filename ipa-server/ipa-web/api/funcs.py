# Authors: Rob Crittenden <rcritten@redhat.com>
#
# Copyright (C) 2007  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; version 2 only
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

import ldap
import ipa
import ipa.dsinstance
import ipa.ipaldap
import pdb
import string
from types import *
import xmlrpclib

# FIXME, this needs to be auto-discovered
host = 'localhost'
port = 389
binddn = "cn=directory manager"
bindpw = "freeipa"

basedn = "dc=greyoak,dc=com"
scope = ldap.SCOPE_SUBTREE

def get_user (username):
    """Get a specific user's entry. Return as a dict of values.
       Multi-valued fields are represented as lists.
    """
    ent=""

    # FIXME: Is this the filter we want or should it be more specific?
    filter = "(uid="  username  ")"
    try:
        m1 = ipa.ipaldap.IPAdmin(host,port,binddn,bindpw)
        ent = m1.getEntry(basedn, scope, filter, None)
    except ldap.LDAPError, e:
        raise xmlrpclib.Fault(1, e)
    except ipa.ipaldap.NoSuchEntryError:
        raise xmlrpclib.Fault(2, "No such user")

    # Convert to LDIF
    entry = str(ent) 

    # Strip off any junk
    entry = entry.strip()

    # Don't need to identify binary fields and this breaks the parser so
    # remove double colons
    entry = entry.replace('::', ':')
    specs = [spec.split(':') for spec in entry.split('\n')]

    # Convert into a dict. We need to handle multi-valued attributes as well
    # so we'll convert those into lists.
    user={}
    for (k,v) in specs:
        k = k.lower()
        if user.get(k) is not None:
            if isinstance(user[k],list):
                user[k].append(v.strip())
            else:
                first = user[k]
                user[k] = []
                user[k].append(first)
                user[k].append(v.strip())
        else:
            user[k] = v.strip()

    return user
#    return str(ent) # return as LDIF

def add_user (user):
    """Add a user in LDAP"""
    dn="uid=%s,ou=users,ou=default,dc=greyoak,dc=com" % user['uid']
    entry = ipa.ipaldap.Entry(dn)

    # some required objectclasses
    entry.setValues('objectClass', 'top', 'posixAccount', 'shadowAccount', 'account', 'person', 'inetOrgPerson', 'organizationalPerson', 'krbPrincipalAux', 'krbTicketPolicyAux')

    # Fill in shadow fields
    entry.setValue('shadowMin', '0')
    entry.setValue('shadowMax', '99999')
    entry.setValue('shadowWarning', '7')
    entry.setValue('shadowExpire', '-1')
    entry.setValue('shadowInactive', '-1')
    entry.setValue('shadowFlag', '-1')

    # FIXME: calculate shadowLastChange

    # fill in our new entry with everything sent by the user
    for u in user:
        entry.setValues(u, user[u])

    try:
        m1 = ipa.ipaldap.IPAdmin(host,port,binddn,bindpw)
        res = m1.addEntry(entry)
        return res
    except ldap.ALREADY_EXISTS:
        raise xmlrpclib.Fault(3, "User already exists")
        return None
    except ldap.LDAPError, e:
        raise xmlrpclib.Fault(1, str(e))
        return None

def get_add_schema ():
    """Get the list of fields to be used when adding users in the GUI."""

    # FIXME: this needs to be pulled from LDAP
    fields = []

    field1 = {
        "name":       "uid" ,
        "label":      "Login:",
        "type":       "text",
        "validator":  "text",
        "required":   "true"
    }
    fields.append(field1)

    field1 = {
        "name":       "userPassword" ,
        "label":      "Password:",
        "type":       "password",
        "validator":  "String",
        "required":   "true"
    }
    fields.append(field1)

    field1 = {
        "name":       "gn" ,
        "label":      "First name:",
        "type":       "text",
        "validator":  "string",
        "required":   "true"
    }
    fields.append(field1)

    field1 = {
        "name":       "sn" ,
        "label":      "Last name:",
        "type":       "text",
        "validator":  "string",
        "required":   "true"
    }
    fields.append(field1)

    field1 = {
        "name":       "mail" ,
        "label":      "E-mail address:",
        "type":       "text",
        "validator":  "email",
        "required":   "true"
    }
    fields.append(field1)

    return fields
