import sys
import json


import argparse

import uccaapp as ua
import uccaapp.api as uapi



server_address = "http://ucca.development.cs.huji.ac.il"
#server_address = "http://ucca.staging.cs.huji.ac.il"
project = 95 # 11 # 92
source = 12 # 16

def main():

    parser = argparse.ArgumentParser(description='Download user tasks from UCCAApp according to a list of task IDs (either as a space-separated list with --ids, or as a file, one ID per line, with --file). Outputs retrieved tasks in JSON format, which can be further processed using tabulate.py.')
    parser.add_argument('-i', '--ids', type=str)
    parser.add_argument('-f', '--file', type=str)
    parser.add_argument('username', type=str)
    parser.add_argument('password', type=str)
    args = parser.parse_args()
    
    server_accessor = uapi.ServerAccessor(server_address=server_address, \
            email=args.username, password=args.password, \
            auth_token="", project_id=project, source_id=source,\
                                          verbose=False)

    d = {}
    ids = []
    if args.file:
        with open(args.file) as f:
            for line in f:
                line = line.strip()
                ids.append(line)

    elif args.ids:
        ids = args.ids.split()
        
    for ID in ids:
        try:
            task_id = int(ID)
        except ValueError:
            continue
            
        task = server_accessor.get_user_task(task_id)
        d[task_id] = task


    #for task in d.values():
    #    print(json.dumps(task, indent=2))

    print(json.dumps(list(d.values()), indent=2))


if __name__ == "__main__":
    main()
