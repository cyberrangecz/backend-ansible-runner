import yaml
import json
import requests
import argparse

from generator.var_generator import generate
from generator.var_parser import parser_var_file
from requests.exceptions import ConnectionError

VARIABLE_FILE_PATH = 'variables.yml'
KYPO_ANSWERS_STORAGE_API_URL = 'http://answers-storage:8087/kypo-rest-answers-storage/api/v1'
HEADERS = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
}


def load_inventory_variables(inventory_path):
    with open(inventory_path, 'r') as file:
        return yaml.full_load(file)['all']['vars']


def create_answers_file(generated_answers, answers_path):
    with open(answers_path, 'w') as file:
        json.dump(generated_answers, file)


def generate_answers(inventory_variables):
    pool_id = inventory_variables['kypo_global_pool_id']
    sandbox_id = inventory_variables['kypo_global_sandbox_allocation_unit_id']
    seed = (pool_id + sandbox_id) * 43

    with open(VARIABLE_FILE_PATH, 'r') as file:
        variable_list = parser_var_file(file)

    return generate(variable_list, seed)


def get_post_data_json(inventory_variables, generated_answers):
    sandbox_id = inventory_variables['kypo_global_sandbox_allocation_unit_id']
    post_data = {
        'sandbox_ref_id': sandbox_id,
        'sandbox_answers': []
    }

    for key, item in generated_answers.items():
        post_data['sandbox_answers'].append({
            'answer_content': item,
            'answer_identifier': key
        })

    return json.dumps(post_data, indent=4)


def send_post_request(inventory_variables, generated_answers):
    post_data_json = get_post_data_json(inventory_variables, generated_answers)
    try:
        requests.post(KYPO_ANSWERS_STORAGE_API_URL + '/sandboxes', data=post_data_json,
                      headers=HEADERS)
    except ConnectionError:
        print('\n[Warning]: Service answers-storage is unavailable.\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('inventory_path')
    parser.add_argument('answers_path')

    args = parser.parse_args()
    inventory_variables = load_inventory_variables(args.inventory_path)

    generated_answers = generate_answers(inventory_variables)
    create_answers_file(generated_answers, args.answers_path)
    send_post_request(inventory_variables, generated_answers)


if __name__ == '__main__':
    main()
