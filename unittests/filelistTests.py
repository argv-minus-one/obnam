import os
import unittest


import wibbrlib


class FileComponentTests(unittest.TestCase):

    def testCreate(self):
        c = wibbrlib.filelist.create_file_component(".", "pink")
        self.check(c)

    def testCreateFromStatResult(self):
        st = os.lstat(".")
        c = wibbrlib.filelist.create_file_component_from_stat(".", st, "pink")
        self.check(c)
        
    def check(self, c):
        self.failIfEqual(c, None)
        subs = wibbrlib.cmp.get_subcomponents(c)
        self.failUnlessEqual(
          wibbrlib.cmp.first_string_by_kind(subs, wibbrlib.cmp.CMP_FILENAME),
          ".")

        st = os.lstat(".")
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_MODE),
          st.st_mode)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_INO),
          st.st_ino)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_DEV),
          st.st_dev)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_NLINK),
          st.st_nlink)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_UID),
          st.st_uid)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_GID),
          st.st_gid)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_SIZE),
          st.st_size)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_ATIME),
          st.st_atime)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_MTIME),
          st.st_mtime)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_CTIME),
          st.st_ctime)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_BLOCKS),
          st.st_blocks)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, 
            wibbrlib.cmp.CMP_ST_BLKSIZE),
          st.st_blksize)

        self.failUnlessEqual(
            wibbrlib.cmp.first_string_by_kind(subs, wibbrlib.cmp.CMP_CONTREF),
            "pink")


class FilelistTests(unittest.TestCase):

    def testCreate(self):
        fl = wibbrlib.filelist.create()
        self.failUnlessEqual(wibbrlib.filelist.num_files(fl), 0)

    def testAddFind(self):
        fl = wibbrlib.filelist.create()
        wibbrlib.filelist.add(fl, ".", "pink")
        self.failUnlessEqual(wibbrlib.filelist.num_files(fl), 1)
        c = wibbrlib.filelist.find(fl, ".")
        self.failUnlessEqual(wibbrlib.cmp.get_kind(c), wibbrlib.cmp.CMP_FILE)

    def testAddFileComponent(self):
        fl = wibbrlib.filelist.create()
        fc = wibbrlib.filelist.create_file_component(".", "pink")
        wibbrlib.filelist.add_file_component(fl, ".", fc)
        self.failUnlessEqual(wibbrlib.filelist.num_files(fl), 1)
        c = wibbrlib.filelist.find(fl, ".")
        self.failUnlessEqual(wibbrlib.cmp.get_kind(c), wibbrlib.cmp.CMP_FILE)

    def testToFromObject(self):
        fl = wibbrlib.filelist.create()
        wibbrlib.filelist.add(fl, ".", "pretty")
        o = wibbrlib.filelist.to_object(fl, "pink")
        self.failUnlessEqual(wibbrlib.obj.get_kind(o), 
                             wibbrlib.obj.OBJ_FILELIST)
        self.failUnlessEqual(wibbrlib.obj.get_id(o), "pink")
        
        fl2 = wibbrlib.filelist.from_object(o)
        self.failIfEqual(fl2, None)
        self.failUnlessEqual(type(fl), type(fl2))
        self.failUnlessEqual(wibbrlib.filelist.num_files(fl2), 1)

        c = wibbrlib.filelist.find(fl2, ".")
        self.failIfEqual(c, None)
        self.failUnlessEqual(wibbrlib.cmp.get_kind(c), wibbrlib.cmp.CMP_FILE)


class FindTests(unittest.TestCase):

    def testFindInodeSuccessful(self):
        pathname = "Makefile"
        fl = wibbrlib.filelist.create()
        wibbrlib.filelist.add(fl, pathname, "pink")
        st = os.lstat(pathname)
        c = wibbrlib.filelist.find_matching_inode(fl, pathname, st)
        subs = wibbrlib.cmp.get_subcomponents(c)
        self.failUnlessEqual(
          wibbrlib.cmp.first_varint_by_kind(subs, wibbrlib.cmp.CMP_ST_MTIME),
          st.st_mtime)

    def testFindInodeUnsuccessful(self):
        pathname = "Makefile"
        fl = wibbrlib.filelist.create()
        wibbrlib.filelist.add(fl, pathname, "pink")
        st = os.lstat(".")
        c = wibbrlib.filelist.find_matching_inode(fl, pathname, st)
        self.failUnlessEqual(c, None)