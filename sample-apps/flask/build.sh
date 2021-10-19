#!/bin/bash

var_maintainer="demo"
var_imagename="xpy"
var_tag="latest"

var_image_build_type="${1}"
var_extra_image_name="${2}"
if [[ "${var_image_build_type}" == "" ]]; then
    var_image_build_type="default"
fi

var_use_image_name="${var_maintainer}/${var_imagename}"

function yellow() { printf "\x1b[38;5;227m%s\e[0m " "${@}"; printf "\n"; }
function warn() { printf "\x1b[38;5;208m%s\e[0m " "${@}"; printf "\n"; }
function green() { printf "\x1b[38;5;048m%s\e[0m " "${@}"; printf "\n"; }
function red() { printf "\x1b[38;5;196m%s\e[0m " "${@}"; printf "\n"; }

export VERBOSE="0"
export DATE_FMT="%Y-%m-%dT%H:%M:%SZ"

if [[ "${USER}" == "" ]]; then
    var_cur_os_username=$(whoami)
    export USER="${var_cur_os_username}"
fi

# debug - only print if VERBOSE != 0
function debug() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} DEBUG ${*}"
    if [[ ${VERBOSE} -ne 0 ]]; then
        echo "${log_str}"
    fi
}

function info() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} INFO ${*}"
    if [[ ${VERBOSE} -ne 0 ]]; then
        echo "${log_str}"
    fi
}

function err() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} ERROR ${*}"
    red "${log_str}"
}

function tracked_log() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} INFO ${*}"
    echo "${log_str}"
}

function trace() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} TRACE ${*}"
    if [[ ${VERBOSE} -ne 0 ]]; then
        echo "${log_str}"
    fi
}

function crit() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} CRITICAL ${*}"
    warn "${log_str}"
}

function good() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} SUCCESS ${*}"
    if [[ ${SILENT} -eq 0 ]]; then
        green "${log_str}"
    fi
}

function banner_log() {
    cur_date="$(date -u +"${DATE_FMT}")"
    local log_str="${cur_date} HEADER ${*}"
    yellow "${log_str}"
}

banner_log "--------------------------------------------------------"
banner_log "building new docker image=${var_use_image_name}:${var_tag}"
docker build --rm -t "${var_use_image_name}" .
var_last_status=$?
if [[ "${var_last_status}" == "0" ]]; then
    tracked_log ""
    if [[ "${var_tag}" != "" ]]; then
        tracked_log "docker images | grep \"${var_use_image_name} \" | grep latest | awk '{print \$3}'"
        var_image_csum=$(docker images | grep "${var_use_image_name} " | grep latest | awk '{print $3}' | head -1)
        if [[ "${var_image_csum}" != "" ]]; then
            docker tag "${var_image_csum}" "${var_use_image_name}:${var_tag}"
            var_last_status=$?
            if [[ "${var_last_status}" != "0" ]]; then
                err "failed to tag image=${var_use_image_name} with tag=${var_tag} with command:"
                echo "docker tag ${var_image_csum} ${var_use_image_name}:${var_tag}"
                exit 1
            else
                tracked_log "build successful tagged image=${var_use_image_name} with tag=${var_tag}"
            fi

            if [[ "${var_extra_image_name}" != "" ]]; then
                tracked_log "setting the docker tag"
                tracked_log "docker tag ${var_image_csum} ${var_extra_image_name}"
                docker tag "${var_image_csum}" "${var_extra_image_name}"
                var_last_status=$?
                if [[ "${var_last_status}" != "0" ]]; then
                    err "failed to tag image=${var_use_image_name} with tag=${var_tag} with command:"
                    echo "docker tag ${var_image_csum} ${var_extra_image_name}"
                    exit 1
                else
                    tracked_log "added additional docker tag: ${var_extra_image_name}"
                fi
            fi
        else
            err "build failed to find latest image=${var_use_image_name} with tag=${var_tag}"
            exit 1
        fi
    fi
else
    err "build failed with exit code: ${var_last_status}"
    exit 1
fi

if [[ "${var_extra_image_name}" != "" ]]; then
    good "docker build successful build_type=${var_image_build_type} ${var_use_image_name}:${var_tag} extra_name=${var_extra_image_name}"
else
    good "docker build successful build_type=${var_image_build_type} ${var_use_image_name}:${var_tag}"
fi

exit 0
