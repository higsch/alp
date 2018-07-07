"""
Parser for files with lines from a logfile.
Lines are formatted by a given formatstring.
E.g. usable for apache access_log files.

Idea: read log file line by line
        -> convert format string to regex
        -> identify fields in log
        -> build kv dictionary
"""
from pathlib import Path
from datetime import datetime
import sys

import re
import user_agents

"""Standard formatstring for uberspace environments."""
fs_uberspace = r"%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""

"""Standard file name of logifile (just for deveklopment)"""
std_filename = "./log/access_log"

"""Supported variables."""
vars = {
    "%h": "remote_hostname",
    "%l": "remote_logname",
    "%u": "remote_user",
    "%t": "time",
    "%r": "first_line_of_http_request",
    "%>s": "final_status",
    "%b": "response_size_bytes",
    "%\{[^\}]+?\}i": "VARNAME"}

"""Regex of supported variables (TODO: needs to be improved)."""    
vars_regex = {
    "%h": r"\S+",
    "%l": r"\S+",
    "%u": r"\S+",
    "%t": r"\S+|\[[\s\S]+\]",
    "%r": r"[\s\S]+",
    "%>s": r"\S+",
    "%b": r"\S+",
    "%\{[^\}]+?\}i": r"[\s\S]+"}

def _logs(filename):
    """Read a single line of a logfile."""
    file = Path(filename).resolve()
    if (file.is_file()):
        with file.open(mode = 'r') as f:
            for line in f.readlines():
                yield line
    else:
        print("No such file '{}'".format(filename), file = sys.stderr)
    
def _replaceVar(s):
    """Replace variable name in %{VARNAME}i structures."""
    res = "no_var"
    for key in vars.keys():
        if (re.match(key, s) is not None):
            res = vars[key]
    if ("VARNAME" in res):
        varname = re.search(r"(?<={)[\w-]+(?=})", s).group(0)
        varname = re.sub("-", "_", varname)
        res = res.replace("VARNAME", varname.lower())
    return(res)
    
def _insertComponentRegex(component):
    """Fill in regex of component.
    TODO: Check if trailing \" are present, then also spaces should be allowed.
    """
    for key in vars_regex:
        if (re.match(key, component) is not None):
            return(vars_regex[key])
    return(r"[\s\S]+")
    
# split log in dictionary
def _splitLogByFormatString(log, fs_regex):
    """Split the log file according to a parsed formatstring.
    Parse time, http request and user agent.
    """
    log_fs_search = re.search(fs_regex, log)
    if (log_fs_search is not None):
        res = log_fs_search.groupdict()
        if ("time" in res):
            res["time"] = _convertTimeStamp(res["time"])
        if ("first_line_of_http_request" in res):
            res["first_line_of_http_request"] = _parseHttpRequest(res["first_line_of_http_request"])
        if ("user_agent" in res):
            res["user_agent"] = _parseUserAgent(res["user_agent"])
        return(res)

def parseFormatString(fs):
    """Parse the formatstring."""
    # get positions of all percent sign structures
    component_regex = "%{[\w-]+}\w?|%>?\w?"
    percent_positions = []
    for match in re.finditer(component_regex, fs):
        percent_positions.append(match.span())
        
    # fill gaps with chars from formatstring
    fs_regex_components = []
    previous_pos = 0
    # go through each found structure and assemble the parsed formatstring
    for pos_tuple in percent_positions:
        if (pos_tuple[0] - previous_pos > 0):
            fs_regex_components.append(fs[previous_pos:pos_tuple[0]])
        component = fs[pos_tuple[0]:pos_tuple[1]]
        fs_regex_components.append("".join(["(?P<", _replaceVar(component), ">", _insertComponentRegex(component), ")"]))
        previous_pos = pos_tuple[1]
    
    # check, if there is a final non-match
    if (previous_pos < len(fs)-1):
        fs_regex_components.append(fs[previous_pos-len(fs):])
        
    # clue the components to a string
    fs_regex = "".join(fs_regex_components)
    return(fs_regex)

def logMap(filename = std_filename, fs = fs_uberspace):
    """Build a map of all log lines."""
    fs_regex = parseFormatString(fs)
    for log in _logs(filename):
        yield _splitLogByFormatString(log, fs_regex)
    
def _convertTimeStamp(ts):
    """Parse the timestamp."""
    d = datetime.strptime(ts, "[%d/%b/%Y:%H:%M:%S %z]")
    return(d)
    
def _parseHttpRequest(httpr):
    """Parse the http request line."""
    httpr_match = re.match("(?P<http_method>\w+) (?P<http_url>.+) (?P<http_version>.+)", httpr)
    if (httpr_match is not None):
        return httpr_match.groupdict();
        
def _parseUserAgent(ua):
    """Parse the user agent."""
    return(user_agents.parse(ua))

if __name__ == "__main__":
    for log in logMap():
        print(log)
    