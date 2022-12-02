#!/bin/bash

set -eu

CRON_RESULT_FILE="/opt/snmp_monitoring/snmp_extend/get_days_until_local_cert_exp/get_days_until_local_cert_exp.cron.result"

# Import the variables: LOCAL_CERT, DAYS_REMAIN and TIMESTAMP.
source $CRON_RESULT_FILE

# Set threshold value in seconds. If time difference between current date and the timestamp in result file is bigger than this value, we count it as outdated.
THRESHOLD=86400

if [[ $LOCAL_CERT -eq 0 ]]; then
	exit 4
fi

if [[ $DAYS_REMAIN -lt 0 ]]; then
	echo 0
	exit 2
fi

current_date=$(date)

current_sec=$(date -d "$current_date" +%s)
timestamp_sec=$(date -d "$TIMESTAMP" +%s)
diff_sec=$((current_sec - timestamp_sec))

if [[ $diff_sec -gt $THRESHOLD ]]; then
	exit 3
fi

echo $DAYS_REMAIN
exit 0