#!/bin/bash
# shellcheck disable=SC2009

function yellow() { printf "\x1b[38;5;227m%s\e[0m " "${@}"; printf "\n"; };
function warn() { printf "\x1b[38;5;208m%s\e[0m " "${@}"; printf "\n"; };
function green() { printf "\x1b[38;5;048m%s\e[0m " "${@}"; printf "\n"; };
function red() { printf "\x1b[38;5;196m%s\e[0m " "${@}"; printf "\n"; };

if [[ "${DATE_FMT}" == "" ]]; then
    export DATE_FMT="%Y-%m-%dT%H:%M:%SZ"
fi

if [[ "${LOG_JOB_NAME}" == "" ]]; then
    export LOG_JOB_NAME="${0}"
fi

if [[ "${VERBOSE}" == "" ]]; then
    export VERBOSE=0
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

function show_diagnostics() {
    yellow "----------------------"
    pwd
    banner_log "listing contents of the current directory:"
    ls -lrt
    banner_log "python version:"
    which python
    python --version
    banner_log "env list for AWS credentials:"
    env | sort | grep AWS
    banner_log "aws version:"
    which aws
    /usr/local/bin/aws --version
    banner_log "getting aws identity:"
    aws sts get-caller-identity
    yellow "----------------------"
} # show_diagnostics - end

function load_aws_env_vars() {
    # the docker compose script may inject empty strings - make sure to unset the empty ones
    if [[ "${AWS_ACCESS_KEY_ID}" == "" ]]; then
        unset AWS_ACCESS_KEY_ID
    fi
    if [[ "${AWS_SECRET_ACCESS_KEY}" == "" ]]; then
        unset AWS_SECRET_ACCESS_KEY
    fi
} # load_aws_env_vars - end

function load_python_runtime() {
    var_path_to_venv="/opt/venv/bin/activate"
    source "${var_path_to_venv}"
    var_last_status="$?"
    if [[ "${var_last_status}" -ne 0 ]]; then
        err "failed to load python virtualenv with command:"
        echo "source ${var_path_to_venv}"
        exit 1
    fi
    if [[ "${VERBOSE}" -ne 0 ]]; then
        echo ""
        crit "python path and installed pips:"
        which python
        pip list
        echo ""
    fi
} # load_python_runtime - end

function load_env() {
    load_aws_env_vars
    load_python_runtime
} # load_env - ned

function start_aws_xray_daemon() {
    info "start - xray daemon - https://docs.aws.amazon.com/xray/latest/devguide/xray-daemon-configuration.html"
    cd /tmp || return
    # -o => local mode no EC2 instance metadata
    # -l => log level
    # -f => log file
    # -n => region
    local var_command="nohup xray -o -l debug -f /tmp/xray.log -n ${AWS_DEFAULT_REGION} > /tmp/nohup-xray.log 2>&1 &"
    info "starting xray daemon XRAY_SERVICE_NAME=${XRAY_SERVICE_NAME} with command: ${var_command}"
    eval "${var_command}"
    sleep 2
    var_num_pids=$(pgrep -c xray)
    var_last_status="$?"
    if [[ "${var_last_status}" -ne 0 ]]; then
        err "failed finding a running xray daemon with command: ${var_command} - stopping"
        exit 1
    elif [[ "${var_num_pids}" -ne 1 ]]; then
        err "failed starting xray daemon with command: ${var_command} - stopping"
        exit 1
    else
        info "xray daemon is running"
        # SC2009
        ps auwwx | grep -v grep | grep xray
    fi
    info "done - xray daemon"
} # start_aws_xray_daemon - end

function start_app() {
    info "start - app"
    cd /opt/stack || return
    python application.py
    info "done - app"
} # start_app - end

function run_main() {
    info "main - begin"
    if [[ "${XRAY_DAEMON_ENABLED}" == "1" ]]; then
        start_aws_xray_daemon
    else
        info "main - xray daemon skipped"
    fi
    start_app
    info "main - end"
} # run_main - end

load_env

if [[ "${VERBOSE}" -ne 0 ]]; then
    show_diagnostics
fi

run_main

green "done"

exit 0
