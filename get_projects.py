import sys
import json
import os

import argparse
from requests.exceptions import HTTPError

import uccaapp as ua
import uccaapp.api as uapi



server_address = "http://ucca.development.cs.huji.ac.il"
project = 92
source = 16

def main():

    parser = argparse.ArgumentParser(description='Download user tasks from UCCAApp according to a list of project IDs (either as a space-separated list with --ids, or as a file, one ID per line, with --file). Outputs retrieved tasks in JSON format, which can be further processed using tabulate.py.')
    parser.add_argument('-i', '--ids', type=str)
    parser.add_argument('-f', '--file', type=str)
    parser.add_argument('-o', '--out', default='.', type=str)
    parser.add_argument('username', type=str)
    parser.add_argument('password', type=str)
    args = parser.parse_args()
    
    server_accessor = uapi.ServerAccessor(server_address=server_address, \
            email=args.username, password=args.password, \
            auth_token="", project_id=project, source_id=source,\
                                          verbose=False)

    ids = []
    if args.file:
        with open(args.file) as f:
            for line in f:
                line = line.strip()
                ids.append(line.split()[0].strip())

    elif args.ids:
        ids = args.ids.split()
        

    errors = {}

    for ID in ids:
        try:
            proj_id = int(ID)
        except ValueError:
            continue

        # if dir PROJ not existent, create dir PROJ
        proj_dir = f'{args.out}/{proj_id}'
        if not os.path.exists(proj_dir):
            os.makedirs(proj_dir)
        tasks_dir = f'{proj_dir}/tasks'
        if not os.path.exists(tasks_dir):
            os.makedirs(tasks_dir)

        try:
            proj = server_accessor.get_project(proj_id)
        except HTTPError as e:
            errors[proj_id] = e
            continue

        with open(f'{proj_dir}/{proj_id}.json', 'w') as f:
            json.dump(proj, f, indent=2)
        
        for task in proj['tasks']:
            task_id = task['id']

            try:
                user_task = server_accessor.get_user_task(task_id)
            except HTTPError as e:
                errors[task_id] = e
                continue
                
            with open(f'{tasks_dir}/{task_id}.json', 'w') as f:
                json.dump(user_task, f, indent=2)




if __name__ == "__main__":
    main()
