# parser for files with lines formatted by a given format formatstring
# usable for apache access_log files
#
# idea: read log file line by line
# -> convert format string to regex
# -> identify fields in log
# -> build kv dictionary
#
import re
from pathlib import Path
import sys
import json

fs = fs_uberspace = r"%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
#                     012345678901234567890123456789012345678901234567890123456789
#                     0         1         2         3         4         5
std_filename = "./log/access_log"

strings = {
    "%h": "remote_hostname",
    "%l": "remote_logname",
    "%u": "remote_user",
    "%t": "time",
    "%r": "first_line_of_request",
    "%>s": "final_status",
    "%b": "response_size_bytes",
    "%\{[^\}]+?\}i": "VARNAME"}

# read a single line of log file
def _logs(filename):
    file = Path(filename).resolve()
    if (file.is_file()):
        with file.open(mode = 'r') as f:
            for line in f.readlines():
                yield line
    else:
        print("No such file '{}'".format(filename), file = sys.stderr)

# split log in dictionary
def _splitLogByFormatString(log, formatstring):
    log_split = re.findall(r'\[.*?\]|\".*?\"|\S+', log)
    formatstring_split = re.findall(r'\S+', formatstring)
    return(dict(zip(formatstring_split, log_split)))
    
def replaceVar(s):
    res = "no_var"
    for key in strings.keys():
        if (re.match(key, s) is not None):
            res = strings[key]
    if ("VARNAME" in res):
        res = res.replace("VARNAME", re.search(r"(?<={)[\w-]+(?=})", s).group(0))
    return(res)    
    
def parseFormatString(fs):
    # get positions of all percent signs
    percent_positions = []
    for match in re.finditer("^%[\w>]|%[\w>{}-]+", fs):
        percent_positions.append(match.span())
    # fill gaps with chars from formatstring
    fs_regex_components = []
    previous_pos = 0
    for pos_tuple in percent_positions:
        if (pos_tuple[0] - previous_pos > 0):
            fs_regex_components.append(fs[previous_pos:pos_tuple[0]])
        fs_regex_components.append("".join(["(?P<", replaceVar(fs[pos_tuple[0]:pos_tuple[1]]), ">^%[\w>]|%[\w>{}-]+)"]))
        previous_pos = pos_tuple[1]
    if (previous_pos < len(fs)-1):
        fs_regex_components.append(fs[previous_pos-len(fs):])
    fs_regex = "".join(fs_regex_components)
    return(fs_regex)

# construct a map of split log items
def logMap(filename = std_filename, formatstring = fs_uberspace):
    map = []
    for log in _logs(filename):
        map.append(_splitLogByFormatString(log, formatstring))
    return(map)

if __name__ == "__main__":
    print(json.dumps(logMap(), indent = 4))