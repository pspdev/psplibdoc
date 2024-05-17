#!/usr/bin/python3

from collections import defaultdict
import Levenshtein
import psp_libdoc
import re
import subprocess
import sys

def run_prxtool(binary_path):
    return subprocess.check_output(["prxtool", "-w", binary_path], stderr=subprocess.DEVNULL).decode('ascii')

def get_raw_functions(binary_path):
    data = run_prxtool(binary_path)
    funs = defaultdict(str)
    cur_fun = None
    names = []
    for line in data.split('\n'):
        if 'Subroutine' in line:
            # ; Subroutine sceUsb_C21645A4 - Address 0x00002F40 - Aliases: sceUsb_driver_C21645A4, sceUsbBus_driver_C21645A4
            m = re.match(r"; Subroutine ([^ ]*) .*", line)
            names = [m.groups()[0]]
            alias_pos = line.find("Aliases: ")
            if alias_pos != -1:
                alias_str = line[alias_pos + len("Aliases: "):]
                names += alias_str.split(", ")
        elif line.startswith('\t0x'):
            m = re.match(r"\t0x[0-9A-F]{8}: 0x([0-9A-F]{8})", line)
            data = m.groups()[0]
            for n in names:
                funs[n] += data
        elif '; Imported from' in line:
            break
    return funs

def match_module_pair(path1, path2):
    funs1 = {k: v for k, v in get_raw_functions(path1).items() if not k.startswith('sub_')}
    funs2 = {k: v for k, v in get_raw_functions(path2).items() if not k.startswith('sub_')}
    result = {}
    while len(funs1) > 0 and len(funs2) > 0:
        closest_pair = None
        min_dist = None
        for (f1, c1) in funs1.items():
            if f1.startswith('sub_'):
                continue
            lib1 = f1[:-8]
            for (f2, c2) in funs2.items():
                if f2.startswith('sub_'):
                    continue
                lib2 = f2[:-8]
                if lib1 != lib2:
                    continue
                cur_dist = Levenshtein.distance(c1, c2)
                if min_dist is None or cur_dist < min_dist:
                    min_dist = cur_dist
                    closest_pair = (f1, f2)
        #print(closest_pair, min_dist)
        del funs1[closest_pair[0]]
        del funs2[closest_pair[1]]
        result[closest_pair[0]] = closest_pair[1]
    return result

def match_modules(paths):
    results = []
    for (path1, path2) in zip(paths, paths[1:]):
        print("check", path1, path2)
        results.append(match_module_pair(path1, path2))

    checked = set()
    nid_matches = {}
    for j in range(len(results)):
        for k in results[j]:
            if k not in checked:
                firstk = k
                for i in range(j, len(results)):
                    checked.add(k)
                    print(k, '->', end=' ')
                    if k not in results[i]:
                        break
                    k = results[i][k]
                    checked.add(k)
                    nid_matches[k] = firstk
                print()
    return nid_matches

def check_entry(entries, funname):
    lib = '_'.join(funname.split('_')[:-1])
    nid = funname.split('_')[-1]
    for e in entries:
        if e.nid == nid and e.libraryName == lib:
            if not e.name.endswith(e.nid):
                return e.name
            else:
                return None
    assert(False)

def fix_psplibdoc(libdoc, modules):
    nid_matches = match_modules(modules)

    entries = psp_libdoc.loadPSPLibdoc(libdoc)
    entries2 = []
    for e in entries:
        funname = e.libraryName + '_' + e.nid
        if e.name.endswith(e.nid) and funname in nid_matches:
            prev_name = check_entry(entries, nid_matches[funname])
            print(funname, '->', prev_name)
            e = e._replace(name = prev_name, source = "previous version (automated)")
        entries2.append(e)

    psp_libdoc.exportPSPLibdocCombined(entries2, libdoc, None, True)

if __name__ == '__main__':
    #get_raw_functions(sys.argv[1])
    #match_module_pair(sys.argv[1], sys.argv[2])
    #match_modules(sys.argv[1:])
    fix_psplibdoc(sys.argv[1], sys.argv[2:])

