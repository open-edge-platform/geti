# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
"""Module containing dict containing supported FEATURE_FLAGS for the platform"""

# IMPORTANT
# Adding, enabling or removing feature flags, please remember to make the same changes
# in the Application Stack repository! https://github.com/intel-innersource/applications.ai.geti.application-stack
FEATURE_FLAGS = {
    "FEATURE_FLAG_ACC_SVC_MOD": "false",
    "FEATURE_FLAG_ALLOW_EXTERNAL_KEY_PROJECT_IMPORT": "true",
    "FEATURE_FLAG_AMBIENT_MESH": "false",
    "FEATURE_FLAG_ANALYTICS_WORKFLOW_ID": "true",
    "FEATURE_FLAG_ANOMALY_REDUCTION": "true",
    "FEATURE_FLAG_ASYNCHRONOUS_MEDIA_PREPROCESSING": "false",
    "FEATURE_FLAG_CAMERA_VIDEO_UPLOAD": "false",
    "FEATURE_FLAG_CLASSIFICATION_RANGES": "true",
    "FEATURE_FLAG_CREDIT_SYSTEM": "false",
    "FEATURE_FLAG_DECORD_VIDEO_DECODER": "false",
    "FEATURE_FLAG_FP16_INFERENCE": "true",
    "FEATURE_FLAG_KEYPOINT_DETECTION": "false",
    "FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE": "false",
    "FEATURE_FLAG_MAINTENANCE_BANNER": "false",
    "FEATURE_FLAG_MANAGE_USERS": "false",
    "FEATURE_FLAG_MANAGE_USERS_ROLES": "true",
    "FEATURE_FLAG_OBJECT_STORAGE_OP": "true",
    "FEATURE_FLAG_OFFLINE_INSTALLATION": "true",
    "FEATURE_FLAG_OIDC_CIDAAS": "false",
    "FEATURE_FLAG_ORG_QUOTAS": "false",  # can be enabled only if FEATURE_FLAG_CREDIT_SYSTEM is enabled
    "FEATURE_FLAG_OTX_VERSION_SELECTION": "true",
    "FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE": "true",
    "FEATURE_FLAG_REQ_ACCESS": "false",
    "FEATURE_FLAG_RETAIN_TRAINING_ARTIFACTS": "false",
    "FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK": "true",
    "FEATURE_FLAG_STORAGE_SIZE_COMPUTATION": "true",
    "FEATURE_FLAG_SUPPORT_CORS": "false",
    "FEATURE_FLAG_USER_ONBOARDING": "false",
    "FEATURE_FLAG_VISUAL_PROMPT_SERVICE": "true",
    "FEATURE_FLAG_WORKSPACE_ACTIONS": "false",
}
