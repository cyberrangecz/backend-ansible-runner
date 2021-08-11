#!/usr/bin/env bash

usage() { echo "kypo-ansible-runner.sh -r [git repo url] -i [inventory file path]"; }

while getopts ":u:r:i:h" opt; do
  case ${opt} in
  u) REPO_URL=$OPTARG ;;
  r) REVISION=$OPTARG ;;
  i) INVENTORY=$OPTARG ;; # realpath -e on some systems
  h)
    usage
    exit
    ;;
  \?)
    echo "Unknown option: -$OPTARG" >&2
    exit 1
    ;;
  :)
    echo "Missing option argument for -$OPTARG" >&2
    exit 1
    ;;
  *)
    echo "Unimplemented option: -$OPTARG" >&2
    exit 1
    ;;
  esac
done

if ((OPTIND == 1)); then
  echo "No options specified"
  exit 1
fi
shift $((OPTIND - 1))

chmod 600 /root/.ssh -R
chown root:root /root/.ssh -R

# Check if inventory file exists.
INVENTORY_FILE=$(realpath $INVENTORY)
if [ $? != 0 ]; then
  echo "Inventory file does not exist. Exiting."
  exit 1
fi

# Check if git repo is reachable.
git ls-remote $REPO_URL -q
if [ $? != 0 ]; then
  echo "Git repository unreachable. Git exit code: ${REPO_TEST}. Exiting."
  exit 1
fi

git clone $REPO_URL ansible_repo || exit 1
cd ansible_repo || exit 1
if [ $REVISION ]; then
  git checkout $REVISION || exit 1
fi

ANSWERS_FILE=$(realpath 'answers.json')
echo {} > "$ANSWERS_FILE"

VARIABLES_FILE='variables.yml'
PREPARE_ANSWERS_PY='../manage_answers.py'
if [ -f $VARIABLES_FILE ]; then
  python3.8 "$PREPARE_ANSWERS_PY" "$INVENTORY_FILE" "$ANSWERS_FILE"
fi

git submodule update --init --recursive || exit 1
cd provisioning || exit 1

REQUIREMENTS_FILE="requirements.yml"
if [ -f $REQUIREMENTS_FILE ]; then
  ansible-galaxy install -r $REQUIREMENTS_FILE -p roles || exit 1
fi

autossh -M 12234 -f -N -D 12345 man

PRE_PLAYBOOK_FILE="pre-playbook.yml"
if [ -f $PRE_PLAYBOOK_FILE ]; then
  ansible-playbook $PRE_PLAYBOOK_FILE -i "${INVENTORY_FILE}" -vv || exit "$?"
  ANSIBLE_ERROR=$?
  if [ "$ANSIBLE_ERROR" != 0 ]
  then
    exit $ANSIBLE_ERROR
  fi
fi

PLAYBOOK_FILE="playbook.yml"
ansible-playbook $PLAYBOOK_FILE -i "${INVENTORY_FILE}" -e "@$ANSWERS_FILE" -vv || exit "$?"
