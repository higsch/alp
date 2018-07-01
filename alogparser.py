import re
from pathlib import Path
import sys
import json

fs_uberspace = "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
std_filename = "./log/access_log"

# read a single line of log file
def _logs(filename):
    file = Path(filename).resolve()
    if (file.is_file()):
        with file.open(mode = 'r') as f:
            for line in f.readlines():
                yield line
        #for line in file_content:
        #    yield line
    else:
        print("No such file '{}'".format(filename), file = sys.stderr)

# split log in dictionary
def _splitLogByFormatString(log, formatstring):
    log_split = re.findall(r'\[.*?\]|\".*?\"|\S+', log)
    formatstring_split = re.findall(r'\S+', formatstring)
    return(dict(zip(formatstring_split, log_split)))

# construct a map of split log items
def logMap(filename = std_filename, formatstring = fs_uberspace):
    map = []
    for log in _logs(filename):
        map.append(_splitLogByFormatString(log, formatstring))
    return(map)

if __name__ == "__main__":
    print(json.dumps(logMap(), indent = 4))