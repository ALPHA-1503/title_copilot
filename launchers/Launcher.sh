#!/bin/bash

PORT=22028
SSH_COMMAND="ssh -N -f -p 22002 user@idaho-b.tensordockmarketplace.com -i ~/.ssh/id_rsa_tensordock -L 22028:localhost:8000"

check_port() {
  local PORT=$1
  if nc -zv localhost "$PORT" 2>&1 | grep -q 'succeeded'; then
    echo "Port $PORT is open on localhost"
    return 0
  else
    echo "Port $PORT is closed on localhost"
    return 1
  fi
}

check_port $PORT
PORT_STATUS=$?


if [ $PORT_STATUS -ne 0 ]; then
  echo "One or both ports are closed. Running SSH command..."
  $SSH_COMMAND
  if [ $? -eq 0 ]; then
    echo "SSH command successful."
  else
    echo "Error: SSH command failed with exit code $?."
    echo "One or both remote virtual machine are probably not running."
  fi
fi



screen -dmS title_copilot bash -c 'python3 -m venv .venv; pip install -r requirements.txt -q; source .venv/bin/activate; python3 ./scripts/before_code.py; python3 ./App.py; exec bash'
echo "Screen session 'title_copilot' started. Run 'screen -r title_copilot' to attach to the session and CTRL + A + D to detach from the session."
echo -e "\033[0;32mWarning! CTRL + D will kill the screen session.\033[0m"

