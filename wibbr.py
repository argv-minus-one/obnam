"""Wibbr - a backup program"""


import ConfigParser
import optparse
import subprocess

import wibbrlib.backend
import wibbrlib.mapping
import wibbrlib.object


def default_config():
    """Return a ConfigParser object with the default builtin configuration"""
    items = (
        ("wibbr", "block-size", "%d" % (64 * 1024)),
        ("wibbr", "cache-dir", "tmp.cachedir"),
        ("wibbr", "local-store", "tmp.local-store"),
    )
    
    config = ConfigParser.RawConfigParser()
    for section, item, value in items:
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, item, value)
    
    return config


def parse_args(config, argv):
    parser = optparse.OptionParser()
    
    parser.add_option("--block-size",
                      type="int",
                      metavar="SIZE",
                      help="Make blocks that are about SIZE kilobytes")
    
    parser.add_option("--cache-dir",
                      metavar="DIR",
                      help="Store cached blocks in DIR")
    
    parser.add_option("--local-store",
                      metavar="DIR",
                      help="Use DIR for local block storage (not caching)")

    (options, args) = parser.parse_args(argv)
    
    if options.block_size:
        config.set("wibbr", "block-size", "%d" % options.block_size)
    if options.cache_dir:
        config.set("wibbr", "cache-dir", options.cache_dir)
    if options.local_store:
        config.set("wibbr", "local-store", options.local_store)


def enqueue_object(config, be, map, oq, object_id, object):
    block_size = config.getint("wibbr", "block-size")
    cur_size = wibbrlib.object.object_queue_combined_size(oq)
    if len(object) + cur_size > block_size:
        block_id = wibbrlib.backend.generate_block_id(be)
        block = wibbrlib.object.block_create_from_object_queue(block_id, oq)
        wibbrlib.backend.upload(be, block_id, block)
        for id in wibbrlib.object.object_queue_ids(oq):
            wibbrlib.mapping.mapping_add(map, id, block_id)
        oq = wibbrlib.object.object_queue_create()
    wibbrlib.object.object_queue_add(oq, object_id, object)
    return oq


def create_file_contents_object(config, be, map, oq, filename):
    object_id = wibbrlib.object.object_id_new()
    block_size = config.getint("wibbr", "block-size")
    f = file(filename, "r")
    while True:
        data = f.read(block_size)
        if not data:
            break
        c = wibbrlib.component.component_encode(
                wibbrlib.component.CMP_FILEDATA, data)
        o = wibbrlib.object.object_encode(object_id, 
                wibbrlib.object.OBJ_FILECONT, [c])
        oq = enqueue_object(config, be, map, oq, object_id, o)
    f.close()
    return object_id, oq
