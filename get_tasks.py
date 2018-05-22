import sys
import json


import argparse

import uccaapp as ua
import uccaapp.api as uapi



server_address = "http://ucca.development.cs.huji.ac.il"
project = 92
source = 16

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ids', type=str)
    parser.add_argument('-f', '--file', type=str)
    parser.add_argument('-n', '--username', type=str)
    parser.add_argument('-p', '--password', type=str)
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


    print(json.dumps(d, indent=True))



if __name__ == "__main__":
    main()
