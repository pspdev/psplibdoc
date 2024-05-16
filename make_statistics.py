#! /usr/bin/env python3

# Generate a HTML report from all the PSP export files, specifying known names for all libraries, and determining which NIDs have been randomized

import psp_libdoc
import glob
import os
import sys
from collections import defaultdict, Counter

OUTPUT_HTML = "./github-pages"

# List of colors & descriptions for each "category" of NID
HTML_STATUS = [
    # for both obfuscated and non-obfuscated
    ("known", "green", "matching the name hash"),
    # for non-obfuscated
    ("unknown", "orange", "unknown"),
    ("wrong", "red", "not matching the name hash"),
    # for obfuscated
    ("nok_from_previous", "yellow", "obfuscated but matching a previous non-obfuscated name"),
    ("nok_dubious", "brown", "obfuscated but found from an unknown source"),
    ("unknown_nonobf", "orange", "unknown and non-obfuscated"),
    ("unknown_obf", "grey", "unknown but obfuscated")
]

def find_html_status(status):
    for (s, color, desc) in HTML_STATUS:
        if s == status:
            return (color, desc)

# Header for the main HTML page
def html_header(versions):
    header = """<!DOCTYPE html>
<html>
<title>PSP NID Status</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<style>
.w3-table .w3-container {
    padding: 0em 0px;
}
.w3-col {
    height:24px;
}
</style>
<body>
<div class="w3-container" style="height:100vh; width:100vw; overflow: scroll;">
<h1>PSP NID Status</h1>
<p>
This page contains the status of all the NIDs from the PSP official firmwares. <br />
To get more details about a library, click its name to see its list of NIDs. <br />
On later firmwares, some kernel NIDs were randomized. A star indicates (most of) the library's NIDs were (re-)randomized at that firmware version. Note that the algorithm used to identify the randomizations is imperfect and, in particular, won't detect libraries whose NIDs have been randomized from the beginning. <br />
Progress counts are given for both non-randomized and randomized NIDs (if present). Note that for randomized NIDs, all specified names are considered correct even though they cannot be verified. <br />
Hover a color to get the numbers and the definition of its status. <br />
</p>"""
    header += """<table class="w3-table"><tr><th>Module name</th><th>Library name</th><th>Progress</th>"""
    for ver in versions:
        header += f"<th>{ver}</th>"
    header += "</tr>"
    return header

# Footer for the main HTML page
def html_footer():
    return """</table></div></body></html>"""

# Output a row of the large table of the main page, for a given module & library, with the statistics given by "make_stats"
def html_library(module, lib, stats_byver, versions):
    # Specify the module and library name
    output = f"""<tr><td>{module}</td><td><a href="modules/{module}_{lib}.html">{lib}</a></td>"""
    # Make statistics over all versions to give an overall % of resolution for the library
    status_bynid = {}
    for ver in stats_byver:
        for status in stats_byver[ver][0]:
            if status == "total":
                continue
            for (nid, _, _, _) in stats_byver[ver][0][status]:
                status_bynid[nid] = status
    cnt = Counter(status_bynid.values())
    both_stats = []
    nonobf_ok = cnt["known"]
    nonobf_total = nonobf_ok + cnt["wrong"] + cnt["unknown_nonobf"] + cnt["unknown"]
    obf_ok = cnt["nok_from_previous"] + cnt["nok_dubious"]
    obf_total = obf_ok + cnt["unknown_obf"]
    if nonobf_total != 0:
        both_stats.append("%.1f%% (%d/%d)" % (nonobf_ok / nonobf_total * 100, nonobf_ok, nonobf_total))
    if obf_total != 0:
        both_stats.append("%.1f%% (%d/%d)" % (obf_ok / obf_total * 100, obf_ok, obf_total))
    agg_stats = " / ".join(both_stats)
    output += f"""<td style="white-space: nowrap;">{agg_stats}</td>"""

    # Make a column for each firmware version
    for ver in versions:
        # Show an empty cell if the library didn't exist in that firmware version
        if ver not in stats_byver:
            output += "<td></td>"
            continue
        output += "<td>"
        cur_stats = stats_byver[ver][0]
        # Add a star if the NIDs of that library were (re-)randomized in that firmware version
        is_obf = stats_byver[ver][1]
        if is_obf:
            obf_str = '<div style="position: absolute; width: 100%; height: 100%; text-align: center;">*</div>'
        else:
            obf_str = ''

        # Make progress bars with tooltips and colors given in HTML_STATUS
        for (status, color, desc) in HTML_STATUS:
            if status not in cur_stats:
                continue
            count = len(cur_stats[status])
            if count == 0:
                continue
            total = cur_stats['total']
            percent = int(count / total * 100)

            output += f"""<div style="position: relative;"><div class="w3-col w3-container w3-{color} w3-tooltip" style="width:{percent}%">
<span style="position:absolute;left:0;bottom:18px" class="w3-text w3-tag">{count}/{total} NIDs are {desc}</span>
</div>"""
        output += f"{obf_str}</div></td>"
    return output

# Output a HTML page for a single library
def html_single_library(module, lib, stats_bynid, versions):
    output = f"""<!DOCTYPE html>
<html>
<title>PSP NID Status for {lib} in {module}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<body>
<div class="w3-container" style="height:100vh; width:100vw; overflow: scroll;">
<h1>{module}: {lib}</h1>
<p>
This page contains the status of all the NIDs from the {lib} library inside the {module} module.<br />
Hover a cell to know the meaning of the color. <br />
"..." means the given name is the same as the one on its left. <br />
</p>
"""
    # Output the header row (containing all the firmware versions)
    output += """<table class="w3-table"><tr><th>NID</th>"""
    for v in versions:
        output += f"<th>{v}</th>"
    output += '</tr>'
    # Sort NIDs by the first firmware version they appear in, then by the names associated to them
    sorted_nids = []
    sources = {}
    for v in versions:
        ver_nids = []
        for nid in stats_bynid:
            if v in stats_bynid[nid]:
                (_, name, source) = stats_bynid[nid][v]
                sources[name] = source
                ver_nids.append((name, nid))
        for (_, nid) in sorted(ver_nids):
            if nid not in sorted_nids:
                sorted_nids.append(nid)
    # For each NID, show the associated name, status & a tooltip explaining its status
    for nid in sorted_nids:
        output += f"<tr><td>{nid}</td>"
        last_name = None
        for v in versions:
            if v not in stats_bynid[nid]:
                output += "<td></td>"
            else:
                (status, name, source) = stats_bynid[nid][v]
                show_name = name
                source_str = ''
                if name == last_name:
                    show_name = '...'
                elif source != '' and source != 'matching':
                    source_str = ' (source: ' + source + ')'
                last_name = name
                (color, desc) = find_html_status(status)
                output += f"""<td class="w3-{color}"><div class="w3-tooltip">{show_name}{source_str}<span style="position:absolute;left:0;bottom:18px" class="w3-text w3-tag">NID is {desc}</span></div></td>"""
        output += "</tr>"
    output += "</table></div></body></html>"
    return output

# Build the statistics for a given library at a given version. "obfuscated" is specified if the NIDs of the library have been randomized in the current or a previous firmware version.
# "prev_nonobf" lists the NIDs already seen in a version of the library were the NIDs were not (yet) randomized.
# "prev_ok" lists all the NIDs for which a name was found (which corresponds to the NID when computing the hash).
def make_stats(module, lib, version, obfuscated, cur_nids, prev_nonobf, prev_ok):
    unk_nids = []
    nok_nids = []
    ok_nids = []
    # Sort NIDs by category: unknown (name ends with the NID), ok (NID matches the hash) and nok (NID doesn't match the hash)
    for cur_nid in cur_nids:
        nid = cur_nid["nid"]
        name = cur_nid["name"]
        if not obfuscated:
            prev_nonobf[nid] = (version, name)
        if name.endswith(nid):
            unk_nids.append(cur_nid)
        elif psp_libdoc.compute_nid(name) == nid:
            ok_nids.append(cur_nid)
        else:
            nok_nids.append(cur_nid)

    if obfuscated:
        nok_dubious = []
        nok_from_prev = []
        # If the NIDs have been randomized, it means they cannot be confirmed using the hash,
        # but they might come from previous versions of the libraries when the NIDs were not randomized.
        # Here, check if the names were found in previous non-randomized versions of the library.
        for cur_nid in nok_nids:
            nid = cur_nid["nid"]
            name = cur_nid["name"]
            if nid in prev_ok or nid in prev_nonobf:
                print("WARN: previously seen non-obfuscated:", module, lib, version, nid, name, prev_nonobf[nid], file=sys.stderr)
            found_prev = False
            for nid2 in prev_ok:
                if prev_ok[nid2][1] == name:
                    found_prev = True
                    break
            if not found_prev:
                nok_dubious.append(cur_nid)
            else:
                nok_from_prev.append(cur_nid)

        # For unknown names, differentiate between the ones seen in non-randomized versions, and the ones never seen in one (ie most likely randomized).
        unk_nonobf = []
        unk_obf = []
        for cur_nid in unk_nids:
            nid = cur_nid["nid"]
            if nid in prev_ok: # could by prev_nonobf, for pure information
                print("WARN: previously seen non-obfuscated OK:", module, lib, version, nid, prev_ok[nid], file=sys.stderr)
            if nid in prev_nonobf:
                unk_nonobf.append(cur_nid)
            else:
                unk_obf.append(cur_nid)
        stats = {"known": ok_nids, "unknown_nonobf": unk_nonobf, "unknown_obf": unk_obf, "nok_from_previous": nok_from_prev, "nok_dubious": nok_dubious}
    else:
        # For non-obfuscated modules, it's more simple, just do a safety check to see if there's no NID which was known in previous versions but is wrong or unknown in a later one.
        for cur_nid in (nok_nids + unk_nids):
            nid = cur_nid["nid"]
            name = cur_nid["name"]
            if nid in prev_ok:
                print("WARN: previously seen OK:", module, lib, version, nid, name, prev_ok[nid], file=sys.stderr)
        stats = {"known": ok_nids, "unknown": unk_nids, "wrong": nok_nids}

    stats['total'] = len(cur_nids)

    for cur_nid in ok_nids:
        prev_ok[cur_nid["nid"]] = (version, cur_nid["name"])

    return stats

def get_nids_ver(nids, ver):
    output = []
    for nid in nids:
        if ver in nid["versions"]:
            output.append(nid)
    return output

# Make statistics for all the versions of a library, write the single HTML page, and return the row for the main page
def handle_library(module, lib, nids, versions):
    vers = list(sorted(set([v for nid in nids for v in nid["versions"]])))
    # Indicates the NIDs had at least one round of randomization in previous (or current) firmware version
    now_obfuscated = False
    prev_nonobf = {}
    prev_ok = {}
    stats_byver = {vers[0]: (make_stats(module, lib, vers[0], now_obfuscated, get_nids_ver(nids, vers[0]), prev_nonobf, prev_ok), False)}
    for (v1, v2) in zip(vers, vers[1:]):
        # For each consecutive firmware versions v1 and v2, see their respective NIDs
        v1_nids = set([x["nid"] for x in get_nids_ver(nids, v1)])
        v2_nids = set([x["nid"] for x in get_nids_ver(nids, v2)])
        # Check the NIDs which appeared and the ones which disappeared
        new_nids = v2_nids - v1_nids
        disappear_nids = v1_nids - v2_nids
        # Heuristic to find randomization rounds: if more than 20% of the NIDs of the new version are new, and more than 20% of the NIDs of the previous version disappeared
        # This works in almost all cases, except it never detects if a library got randomized NIDs from the beginning
        new_ratio = len(new_nids) / len(v2_nids)
        dis_ratio = len(disappear_nids) / len(v1_nids)
        is_obfuscated = False
        if new_ratio > 0.2 and dis_ratio > 0.2:
            is_obfuscated = True
            # If we find a new NID whose name is known, then it means there cannot have been a randomization here (note this check triggers rarely), except for 5.55 which misses functions from 5.51
            for n in new_nids:
                name = None
                for nid in get_nids_ver(nids, v2):
                    if nid["nid"] == n:
                        name = nid["name"]
                if psp_libdoc.compute_nid(name) == n and v1 != '5.55': # some exceptions exist for 5.55 (which misses functions from 5.51)
                    is_obfuscated = False
        if is_obfuscated:
            now_obfuscated = True
        stats_byver[v2] = (make_stats(module, lib, v2, now_obfuscated, get_nids_ver(nids, v2), prev_nonobf, prev_ok), is_obfuscated)

    # Get the results by NID for the individual pages
    stats_bynid = defaultdict(dict)
    for v in vers:
        for status in stats_byver[v][0]:
            if status == "total":
                continue
            for cur_nid in stats_byver[v][0][status]:
                stats_bynid[cur_nid["nid"]][v] = (status, cur_nid["name"], cur_nid["source"])
    with open(OUTPUT_HTML + '/modules/' + module + '_' + lib + '.html', 'w') as fd:
        fd.write(html_single_library(module, lib, stats_bynid, vers))

    return html_library(module, lib, stats_byver, versions)

def main():
    # Create the folders for the HTML output
    os.makedirs(OUTPUT_HTML, exist_ok=True)
    os.makedirs(OUTPUT_HTML + "/modules", exist_ok=True)

    # Parse all the NID export files
    filelist = glob.glob('PSPLibDoc/**/*.xml', recursive=True)

    nid_bylib = defaultdict(lambda: defaultdict(list))
    versions = set()

    for file in filelist:
        entries = psp_libdoc.loadPSPLibdoc(file)
        for e in entries:
            cur_ver = [v for v in e.versions if not v.startswith('vita')]
            for v in cur_ver:
                versions.add(v)
            if len(cur_ver) == 0:
                continue
            nid_bylib[e.prx][e.libraryName].append({"nid": e.nid, "name": e.name, "versions": cur_ver, "source": e.source})

    versions = list(sorted(versions))

    # Output the main and single HTML pages
    html_output = html_header(versions)
    for prx in sorted(nid_bylib):
        for lib in sorted(nid_bylib[prx]):
            html_output += handle_library(prx, lib, nid_bylib[prx][lib], versions)
    html_output += html_footer()
    with open(OUTPUT_HTML + "/index.html", 'w') as fd:
        fd.write(html_output)

if __name__ == '__main__':
    main()

