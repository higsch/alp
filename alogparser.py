# parser for files with lines formatted by a given format formatstring
# usable for apache access_log files
#
# idea: read log file line by line
# -> convert format string to regex
# -> identify fields in log
# -> build kv dictionary
#
from pathlib import Path
from datetime import datetime
import sys

import re
import user_agents

fs_uberspace = r"%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
std_filename = "./log/access_log"

vars = {
    "%h": "remote_hostname",
    "%l": "remote_logname",
    "%u": "remote_user",
    "%t": "time",
    "%r": "first_line_of_http_request",
    "%>s": "final_status",
    "%b": "response_size_bytes",
    "%\{[^\}]+?\}i": "VARNAME"}
    
vars_regex = {
    "%h": r"\S+",
    "%l": r"\S+",
    "%u": r"\S+",
    "%t": r"\S+|\[[\s\S]+\]",
    "%r": r"[\s\S]+",
    "%>s": r"\S+",
    "%b": r"\S+",
    "%\{[^\}]+?\}i": r"[\s\S]+"}

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
    
def _replaceVar(s):
    res = "no_var"
    for key in vars.keys():
        if (re.match(key, s) is not None):
            res = vars[key]
    if ("VARNAME" in res):
        varname = re.search(r"(?<={)[\w-]+(?=})", s).group(0)
        varname = re.sub("-","", varname)
        res = res.replace("VARNAME", varname.lower())
    return(res)

# TODO: Check if trailing \" are present, then also spaces should be allowed
def _insertComponentRegex(component):
    for key in vars_regex:
        if (re.match(key, component) is not None):
            return(vars_regex[key])
    return(r"[\s\S]+")
    
# split log in dictionary
def _splitLogByFormatString(log, fs_regex):
    log_fs_search = re.search(fs_regex, log)
    if (log_fs_search is not None):
        res = log_fs_search.groupdict()
        if ("time" in res):
            res["time"] = _convertTimeStamp(res["time"])
        if ("first_line_of_http_request" in res):
            res["first_line_of_http_request"] = _parseHttpRequest(res["first_line_of_http_request"])
        if ("useragent" in res):
            res["useragent"] = _parseUserAgent(res["useragent"])
        return(res)

def parseFormatString(fs):
    # get positions of all percent signs
    component_regex = "%{[\w-]+}\w?|%>?\w?"
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
    return(fs_regex)

# construct a map of split log items
def logMap(filename = std_filename, fs = fs_uberspace):
    fs_regex = parseFormatString(fs)
    for log in _logs(filename):
        yield _splitLogByFormatString(log, fs_regex)
    
def _convertTimeStamp(ts):
    d = datetime.strptime(ts, "[%d/%b/%Y:%H:%M:%S %z]")
    return(d)
    
def _parseHttpRequest(httpr):
    httpr_match = re.match("(?P<http_method>\w+) (?P<http_url>.+) (?P<http_version>.+)", httpr)
    if (httpr_match is not None):
        return httpr_match.groupdict();
        
def _parseUserAgent(ua):
    return(user_agents.parse(ua))

if __name__ == "__main__":
    print(logMap())
    