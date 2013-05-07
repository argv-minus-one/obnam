# Copyright 2013  Lars Wirzenius
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# =*= License: GPL-3+ =*=


import obnamlib


class KeyValueStore(object):

    def __init__(self):
        self._map = {}

    def get_value(self, key, default):
        if key in self._map:
            return self._map[key]
        return default

    def set_value(self, key, value):
        self._map[key] = value

    def items(self):
        return self._map.items()

    def copy(self):
        other = KeyValueStore()
        for key, value in self.items():
            other.set_value(key, value)
        return other


class LockableKeyValueStore(object):

    def __init__(self):
        self.locked = False
        self.data = KeyValueStore()
        self.stashed = None

    def lock(self):
        assert not self.locked
        self.stashed = self.data
        self.data = self.data.copy()
        self.locked = True

    def unlock(self):
        assert self.locked
        self.data = self.stashed
        self.stashed = None
        self.locked = False

    def commit(self):
        assert self.locked
        self.stashed = None
        self.locked = False

    def get_value(self, key, default):
        return self.data.get_value(key, default)

    def set_value(self, key, value):
        self.data.set_value(key, value)

    def items(self):
        return self.data.items()


class Counter(object):

    def __init__(self):
        self._latest = 0

    def next(self):
        self._latest += 1
        return self._latest


class DummyClient(object):

    def __init__(self, name):
        self.name = name
        self.generation_counter = Counter()
        self.data = LockableKeyValueStore()

    def lock(self):
        if self.data.locked:
            raise obnamlib.RepositoryClientLockingFailed(self.name)
        self.data.lock()

    def _require_lock(self):
        if not self.data.locked:
            raise obnamlib.RepositoryClientNotLocked(self.name)

    def unlock(self):
        self._require_lock()
        self.data.unlock()

    def commit(self):
        self._require_lock()
        self.data.set_value('current-generation', None)
        self.data.commit()

    def get_key(self, key):
        return self.data.get_value(key, '')

    def set_key(self, key, value):
        self._require_lock()
        self.data.set_value(key, value)

    def get_generation_ids(self):
        key = 'generation-ids'
        return self.data.get_value(key, [])

    def create_generation(self):
        self._require_lock()
        if self.data.get_value('current-generation', None) is not None:
            raise obnamlib.RepositoryClientGenerationUnfinished(self.name)
        generation_id = (self.name, self.generation_counter.next())
        ids = self.data.get_value('generation-ids', [])
        self.data.set_value('generation-ids', ids + [generation_id])
        self.data.set_value('current-generation', generation_id)
        return generation_id

    def get_generation_key(self, gen_id, key):
        return self.data.get_value(gen_id + (key,), '')

    def set_generation_key(self, gen_id, key, value):
        self._require_lock()
        self.data.set_value(gen_id + (key,), value)

    def remove_generation(self, gen_id):
        self._require_lock()
        ids = self.data.get_value('generation-ids', [])
        if gen_id not in ids:
            raise obnamlib.RepositoryGenerationDoesNotExist(self.name)
        self.data.set_value('generation-ids', [x for x in ids if x != gen_id])

    def get_generation_chunk_ids(self, gen_id):
        return []


class DummyClientList(object):

    def __init__(self):
        self.data = LockableKeyValueStore()

    def lock(self):
        if self.data.locked:
            raise obnamlib.RepositoryClientListLockingFailed()
        self.data.lock()

    def unlock(self):
        if not self.data.locked:
            raise obnamlib.RepositoryClientListNotLocked()
        self.data.unlock()

    def commit(self):
        if not self.data.locked:
            raise obnamlib.RepositoryClientListNotLocked()
        self.data.commit()

    def force(self):
        if self.data.locked:
            self.unlock()
        self.lock()

    def _require_lock(self):
        if not self.data.locked:
            raise obnamlib.RepositoryClientListNotLocked()

    def names(self):
        return [k for k, v in self.data.items() if v is not None]

    def __getitem__(self, client_name):
        client = self.data.get_value(client_name, None)
        if client is None:
            raise obnamlib.RepositoryClientDoesNotExist(client_name)
        return client

    def add(self, client_name):
        self._require_lock()
        if self.data.get_value(client_name, None) is not None:
            raise obnamlib.RepositoryClientAlreadyExists(client_name)
        self.data.set_value(client_name, DummyClient(client_name))

    def remove(self, client_name):
        self._require_lock()
        if self.data.get_value(client_name, None) is None:
            raise obnamlib.RepositoryClientDoesNotExist(client_name)
        self.data.set_value(client_name, None)

    def rename(self, old_client_name, new_client_name):
        self._require_lock()
        client = self.data.get_value(old_client_name, None)
        if client is None:
            raise obnamlib.RepositoryClientDoesNotExist(old_client_name)
        if self.data.get_value(new_client_name, None) is not None:
            raise obnamlib.RepositoryClientAlreadyExists(new_client_name)
        self.data.set_value(old_client_name, None)
        self.data.set_value(new_client_name, client)

    def get_client_by_generation_id(self, gen_id):
        client_name, generation_number = gen_id
        return self[client_name]


class RepositoryFormatDummy(obnamlib.RepositoryInterface):

    '''Simplistic repository format for testing.

    This class exists to exercise the RepositoryInterfaceTests class.

    '''

    format = 'dummy'

    def __init__(self):
        self._client_list = DummyClientList()

    def set_fs(self, fs):
        pass

    def init_repo(self):
        pass

    def get_client_names(self):
        return self._client_list.names()

    def lock_client_list(self):
        self._client_list.lock()

    def unlock_client_list(self):
        self._client_list.unlock()

    def commit_client_list(self):
        self._client_list.commit()

    def force_client_list_lock(self):
        self._client_list.force()

    def add_client(self, client_name):
        self._client_list.add(client_name)

    def remove_client(self, client_name):
        self._client_list.remove(client_name)

    def rename_client(self, old_client_name, new_client_name):
        self._client_list.rename(old_client_name, new_client_name)

    def lock_client(self, client_name):
        self._client_list[client_name].lock()

    def unlock_client(self, client_name):
        self._client_list[client_name].unlock()

    def commit_client(self, client_name):
        self._client_list[client_name].commit()

    def get_allowed_client_keys(self):
        return [obnamlib.REPO_CLIENT_TEST_KEY]

    def get_client_key(self, client_name, key):
        return self._client_list[client_name].get_key(key)

    def set_client_key(self, client_name, key, value):
        if key not in self.get_allowed_client_keys():
            raise obnamlib.RepositoryClientKeyNotAllowed(
                self.format, client_name, key)
        self._client_list[client_name].set_key(key, value)

    def get_client_generation_ids(self, client_name):
        return self._client_list[client_name].get_generation_ids()

    def create_generation(self, client_name):
        return self._client_list[client_name].create_generation()

    def get_allowed_generation_keys(self):
        return [obnamlib.REPO_GENERATION_TEST_KEY]

    def get_generation_key(self, generation_id, key):
        client = self._client_list.get_client_by_generation_id(generation_id)
        return client.get_generation_key(generation_id, key)

    def set_generation_key(self, generation_id, key, value):
        client = self._client_list.get_client_by_generation_id(generation_id)
        if key not in self.get_allowed_generation_keys():
            raise obnamlib.RepositoryGenerationKeyNotAllowed(
                self.format, client.name, key)
        return client.set_generation_key(generation_id, key, value)

    def remove_generation(self, generation_id):
        client = self._client_list.get_client_by_generation_id(generation_id)
        client.remove_generation(generation_id)

    def get_generation_chunk_ids(self, generation_id):
        client = self._client_list.get_client_by_generation_id(generation_id)
        return client.get_generation_chunk_ids(generation_id)

