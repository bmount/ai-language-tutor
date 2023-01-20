#!/bin/bash

export PROJECT_ID=$(gcloud config get-value core/project)
gcloud iam service-accounts create my-tts-sa \
  --display-name "language learn tts service account"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member serviceAccount:my-tts-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/serviceusage.serviceUsageConsumer
gcloud iam service-accounts keys create ./tts-sa-key.json \
  --iam-account my-tts-sa@${PROJECT_ID}.iam.gserviceaccount.com
export GOOGLE_APPLICATION_CREDENTIALS=`pwd`/tts-sa-key.json
