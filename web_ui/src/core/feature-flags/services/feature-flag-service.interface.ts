// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/*
    IMPORTANT:
    - These feature flags are used when during development (`NODE_ENV === 'development'`).
    their keys are also used to determine which feature flags are supported on the frontend,
    if we want to add a new feature flag we should add it here as well as in the backend
    (src/installer/platform_installer/constants/feature_flags.py).
    Feature flags on both files should always have the same values.

*/
export const DEV_FEATURE_FLAGS = {
    FEATURE_FLAG_NEW_FEATURE: process.env.REACT_APP_FEATURE_FLAG_NEW_FEATURE === 'true',

    FEATURE_FLAG_ANALYTICS_WORKFLOW_ID: false,
    FEATURE_FLAG_WORKSPACE_ACTIONS: false,
    FEATURE_FLAG_CAMERA_VIDEO_UPLOAD: false,
    FEATURE_FLAG_USER_ONBOARDING: false,
    FEATURE_FLAG_FREE_TIER: false,
    FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: true,
    FEATURE_FLAG_ALLOW_EXTERNAL_KEY_PROJECT_IMPORT: false,
    FEATURE_FLAG_LICENSE_VALIDATION: false,
    FEATURE_FLAG_CREDIT_SYSTEM: true,
    FEATURE_FLAG_ORG_QUOTAS: false,
    FEATURE_FLAG_ANOMALY_REDUCTION: true,
    FEATURE_FLAG_VISUAL_PROMPT_SERVICE: true,
    FEATURE_FLAG_CLASSIFICATION_RANGES: true,
    FEATURE_FLAG_MAINTENANCE_BANNER: false,
    FEATURE_FLAG_KEYPOINT_DETECTION: false,
    FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE: false,
    FEATURE_FLAG_OVMS_DEPLOYMENT_PACKAGE: true,
    FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK: false,
    FEATURE_FLAG_MANAGE_USERS: false,
    FEATURE_FLAG_MANAGE_USERS_ROLES: false,
    FEATURE_FLAG_REQ_ACCESS: false,
    FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS: false,
    FEATURE_FLAG_TELEMETRY_STACK: true,

    // Only used for unit testing
    DEBUG: false,
};

export type FeatureFlags = Record<keyof typeof DEV_FEATURE_FLAGS, boolean>;
export type CustomFeatureFlags = Partial<FeatureFlags>;

export interface FeatureFlagService {
    getFeatureFlags: () => Promise<FeatureFlags>;
}
