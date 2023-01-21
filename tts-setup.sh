#!/bin/bash
#
set -e

export PROJECT_ID=$(gcloud config get-value core/project)

if [ -z "$PROJECT_ID" ]; then
	echo "You must set up a GCP account and project, see: https://developers.google.com/workspace/guides/create-project"
	exit 1;
fi

echo "Using $PROJECT_ID"

if [ ! -e tts-sa-key.json ]; then
	gcloud iam service-accounts create my-tts-sa \
	  --display-name "language learn tts service account"
	gcloud projects add-iam-policy-binding ${PROJECT_ID} \
	  --member serviceAccount:my-tts-sa@${PROJECT_ID}.iam.gserviceaccount.com \
	  --role roles/serviceusage.serviceUsageConsumer
	gcloud iam service-accounts keys create ./tts-sa-key.json \
	  --iam-account my-tts-sa@${PROJECT_ID}.iam.gserviceaccount.com
fi
export GOOGLE_APPLICATION_CREDENTIALS=`pwd`/tts-sa-key.json
