import sys
import json
import os

import argparse
import logging
from requests.exceptions import HTTPError


import uccaapp as ua
import uccaapp.api as uapi



# server_address = "http://ucca.development.cs.huji.ac.il"
# server_address = "http://ucca.staging.cs.huji.ac.il"

# project = 11
source = 16

def main():

    logging.basicConfig(filename='get_projects.log', level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s: %(message)s')

    logging.info('###################################')
    logging.info('#             NEW RUN             #')
    logging.info('###################################')
    
    parser = argparse.ArgumentParser(description='Download user tasks from UCCAApp according to a list of project IDs (either as a space-separated list with --ids, or as a file, one ID per line, with --file). Outputs retrieved tasks in JSON format, which can be further processed using tabulate.py.')
    parser.add_argument('-i', '--ids', type=str)
    parser.add_argument('-f', '--file', type=str)
    parser.add_argument('-o', '--out', default='.', type=str)
    parser.add_argument('-a', '--address', default='staging', type=str, help='which ucca server? {staging, development}')
    parser.add_argument('username', type=str)
    parser.add_argument('password', type=str)
    args = parser.parse_args()

    server_address = f"http://ucca.{args.address}.cs.huji.ac.il"
    
    ids = []
    if args.file:
        with open(args.file) as f:
            for line in f:
                line = line.strip()
                ids.append(line.split()[0].strip())

    elif args.ids:
        ids = args.ids.split()

    project = int(ids[0])

    server_accessor = uapi.ServerAccessor(server_address=server_address, \
                                          email=args.username, password=args.password, \
                                          auth_token="", project_id=project, source_id=source,\
                                          verbose=False)

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

        logging.info(f'Attempting to access project {proj_id}...')
        try:
            proj = server_accessor.get_project(proj_id)
        except HTTPError as e:
            errors[proj_id] = e
            logging.warning(f'Failed to access project {proj_id} :\t{e}')
            continue

        logging.info('Success')
        with open(f'{proj_dir}/{proj_id}.json', 'w') as f:
            json.dump(proj, f, indent=2)
        
        for task in proj['tasks']:
            task_id = task['id']

            logging.info(f'Attempting to access task {task_id}...')
            try:
                user_task = server_accessor.get_user_task(task_id)
            except HTTPError as e:
                try:
                    task = server_accessor.get_task(task_id)
                    task["is_active"] = True
                    outp = server_accessor.request("put", "tasks/%d/" % task_id, json=task).json()

                except Exception as e:
                    errors[task_id] = e
                    logging.warning(f'Failed to access task {task_id} :\t{e}')
                    continue

            logging.info('Success')
            with open(f'{tasks_dir}/{task_id}.json', 'w') as f:
                json.dump(user_task, f, indent=2)




if __name__ == "__main__":
    main()
