# Copyright (C) 2008  Lars Wirzenius <liw@liw.fi>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import obnamlib


class Host(obnamlib.Object):

    """A host object."""

    kind = obnamlib.HOST

    def __init__(self, id):
        obnamlib.Object.__init__(self, id=id)
        self._genrefs = None

    def get_genrefs(self):
        if self._genrefs is None:
            self._genrefs = self.find_strings(kind=obnamlib.GENREF)
        return self._genrefs

    def set_genrefs(self, genrefs):
        self._genrefs = genrefs

    genrefs = property(get_genrefs, set_genrefs,
                       doc="References to GEN objects.")

    def prepare_for_encoding(self):
        for genref in self.genrefs:
            c = obnamlib.Component(kind=obnamlib.GENREF, string=genref)
            self.components.append(c)
