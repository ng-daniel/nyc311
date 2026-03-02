exp () {
    set -a
    source "$1"
    set +a
}

exp "./.env"
printenv | grep "DBT"