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
std_filename = "./log/access_log"

vars = {
    "%h": "remote_hostname",
    "%l": "remote_logname",
    "%u": "remote_user",
    "%t": "time",
    "%r": "first_line_of_request",
    "%>s": "final_status",
    "%b": "response_size_bytes",
    "%\{[^\}]+?\}i": "VARNAME"}
    
vars_regex = {
    "%h": "\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "%l": "\S+",
    "%u": "",
    "%t": "",
    "%r": "",
    "%>s": "",
    "%b": "",
    "%\{[^\}]+?\}i": ""}

# This one would work:
# (?P<remote_hostname>[\S]+) (?P<remote_logname>[\S]+) (?P<remote_user>[\S]+) (?P<time>[\s\S]+) \"(?P<first_line_of_request>[\s\S]+)\" (?P<final_status>[\S]+) (?P<response_size_bytes>[\S]+) \"(?P<Referer>[\S]+)\" \"(?P<Useragent>[\s\S]+)\"

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
    
def _replaceVar(s):
    res = "no_var"
    for key in vars.keys():
        if (re.match(key, s) is not None):
            res = vars[key]
    if ("VARNAME" in res):
        varname = re.search(r"(?<={)[\w-]+(?=})", s).group(0)
        varname = re.sub("-","", varname)
        res = res.replace("VARNAME", varname)
    return(res)

def _insertComponentRegex():
       # TODO: translate different components to their regex
    
def parseFormatString(fs):
    # get positions of all percent signs
    component_regex = "^%[\w>]|%[\w>{}-]+"
    any_string_regex = "[\s\S]+"
    percent_positions = []
    for match in re.finditer(component_regex, fs):
        percent_positions.append(match.span())
    # fill gaps with chars from formatstring
    fs_regex_components = []
    previous_pos = 0
    for pos_tuple in percent_positions:
        if (pos_tuple[0] - previous_pos > 0):
            fs_regex_components.append(fs[previous_pos:pos_tuple[0]])
        component = fs[pos_tuple[0]:pos_tuple[1]]
        fs_regex_components.append("".join(["(?P<", _replaceVar(component), ">", _insertComponentRegex(component), ")"]))
        previous_pos = pos_tuple[1]
    if (previous_pos < len(fs)-1):
        fs_regex_components.append(fs[previous_pos-len(fs):])
    fs_regex = "".join(fs_regex_components)
    print(fs_regex)
    return(fs_regex)

# construct a map of split log items
def logMap(filename = std_filename, formatstring = fs_uberspace):
    map = []
    for log in _logs(filename):
        map.append(_splitLogByFormatString(log, formatstring))
    return(map)

if __name__ == "__main__":
    print(json.dumps(logMap(), indent = 4))