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

function run_main() {
    info "run_main - begin"

    var_test_idx=1
    var_use_endpoint="0.0.0.0:5000"
    if [[ "${LISTEN_ADDRESS}" != "" ]]; then
        var_use_endpoint="${LISTEN_ADDRESS}"
    fi
    var_use_transport="http"
    var_use_url="${var_use_transport}://${var_use_endpoint}"

    var_not_done=0
    var_cur_loop=1
    var_num_loops=10

    while [[ "${var_not_done}" -eq 0 ]]; do
        var_command="curl -iivv '${var_use_url}'"
        header_log "loop=${var_cur_loop} test=${var_test_idx} running default healthcheck: ${var_command}"
        eval "${var_command}"
        var_test_idx=$(( var_test_idx + 1 ))
        echo ""

        var_command="curl -iivv '${var_use_url}/outgoing-http-call'"
        header_log "loop=${var_cur_loop} test=${var_test_idx} running outgoing-http-call: ${var_command}"
        eval "${var_command}"
        var_test_idx=$(( var_test_idx + 1 ))
        echo ""

        var_command="curl -iivv '${var_use_url}/aws-sdk-call'"
        header_log "loop=${var_cur_loop} test=${var_test_idx} running aws-sdk-call: ${var_command}"
        eval "${var_command}"
        var_test_idx=$(( var_test_idx + 1 ))
        echo ""

        var_command="curl -iivv '${var_use_url}/flask-sql-alchemy-call'"
        header_log "loop=${var_cur_loop} test=${var_test_idx} running flask-sql-alchemy: ${var_command}"
        eval "${var_command}"
        var_test_idx=$(( var_test_idx + 1 ))
        echo ""

        var_command="curl -iivv '${var_use_url}/aws-sdk-call' -d '{\"bucket\":\"notrealbucket\"}'"
        header_log "loop=${var_cur_loop} test=${var_test_idx} running error test on aws-sdk-call: ${var_command}"
        eval "${var_command}"
        var_test_idx=$(( var_test_idx + 1 ))
        echo ""

        var_command="curl -iivv '${var_use_url}/flask-sql-alchemy-call' -d '{\"username\":\"demouser\",\"email\":\"notreal@email.com\"}'"
        header_log "loop=${var_cur_loop} test=${var_test_idx} running error test on flask-sql-alchemy: ${var_command}"
        eval "${var_command}"
        var_test_idx=$(( var_test_idx + 1 ))
        echo ""

        var_cur_loop=$(( var_cur_loop + 1 ))
        if [[ "${var_cur_loop}" -gt "${var_num_loops}" ]]; then
            var_not_done=1
        fi
    done
    info "run_main - end"
} # run_main - end

run_main

exit 0
