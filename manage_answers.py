import yaml
import json
import requests
import argparse
import sys

from generator.var_generator import generate
from generator.var_parser import parser_var_file
from requests.exceptions import ConnectionError, HTTPError

VARIABLE_FILE_PATH = 'variables.yml'
HEADERS = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
}


class InventoryLoader(yaml.FullLoader):
    pass


InventoryLoader.add_constructor(
    '!unsafe', lambda loader, node: loader.construct_scalar(node))


def load_inventory_variables(inventory_path):
    with open(inventory_path, 'r') as file:
        return yaml.load(file, Loader=InventoryLoader)['all']['vars']


def create_answers_file(generated_answers, answers_file_path):
    with open(answers_file_path, 'w') as file:
        json.dump(generated_answers, file)


def generate_answers(inventory_variables):
    pool_id = inventory_variables['global_pool_id']
    sandbox_id = inventory_variables['global_sandbox_allocation_unit_id']
    seed = (pool_id + sandbox_id) * 31

    with open(VARIABLE_FILE_PATH, 'r') as file:
        variable_list = parser_var_file(file)

    return generate(variable_list, seed)


def get_post_data_json(sandbox_id, allocation_id, generated_answers):
    post_data = {
        'sandbox_ref_id': sandbox_id,
        'allocation_unit_id': allocation_id,
        'sandbox_answers': []
    }

    for key, item in generated_answers.items():
        post_data['sandbox_answers'].append({
            'answer_content': item,
            'answer_variable_name': key
        })

    return json.dumps(post_data, indent=4)


def delete_answers(answers_storage_api, allocation_id):
    requests.delete(answers_storage_api + 'sandboxes/' + str(allocation_id)).raise_for_status()


def post_answers(answers_storage_api, sandbox_id, allocation_id, generated_answers):
    post_data_json = get_post_data_json(sandbox_id, allocation_id, generated_answers)
    post_response = requests.post(answers_storage_api + 'sandboxes',
                                  data=post_data_json, headers=HEADERS)
    post_response.raise_for_status()


def get_answers(answers_storage_api, sandbox_id):
    get_response = requests.get(answers_storage_api + 'sandboxes/' + sandbox_id + '/answers',
                                headers=HEADERS)
    if get_response.status_code == 404:
        return None
    get_response.raise_for_status()
    return {
        answer['answer_variable_name']: answer['answer_content']
        for answer in get_response.json()['sandbox_answers']
    }


def get_or_create_answers(inventory_variables, answers_storage_api, sandbox_id, allocation_id):
    """
    Return the answers stored for the sandbox and whether this call stored them.

    A restarted user stage runs again for the same sandbox, whose answers the
    first run already stored. Trainees are checked against the stored answers,
    so the playbook gets those rather than freshly generated ones.
    """
    stored_answers = get_answers(answers_storage_api, sandbox_id)
    if stored_answers is not None:
        return stored_answers, False

    generated_answers = generate_answers(inventory_variables)
    try:
        post_answers(answers_storage_api, sandbox_id, allocation_id, generated_answers)
    except HTTPError as exc:
        if exc.response is None or exc.response.status_code != 409:
            raise
        stored_answers = get_answers(answers_storage_api, sandbox_id)
        if stored_answers is None:
            # answers-storage answers 404 for a sandbox stored with no answers.
            if generated_answers:
                raise
            stored_answers = {}
        return stored_answers, False
    return generated_answers, True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inventory_path')
    parser.add_argument('answers_file_path')
    parser.add_argument('answers_storage_api')
    parser.add_argument('--cleanup', action='store_true')

    args = parser.parse_args()
    inventory_variables = load_inventory_variables(args.inventory_path)
    sandbox_id = inventory_variables['global_sandbox_id']
    allocation_id = inventory_variables['global_sandbox_allocation_unit_id']
    answers_file_path = args.answers_file_path
    answers_storage_api = args.answers_storage_api

    _success_msg = "\n[OK]: Successful {} upon answers-storage container.\n"
    _request_error_msg = "\n[WARNING]: Failed {} upon answers-storage container." \
                         "Status code {}.\n"

    try:
        if args.cleanup:
            delete_answers(answers_storage_api, allocation_id)
            print(_success_msg.format('DELETE'))
            return

        answers, created = get_or_create_answers(
            inventory_variables, answers_storage_api, sandbox_id, allocation_id)
        create_answers_file(answers, answers_file_path)
        print(_success_msg.format('POST' if created else 'GET'))
    except ConnectionError:
        print('\n[Warning]: Service answers-storage is unavailable.\n')
        sys.exit(1)
    except HTTPError as exc:
        print(_request_error_msg.format(exc.request.method, exc.response))
        sys.exit(1)


if __name__ == '__main__':
    main()
