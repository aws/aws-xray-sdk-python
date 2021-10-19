#!/bin/bash

function yellow() { printf "\x1b[38;5;227m%s\e[0m " "${@}"; printf "\n"; };
function warn() { printf "\x1b[38;5;208m%s\e[0m " "${@}"; printf "\n"; };
function green() { printf "\x1b[38;5;048m%s\e[0m " "${@}"; printf "\n"; };
function red() { printf "\x1b[38;5;196m%s\e[0m " "${@}"; printf "\n"; };

var_container_name="demo-xpy"
var_compose="./compose.yml"

if [[ "${DATE_FMT}" == "" ]]; then
    export DATE_FMT="%Y-%m-%dT%H:%M:%SZ"
fi

if [[ "${LOG_JOB_NAME}" == "" ]]; then
    export LOG_JOB_NAME="${var_container_name}"
fi

# set custom aws credentials at deploy-time
if [[ "${AWS_DEFAULT_REGION}" == "" ]]; then
    export AWS_DEFAULT_REGION=""
fi

if [[ "${AWS_ACCESS_KEY_ID}" == "" ]]; then
    export AWS_ACCESS_KEY_ID=""
fi

if [[ "${AWS_SECRET_ACCESS_KEY}" == "" ]]; then
    export AWS_SECRET_ACCESS_KEY=""
fi

if [[ "${AWS_SHARED_CREDENTIALS_FILE}" == "" ]]; then
    export AWS_SHARED_CREDENTIALS_FILE=""
fi

if [[ "${AWS_CONFIG_FILE}" == "" ]]; then
    export AWS_CONFIG_FILE=""
fi

function info() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} - ${LOG_JOB_NAME} - INFO ${*}"
    echo "${log_str}"
} # info - end

function err() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} - ${LOG_JOB_NAME} - ERROR ${*}"
    red "${log_str}"
} # err - end

function trace() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} - ${LOG_JOB_NAME} - TRACE ${*}"
    if [[ ${VERBOSE} -ne 0 ]]; then
        echo "${log_str}"
    fi
} # trace - end

function crit() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} - ${LOG_JOB_NAME} - CRITICAL ${*}"
    yellow "${log_str}"
} # crit - end

function good() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} - ${LOG_JOB_NAME} - SUCCESS ${*}"
    green "${log_str}"
} # good - end

function banner_log() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} - ${LOG_JOB_NAME} - BANNER ${*}"
    yellow "${log_str}"
} # banner_log - end

function header_log() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} - ${LOG_JOB_NAME} - HEADER ${*}"
    yellow "${log_str}"
} # header_log - end

if [[ "${AWS_ACCESS_KEY_ID}" == "" ]] && [[ "${AWS_SECRET_ACCESS_KEY}" == "" ]] && [[ "${AWS_SHARED_CREDENTIALS_FILE}" == "" ]] && [[ "${AWS_CONFIG_FILE}" == "" ]]; then
    err "missing AWS credentials for: AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY or using AWS_SHARED_CREDENTIALS_FILE + AWS_CONFIG_FILE - stopping"
    exit 1
else
    if [[ "${AWS_ACCESS_KEY_ID}" == "" ]] && [[ "${AWS_SECRET_ACCESS_KEY}" == "" ]]; then
        if [[ -e "${AWS_SHARED_CREDENTIALS_FILE}" ]]; then
            var_cred_data=$(cat "${AWS_SHARED_CREDENTIALS_FILE}")
            var_aws_access_key=$(echo "${var_cred_data}" | grep aws_access_key_id | awk '{print $NF}')
            var_aws_secret_key=$(echo "${var_cred_data}" | grep aws_secret_access_key | awk '{print $NF}')
            export AWS_ACCESS_KEY_ID="${var_aws_access_key}"
            export AWS_SECRET_ACCESS_KEY="${var_aws_secret_key}"
        fi
    fi
fi

if [[ "${AWS_DEFAULT_REGION}" == "" ]]; then
    if [[ -e "${AWS_CONFIG_FILE}" ]]; then
        var_aws_config_data=$(cat "${AWS_CONFIG_FILE}")
        var_aws_region=$(echo "${var_aws_config_data}" | grep region | awk '{print $NF}')
        export AWS_DEFAULT_REGION="${var_aws_region}"
    fi
fi

if [[ "${AWS_ACCESS_KEY_ID}" == "" ]] && [[ "${AWS_SECRET_ACCESS_KEY}" == "" ]]; then
    err "unable to detect valid AWS credentials for: AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY - please set up your AWS credentials and try again - stopping"
    exit 1
fi
if [[ "${AWS_DEFAULT_REGION}" == "" ]]; then
    err "unable to detect valid AWS region - please set up your AWS credentials and try again - stopping"
    exit 1
fi

var_test_if_running=$(docker ps -a | grep -c "${var_container_name}")
if [[ "${var_test_if_running}" -ne 0 ]]; then
    header_log "stopping previous deployment"
    docker-compose -f ${var_compose} down > /dev/null 2>&1
    docker rm "${var_container_name}" > /dev/null 2>&1
fi

header_log "starting docker compose: ${var_compose}"
var_command="docker-compose -f ${var_compose} up -d"
eval "${var_command} 2> /dev/null"
var_last_status="$?"
if [[ "${var_last_status}" -ne 0 ]]; then
    err "failed to start docker compose with command: "
    echo "${var_command}"
    exit 1
fi

info "sleeping before getting logs"
sleep 5

crit "----------------------------------"
docker logs "${var_container_name}"
var_last_status="$?"
if [[ "${var_last_status}" -ne 0 ]]; then
    err "failed to get docker logs with command: "
    echo "docker logs ${var_container_name}"
    exit 1
fi

exit 0
