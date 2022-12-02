#!/bin/bash

CRON_RESULT_FILE="/opt/snmp_monitoring/snmp_extend/get_days_until_local_cert_exp/get_days_until_local_cert_exp.cron.result"
# Using for syncronize access between extend (reader) and cron (writer) scripts.
CRON_RESULT_TMP_FILE="$CRON_RESULT_FILE.tmp"
NUMBER_OF_SEC_IN_DAY="86400"

function update_cron_tmp_file {
	cat << EOL > $CRON_RESULT_TMP_FILE
LOCAL_CERT="$1"
DAYS_REMAIN="$2"
TIMESTAMP="$3"
EOL
    # Atomic operation.
    mv $CRON_RESULT_TMP_FILE $CRON_RESULT_FILE
}

function cert_mgr_show {
    
    local CERT_INDEX="$1"
	local RETRY_COUNT="3"
	local RETRY_TIMEOUT="10" # Seconds.
	local RESULT=""
	local COUNTER="0"

	while [[ $COUNTER -lt $RETRY_COUNT ]]; do
		if [[ $CERT_INDEX == "" ]]; then
			CERT_INFO=$(cert_mgr show)
			RESULT="$?"
		else
			CERT_INFO=$(cert_mgr show -i $1)
			RESULT="$?"
		fi 

		if [[ $RESULT -eq 0 ]]; then
			echo "$CERT_INFO"
			return 0
		fi

		((COUNTER++))
		sleep $RETRY_TIMEOUT
	done

	return 1
}

current_date=$(date)

cert_list=$(cert_mgr_show)
RESULT="$?"
if [[ $RESULT -ne 0 ]]; then
	exit 1
fi

# Get local certificate id. If there are several local certs, get the highest id.
cert_id=$(echo "$cert_list" | grep -oP "(\d+)(?=\s+Status: local)" | tail -n 1)

# If local certificate does not exist.
if [[ -z "$cert_id" ]]; then
	update_cron_tmp_file "0" "NULL" "$current_date"
	exit 0
fi

# Get the expiration date of local certificate.
cert_details=$(cert_mgr_show "$cert_id")
RESULT="$?"
if [[ $RESULT -ne 0 ]]; then
	exit 1
fi

# Example of $cert_expire_date is: "Sun Aug 23 14:17:52 2020".
cert_expire_date=$(echo "$cert_details" | grep -oP "Valid to:\s+\K(.*)")

# Convert current date and expire date to seconds and calculate difference.
current_sec=$(date -d "$current_date" +%s)
expire_sec=$(date -d "$cert_expire_date" +%s)
diff_sec=$(($expire_sec - $current_sec))

diff_days=$((diff_sec / NUMBER_OF_SEC_IN_DAY))

update_cron_tmp_file "1" "$diff_days" "$current_date"

exit 0