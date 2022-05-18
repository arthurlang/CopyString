#!/usr/bin/python3

import os
import html
import sys
import getopt
import shutil
from xml.dom import minidom
from xml.dom.minidom import parse
from xml.dom.minidom import Node
block_list_str = 'drawable-sw'
default_target_files = 'strings.xml,arrays.xml,arrays_car.xml,arrays_tv.xml,strings_car.xml,strings_tv.xml,dimens.xml,colors.xml'
header = '<?xml version="1.0" encoding="utf-8"?>\n'

def get_target_file_relpath_list(dir_path, target_file_list):
    file_list = []
    
    if not os.path.exists(dir_path):
       print('invalide input_dir_path',dir_path)
    for top, dirs, nondirs in os.walk(dir_path):
        
        for item in nondirs:
            if item in target_file_list:
                path = os.path.join(top, item)
                file_list.append(os.path.relpath(path, dir_path))
    return file_list


def get_all_string_node_map(root_node):
    node_map = {}
    for one in root_node.childNodes:
        if one.nodeType == Node.ELEMENT_NODE and one.hasAttribute("name"):
            node_map[one.getAttribute("name")] = one
    return node_map


def append_or_delete_strings_for_file(file_path, append_strings_text, delete_string_map={}):
    with open(file_path, "r", encoding='UTF-8') as f:
        text = f.read()

    for name in delete_string_map.keys():
        index = text.find(name)
        print(name)
        if index is not -1:
            start = '<' + delete_string_map.get(name)
            print(start)
            end = '</' + delete_string_map.get(name) + '>'
            print(end)
            start_index = text.rfind(start, 0, index)
            start_index = text.rfind('\n', 0, start_index)
            print(start_index)
            end_index = text.find(end, index)
            print(end_index)
            if start_index is not -1 and end_index is not -1:
                text = text[:start_index] + text[end_index + len(end):]

    with open(file_path, "w", encoding='UTF-8') as f:
        text = text.replace('</resources>', append_strings_text + "</resources>", 1)
        f.write(text)


def ensure_file_dir_exits(file):
    dir_path = os.path.dirname(file)
    if not os.path.exists(dir_path):
        print('create path:',dir_path)
        os.makedirs(dir_path)


def create_empty_resource_xml(file):
    ensure_file_dir_exits(file)
    dom = minidom.Document()
    resources_node = dom.createElement("resources")
    resources_node.setAttribute("xmlns:xliff", "urn:oasis:names:tc:xliff:document:1.2")
    resources_node.setAttribute("xmlns:android", "http://schemas.android.com/apk/res/android")
    text_value = dom.createTextNode("\n")
    resources_node.appendChild(text_value)
    dom.appendChild(resources_node)
    with open(file, "w") as f:
        dom.writexml(f, indent='', addindent='\t', newl='\n', encoding='UTF-8')


def add_or_update_strings_for_file_by_list(src_path, dst_path, key_list):
    src_dom_tree = parse(src_path)
    src_map = get_all_string_node_map(src_dom_tree.documentElement)
    for src_key in key_list:
        if src_key in src_map:
            if not os.path.exists(dst_path):
                print("create empty resource xml: ", dst_path)
                create_empty_resource_xml(dst_path)
            break
    if not os.path.exists(dst_path):
        return

    dst_dom_tree = parse(dst_path)
    dst_map = get_all_string_node_map(dst_dom_tree.documentElement)
    need_write = False
    strings = ""
    delete_map = {}
    for src_key in key_list:
        if src_key in src_map:
            need_write = True
            strings = strings + "    " + html.unescape(src_map.get(src_key).toxml()) + "\n"
            if src_key in dst_map:
                delete_map[src_key] = dst_map.get(src_key).nodeName

    if need_write:
        print("add or update strings by list: ", dst_path)
        append_or_delete_strings_for_file(dst_path, strings, delete_map)


def add_all_new_strings_for_file(src_path, dst_path):
    src_dom_tree = parse(src_path)
    dst_dom_tree = parse(dst_path)
    src_map = get_all_string_node_map(src_dom_tree.documentElement)
    dst_map = get_all_string_node_map(dst_dom_tree.documentElement)
    need_write = False
    strings = ""
    for src_key in src_map.keys():
        if src_key not in dst_map:
            need_write = True
            strings = strings + "    " + html.unescape(src_map.get(src_key).toxml()) + "\n"

    if need_write:
        print("add all new strings: ", dst_path)
        append_or_delete_strings_for_file(dst_path, strings)


def add_or_update_strings_for_dir_by_list(src, dst, target_file_list, key_list):
    
    for file in get_target_file_relpath_list(src, target_file_list):
        src_file = os.path.join(src, file)
        if os.path.islink(src_file):
            continue
        dst_file = os.path.join(dst, file)

        add_or_update_strings_for_file_by_list(src_file, dst_file, key_list)


def add_all_new_strings_for_dir(src, dst, target_file_list):
    for file in get_target_file_relpath_list(src, target_file_list):
        src_file = os.path.join(src, file)
        if os.path.islink(src_file):
            continue
        dst_file = os.path.join(dst, file)
        if os.path.exists(dst_file):
            add_all_new_strings_for_file(src_file, dst_file)
        else:
            ensure_file_dir_exits(dst_file)
            print('copy file totally: ', dst_file)
            shutil.copyfile(src_file, dst_file)

def copy_files_by_walk_dirs(src_dir_path,dst_dir_path,target_file_list):
    if not os.path.exists(src_dir_path):
       print('invalide input_dir_path',src_dir_path)
    for top, dirs, nondirs in os.walk(src_dir_path):
        
        for item in nondirs:
            if item in target_file_list:
               src_absolute_path = os.path.join(top, item)
               relative_path = os.path.relpath(src_absolute_path, src_dir_path)
               copy_one_file(relative_path,src_absolute_path,dst_dir_path)

def copy_one_file(relative_path,src_absolute_path,dst_dir_path):
    if relative_path.find(block_list_str) >= 0:
        return
    dst_absolute_path = os.path.join(dst_dir_path, relative_path)
    ensure_file_dir_exits(dst_absolute_path)
    shutil.copyfile(src_absolute_path,dst_absolute_path)

def print_usage():
    print('copy_string.py')
    print('usage:')
    print('copy_string.py -s <src dir path> -d <dst dir path> -n <string name list> -f <target file list> -r <target resources list>')
    print('s: source folder directory')
    print('d: destination folder directory, must have the same directory structure as the source folder directory')
    print('n: optional, list of string name which add or update to the target files, separated by ",".')
    print('   if not set, add all new strings to the target file')
    print('f: optional, list of target file name, separated by ",".')
    print('   default is "strings.xml,arrays.xml,arrays_car.xml,arrays_tv.xml,strings_car.xml,strings_tv.xml"')
    print('for example:')
    print('python3 copy_string.py -s ~/Desktop/SystemUI/packages/SystemUI/res-keyguard -d /Users/daxiong/Desktop/SystemUI/packages/SystemUI/res-keyguard')
    print('or:')
    print('python3 copy_string.py -s ~/Desktop/SystemUI/packages/SystemUI/res-keyguard -d /Users/daxiong/Desktop/SystemUI/packages/SystemUI/res-keyguard -n multi_face_number_reach_limit,multi_face_input -f strings.xml')


def main(argv):
    src = None
    dst = None
    names = ""
    res = ""
    files = default_target_files
    try:
        opts, args = getopt.getopt(argv, "hs:d:n:f:r:", ["src=", "dst=", "names=", "files=", "res="])
    except getopt.GetoptError:
        print_usage()
        sys.exit()
    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ("-s", "--src"):
            src = arg
        elif opt in ("-d", "--dst"):
            dst = arg
        elif opt in ("-n", "--names"):
            names = arg
        elif opt in ("-f", "--files"):
            files = arg
        elif opt in ("-r", "--res"):
            res = arg
    if src is None or dst is None:
        print_usage()
        sys.exit()
    if not src == "":
       print('src: ', src)
    if not dst == "":
       print('dst: ', dst)
    if not names == "":
       print('names: ', names)
    if not files == "":
       print('files: ', files)
    if not res == "":
       print('res: ', res)

    if not res == "":
        copy_files_by_walk_dirs(src, dst, list(set(res.split(","))))
    elif names == "":
        add_all_new_strings_for_dir(src, dst, list(set(files.split(","))))
    else:
        add_or_update_strings_for_dir_by_list(src, dst, list(set(files.split(","))), list(set(names.split(","))))
    print("completed")


if __name__ == "__main__":
   main(sys.argv[1:])
