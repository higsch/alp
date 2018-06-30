from pathlib import Path
import sys

fs_uberspace = "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""
filename = "./log/access_log"

# read a single line of log file
def logs(filename):
    file = Path(filename).resolve()
    if (file.is_file()):
        with file.open(mode = 'r') as f:
            for line in f.readlines():
                yield line
        #for line in file_content:
        #    yield line
    else:
        print("No such file '{}'".format(filename), file = sys.stderr)
        
def logMap(filename, formatstring):
    for log in logs(filename):
        print(log)





logMap(filename, formatstring = fs_uberspace)        
