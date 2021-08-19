import yaml
import json
import requests
import argparse

from generator.var_generator import generate
from generator.var_parser import parser_var_file
from requests.exceptions import ConnectionError, HTTPError

VARIABLE_FILE_PATH = 'variables.yml'
HEADERS = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
}


def load_inventory_variables(inventory_path):
    with open(inventory_path, 'r') as file:
        return yaml.full_load(file)['all']['vars']


def create_answers_file(generated_answers, answers_file_path):
    with open(answers_file_path, 'w') as file:
        json.dump(generated_answers, file)


def generate_answers(inventory_variables):
    pool_id = inventory_variables['kypo_global_pool_id']
    sandbox_id = inventory_variables['kypo_global_sandbox_allocation_unit_id']
    seed = (pool_id + sandbox_id) * 31

    with open(VARIABLE_FILE_PATH, 'r') as file:
        variable_list = parser_var_file(file)

    return generate(variable_list, seed)


def get_post_data_json(sandbox_id, generated_answers):
    post_data = {
        'sandbox_ref_id': sandbox_id,
        'sandbox_answers': []
    }

    for key, item in generated_answers.items():
        post_data['sandbox_answers'].append({
            'answer_content': item,
            'answer_variable_name': key
        })

    return json.dumps(post_data, indent=4)


def get_answers(answers_storage_api, sandbox_id):
    return requests.get(answers_storage_api + '/sandboxes/' + str(sandbox_id) + '/answers')


def delete_answers(answers_storage_api, sandbox_id):
    requests.delete(answers_storage_api + '/sandboxes/' + str(sandbox_id)).raise_for_status()


def post_answers(answers_storage_api, sandbox_id, generated_answers):
    post_data_json = get_post_data_json(sandbox_id, generated_answers)
    post_response = requests.post(answers_storage_api + '/sandboxes',
                                  data=post_data_json, headers=HEADERS)
    post_response.raise_for_status()


def manage_answers(inventory_variables, generated_answers, answers_storage_api):
    sandbox_id = inventory_variables['kypo_global_sandbox_allocation_unit_id']
    if get_answers(answers_storage_api, sandbox_id).status_code == 404:
        post_answers(answers_storage_api, sandbox_id, generated_answers)
        return 'post'
    else:
        delete_answers(answers_storage_api, sandbox_id)
        return 'delete'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inventory_path')
    parser.add_argument('answers_file_path')
    parser.add_argument('answers_storage_api')

    args = parser.parse_args()
    inventory_variables = load_inventory_variables(args.inventory_path)
    answers_file_path = args.answers_file_path
    answers_storage_api = args.answers_storage_api

    generated_answers = generate_answers(inventory_variables)
    create_answers_file(generated_answers, answers_file_path)
    try:
        operation = manage_answers(inventory_variables, generated_answers, answers_storage_api)
        print(f'\n[OK]: Operation [{operation}] upon answers-storage container was successful.\n')
    except ConnectionError:
        print('\n[Warning]: Service answers-storage is unavailable.\n')
    except HTTPError as exc:
        print(f'\n[Warning]: Unable to send generated answers to kypo-answers-storage service,'
              f' status code {exc.response}.\n')


if __name__ == '__main__':
    main()
