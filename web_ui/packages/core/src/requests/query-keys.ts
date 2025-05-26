// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    PredictionCache,
    PredictionMode,
} from '../../../../src/core/annotations/services/prediction-service.interface';
import { VideoPaginationOptions } from '../../../../src/core/annotations/services/video-pagination-options.interface';
import { TrainingConfigurationQueryParameters } from '../../../../src/core/configurable-parameters/services/api-model-config-parameters-service';
import { CreditAccountIdentifier } from '../../../../src/core/credits/credits.interface';
import {
    GetTransactionsAggregatesQueryOptions,
    GetTransactionsQueryOptions,
} from '../../../../src/core/credits/transactions/services/transactions-service.interface';
import { AdvancedFilterOptions, AdvancedFilterSortingOptions } from '../../../../src/core/media/media-filter.interface';
import { MediaIdentifier } from '../../../../src/core/media/media.interface';
import { VideoIdentifier } from '../../../../src/core/media/video.interface';
import { ModelGroupIdentifier, ModelIdentifier } from '../../../../src/core/models/models.interface';
import { OrganizationIdentifier } from '../../../../src/core/organizations/organizations.interface';
import { GetOrganizationsQueryOptions } from '../../../../src/core/organizations/services/organizations-service.interface';
import { DOMAIN, ProjectIdentifier } from '../../../../src/core/projects/core.interface';
import { DatasetIdentifier } from '../../../../src/core/projects/dataset.interface';
import { ProjectsQueryOptions } from '../../../../src/core/projects/services/project-service.interface';
import { Task } from '../../../../src/core/projects/task.interface';
import { RESOURCE_TYPE, UsersQueryParams } from '../../../../src/core/users/users.interface';
import { WorkspaceIdentifier } from '../workspaces/services/workspaces.interface';

const WORKSPACES = (organizationId: string) => [organizationId, 'workspaces'];

const ALL_TASKS_DATASET_STATISTICS_KEY = (projectId: string, datasetId: string): [string, string, string] => [
    projectId,
    'dataset-statistics',
    datasetId,
];

const DATASET_STATISTICS_KEY = (
    projectId: string,
    datasetId: string,
    taskId: string
): [string, string, string, string] => [projectId, 'dataset-statistics', datasetId, taskId];

const MODELS_KEY = (projectIdentifier: ProjectIdentifier): readonly [string, string, string] => [
    projectIdentifier.workspaceId,
    projectIdentifier.projectId,
    'models',
];

const MODELS_GROUP = (modelGroupIdentifier: ModelGroupIdentifier): readonly [string, string, string, string] => [
    ...MODELS_KEY(modelGroupIdentifier),
    modelGroupIdentifier.groupId,
];

const MODEL_KEY = (modelIdentifier: ModelIdentifier): readonly [string, string, string, string, string] => {
    const { modelId, ...modelGroupIdentifier } = modelIdentifier;
    return [...MODELS_GROUP(modelGroupIdentifier), modelId];
};

const TRAINING_DATASET_REVISION_KEY = (
    projectIdentifier: ProjectIdentifier,
    datasetId: string,
    revisionId: string
): readonly [string, string, string, string, string] => [
    projectIdentifier.workspaceId,
    projectIdentifier.projectId,
    datasetId,
    revisionId,
    'training-dataset-revision-id',
];

const TRAINING_DATASET_ADVANCED_FILTER_MEDIA = (
    projectIdentifier: ProjectIdentifier,
    storageId: string,
    revisionId: string,
    filterOptions: AdvancedFilterOptions,
    sortingOptions: AdvancedFilterSortingOptions
): [string, string, string, string, string, string, AdvancedFilterOptions, AdvancedFilterSortingOptions] => [
    ...TRAINING_DATASET_REVISION_KEY(projectIdentifier, storageId, revisionId),
    'media',
    filterOptions,
    sortingOptions,
];

const TRAINING_DATASET_ADVANCED_FILTER_VIDEO = (
    projectIdentifier: ProjectIdentifier,
    storageId: string,
    revisionId: string,
    videoId: string,
    filterOptions: AdvancedFilterOptions,
    sortingOptions: AdvancedFilterSortingOptions
): [string, string, string, string, string, string, string, AdvancedFilterOptions, AdvancedFilterSortingOptions] => [
    ...TRAINING_DATASET_REVISION_KEY(projectIdentifier, storageId, revisionId),
    videoId,
    'video',
    filterOptions,
    sortingOptions,
];

const getSelectedMediaItemQueryKeys = () => {
    const commonKey = (mediaItemIdentifier: MediaIdentifier | undefined): [string, MediaIdentifier | undefined] => [
        'selected-media-items',
        mediaItemIdentifier,
    ];

    return {
        IMAGE: (mediaIdentifier: MediaIdentifier | undefined) => [...commonKey(mediaIdentifier), 'image'],
        ANNOTATIONS: (mediaIdentifier: MediaIdentifier | undefined, annotationId = 'latest') => [
            ...commonKey(mediaIdentifier),
            'annotations',
            annotationId,
        ],
        PREDICTIONS: (
            mediaIdentifier: MediaIdentifier | undefined,
            prefix: string,
            predictionCache: PredictionCache,
            taskId?: string,
            roiId?: string
        ) => [...commonKey(mediaIdentifier), taskId, roiId, `${prefix}-predictions`, predictionCache],
        SELECTED: (mediaIdentifier: MediaIdentifier | undefined, taskId?: string) => [
            ...commonKey(mediaIdentifier),
            taskId,
            'selected',
        ],

        DEFAULT: (mediaIdentifier: MediaIdentifier | undefined) => [
            'default-selected-media-item',
            ...commonKey(mediaIdentifier),
        ],
    };
};

const SELECTED_MEDIA_ITEM = getSelectedMediaItemQueryKeys();

const MEDIA_ITEM_ANNOTATIONS = (identifier: MediaIdentifier): [string, MediaIdentifier, string] => [
    'media',
    identifier,
    'annotations',
];

const MEDIA_ITEM = (datasetIdentifier: DatasetIdentifier, mediaIdentifier: MediaIdentifier | undefined) => {
    return [datasetIdentifier, 'media-item', mediaIdentifier];
};

const VIDEO_ANNOTATIONS = (
    datasetIdentifier: DatasetIdentifier,
    identifier: VideoIdentifier,
    options?: VideoPaginationOptions
): [DatasetIdentifier, VideoIdentifier, 'active-learning', Partial<VideoPaginationOptions>] => [
    datasetIdentifier,
    identifier,
    'active-learning',
    options ?? {},
];

const VIDEO_PREDICTIONS = (
    datasetIdentifier: DatasetIdentifier,
    identifier: VideoIdentifier,
    predictionMode: PredictionMode,
    selectedTask: null | Task,
    options?: VideoPaginationOptions
): [
    DatasetIdentifier,
    VideoIdentifier,
    'predictions',
    PredictionMode,
    string | undefined,
    Partial<VideoPaginationOptions>,
] => [datasetIdentifier, identifier, 'predictions', predictionMode, selectedTask?.id, options ?? {}];

const VIDEO_RANGE_ANNOTATIONS = (
    datasetIdentifier: DatasetIdentifier,
    identifier: VideoIdentifier
): [DatasetIdentifier, VideoIdentifier, string] => [datasetIdentifier, identifier, 'range-annotations'];

const ADVANCED_MEDIA_ITEMS = (
    datasetIdentifier: DatasetIdentifier | undefined,
    filterOptions: AdvancedFilterOptions,
    sortingOptions: AdvancedFilterSortingOptions
): [DatasetIdentifier | undefined, string, AdvancedFilterOptions, AdvancedFilterSortingOptions] => {
    return [datasetIdentifier, 'media', filterOptions, sortingOptions];
};

const ADVANCED_MEDIA_FRAME_ITEMS = (
    datasetIdentifier: DatasetIdentifier | undefined,
    filterOptions: AdvancedFilterOptions,
    sortingOptions: AdvancedFilterSortingOptions
): [DatasetIdentifier | undefined, string, AdvancedFilterOptions, AdvancedFilterSortingOptions] => {
    return [datasetIdentifier, 'media-frame', filterOptions, sortingOptions];
};

const ACTIVE_MEDIA_ITEMS = (
    datasetIdentifier: DatasetIdentifier,
    selectedTask: Task | null
): ReadonlyArray<DatasetIdentifier | string> => {
    const key = [datasetIdentifier, 'media', 'active'] as const;

    if (selectedTask !== null) {
        return [...key, selectedTask.id];
    }

    return key;
};

const NEXT_ACTIVE_MEDIA_ITEM = (
    datasetIdentifier: DatasetIdentifier,
    currentMediaItemIdentifier: MediaIdentifier | undefined
): [string, DatasetIdentifier, MediaIdentifier | undefined] => [
    'next-active-media',
    datasetIdentifier,
    currentMediaItemIdentifier,
];

const MODEL_STATISTICS_KEY = ({
    workspaceId,
    projectId,
    groupId,
    modelId,
}: ModelIdentifier): readonly [string, string, string, string, string] => [
    workspaceId,
    projectId,
    groupId,
    modelId,
    'training-statistics',
];

const PROJECT_STATUS_KEY = (projectIdentifier: ProjectIdentifier): [string, string, string] => [
    projectIdentifier.workspaceId,
    projectIdentifier.projectId,
    'project-status',
];

const INFERENCE_SERVER_KEY = (projectIdentifier: ProjectIdentifier): [string, string, string] => [
    projectIdentifier.workspaceId,
    projectIdentifier.projectId,
    'inference-server',
];

const STATUS_KEY = (): [string] => ['status'];

const JOB_DELETE_KEY = (workspaceId: string, jobId: string): readonly [string, string, string] => [
    workspaceId,
    jobId,
    'delete-job',
];

const JOBS_KEY = (
    workspaceIdentifier: WorkspaceIdentifier,
    jobState: string,
    areTrainingDetails?: boolean
): [string, string, string, string] => [
    workspaceIdentifier.workspaceId,
    'jobs',
    jobState,
    areTrainingDetails ? 'training_details' : 'jobs_management',
];

const PROJECTS_KEY = (
    workspaceId: string,
    queryOptions?: ProjectsQueryOptions,
    withSize = false
):
    | readonly [string, string, string, ProjectsQueryOptions]
    | [string, string, string, ProjectsQueryOptions, string]
    | [string, string, string]
    | [string, string, string, string] => {
    const baseKey: [string, string, string] = [workspaceId, 'projects', 'search'];

    if (queryOptions && withSize) {
        return [...baseKey, queryOptions, 'withSize'];
    }

    if (queryOptions) {
        return [...baseKey, queryOptions];
    }

    if (withSize) {
        return [...baseKey, 'withSize'];
    }

    return baseKey;
};

const PROJECT_KEY = (projectIdentifier: ProjectIdentifier): readonly [string, string, string] => [
    projectIdentifier.workspaceId,
    'projects',
    projectIdentifier.projectId,
];

const PROJECT_SETTINGS_KEY = (projectIdentifier: ProjectIdentifier): readonly [string, string, string] | [string] => {
    const { workspaceId, projectId } = projectIdentifier;
    return ['project-settings', workspaceId, projectId];
};

const PROJECT_NAMES = (workspaceId: WorkspaceIdentifier) => [workspaceId.workspaceId, 'projects', 'names'];

const SETTINGS_KEY = (): readonly [string] => {
    return ['user-settings'];
};

const CONFIGURATION = (projectIdentifier: ProjectIdentifier): readonly [string, string, string, string] => [
    ...PROJECT_KEY(projectIdentifier),
    'configuration',
];

const PROJECT_LABELS_KEY = (
    datasetIdentifier: DatasetIdentifier
): readonly [string, string, string, string, string] => [
    ...PROJECT_KEY(datasetIdentifier),
    datasetIdentifier.datasetId,
    'labels',
];

const MODEL_CONFIG_PARAMETERS = (
    projectIdentifier: ProjectIdentifier,
    taskId: string,
    modelId?: string,
    modelTemplateId?: string | null
): readonly [string, string, string, string, string, string | undefined] => {
    if (modelId) {
        return [...CONFIGURATION(projectIdentifier), taskId, modelId];
    }

    if (modelTemplateId) {
        return [...CONFIGURATION(projectIdentifier), taskId, modelTemplateId];
    }

    return [...CONFIGURATION(projectIdentifier), taskId, undefined];
};

const SUPPORTED_ALGORITHMS = (domain: DOMAIN | undefined): [string, DOMAIN | undefined] => [
    'supported_algorithms',
    domain,
];

const EXPORT_MODEL = (
    projectIdentifier: ProjectIdentifier,
    groupId: string,
    modelId: string,
    includeCode: boolean
): readonly [string, string, string, string, boolean, string] => [
    projectIdentifier.workspaceId,
    projectIdentifier.projectId,
    groupId,
    modelId,
    includeCode,
    'export-model',
];

const CODE_DEPLOYMENT_STATUS_KEY = (projectIdentifier: ProjectIdentifier): [string, string, string] => [
    'code-deployment-status',
    projectIdentifier.workspaceId,
    projectIdentifier.projectId,
];

const USERS = (organizationId: string, queryParams: UsersQueryParams = {}) => [organizationId, 'users', queryParams];
const USER = (organizationId: string, userId: string | undefined) => [organizationId, 'users', 'user', userId];

const USER_ROLES = (organizationId: string, userId: string, resourceType?: RESOURCE_TYPE) => [
    organizationId,
    'users',
    userId,
    'roles',
    resourceType ?? '',
];

const ACTIVE_USER = (organizationId: string) => [organizationId, 'users', 'active'];

const USER_ONBOARDING_PROFILE = ['user-onboarding-profile'];

const FEATURE_FLAGS = ['feature-flags'];

const TESTS = (projectIdentifier: ProjectIdentifier): [string, string, string, string] => [
    ...PROJECT_KEY(projectIdentifier),
    'tests',
];

const TEST = (projectIdentifier: ProjectIdentifier, testId: string): [string, string, string, string, string] => [
    ...TESTS(projectIdentifier),
    testId,
];

const TEST_PREDICTIONS = (
    projectIdentifier: ProjectIdentifier,
    testId: string,
    predictionId: string
): [string, string, string, string, string, string] => [...TESTS(projectIdentifier), testId, predictionId];

const TEST_ADVANCED_FILTER_MEDIA = (
    projectIdentifier: ProjectIdentifier,
    testId: string,
    filterOptions: AdvancedFilterOptions,
    sortingOptions: AdvancedFilterSortingOptions
): [string, string, string, string, string, string, AdvancedFilterOptions, AdvancedFilterSortingOptions] => [
    ...TEST(projectIdentifier, testId),
    'media',
    filterOptions,
    sortingOptions,
];

const SERVICE_ACCOUNTS_API_KEY = ['service-account', 'api-key'];

const PROJECT_EXPORT_STATUS_KEY = (projectId: string, exportId: string) => [
    'project-export-status',
    projectId,
    exportId,
];

const PROJECT_IMPORT_STATUS_KEY = (workspaceId: string, importProjectId: string) => [
    'project-import-status',
    workspaceId,
    importProjectId,
];

const PLATFORM_UTILS_KEYS = {
    VERSION_ENTITY_KEY: ['version'],
    WORKFLOW_ID: (userSubjectIdentifier: string) => ['workflow_id', userSubjectIdentifier],
};

const ORGANIZATIONS = (queryOptions: GetOrganizationsQueryOptions) => ['organizations', queryOptions];

const ORGANIZATION = (organizationId: string | undefined) => ['organizations', organizationId];

const ORGANIZATION_BALANCE = ({ organizationId }: OrganizationIdentifier) => [
    'organizations',
    organizationId,
    'balance',
];

const CREDIT_TRANSACTIONS = ({ organizationId }: OrganizationIdentifier, options: GetTransactionsQueryOptions) => [
    'transactions',
    organizationId,
    options,
];

const CREDIT_TRANSACTIONS_AGGREGATES = (
    { organizationId }: OrganizationIdentifier,
    { keys, ...rest }: GetTransactionsAggregatesQueryOptions
) => ['transactions-aggregates', organizationId, ...Array.from(keys), rest];

const CREDIT_ACCOUNTS = ({ organizationId }: OrganizationIdentifier) => [
    'organizations',
    organizationId,
    'credit-accounts',
];

const CREDIT_ACCOUNT = (creditAccountId: CreditAccountIdentifier) => [
    ...CREDIT_ACCOUNTS(creditAccountId),
    creditAccountId,
];

const ACTIVE_SUBSCRIPTION = (organizationId: OrganizationIdentifier) => [
    'subscriptions',
    organizationId.organizationId,
    'active',
];

const ORGANIZATION_QUOTAS = (organizationId: OrganizationIdentifier) => [
    'organizations',
    organizationId.organizationId,
    'quotas',
];

const EXPORT_DATASET_STATUS_JOB_KEY = (data: { organizationId: string; workspaceId: string; jobId: string }) => [
    'export-dataset-status-job',
    data.organizationId,
    data.workspaceId,
    data.jobId,
];
const PREPARE_DATASET_STATUS_JOB_KEY = (data: { organizationId: string; workspaceId: string; jobId: string }) => [
    'prepare-dataset-status-job',
    data.organizationId,
    data.workspaceId,
    data.jobId,
];

const IMPORT_DATASET_NEW_PROJECT_STATUS_JOB_KEY = (data: {
    jobId: string;
    workspaceId: string;
    organizationId: string;
}) => ['import-dataset-new-project-status-job', data.organizationId, data.workspaceId, data.jobId];

const IMPORT_DATASET_EXISTING_PROJECT_STATUS_JOB_KEY = (data: {
    jobId: string;
    workspaceId: string;
    organizationId: string;
}) => ['import-dataset-existing-project-status-job', data.organizationId, data.workspaceId, data.jobId];

const PRODUCTS = ['products'];

const PRODUCT = (productId: number) => [...PRODUCTS, productId];

const MAINTENANCE = ['maintenance'];

const CONFIGURATION_PARAMETERS = {
    PROJECT: (projectIdentifier: ProjectIdentifier) =>
        [
            'project-configuration',
            projectIdentifier.organizationId,
            projectIdentifier.workspaceId,
            projectIdentifier.projectId,
        ] as const,
    TRAINING: (projectIdentifier: ProjectIdentifier, queryParameters?: TrainingConfigurationQueryParameters) =>
        [
            'training-configuration',
            projectIdentifier.organizationId,
            projectIdentifier.workspaceId,
            projectIdentifier.projectId,
            queryParameters?.taskId,
            queryParameters?.modelId,
            queryParameters?.algorithmId,
        ] as const,
};

const QUERY_KEYS = {
    WORKSPACES,
    DATASET_STATISTICS_KEY,
    ALL_TASKS_DATASET_STATISTICS_KEY,
    MODELS_KEY,
    MODEL_KEY,
    MODEL_STATISTICS_KEY,
    MODELS_GROUP,
    MEDIA_ITEM,
    ADVANCED_MEDIA_ITEMS,
    ADVANCED_MEDIA_FRAME_ITEMS,
    ACTIVE_MEDIA_ITEMS,
    SELECTED_MEDIA_ITEM,
    MEDIA_ITEM_ANNOTATIONS,
    VIDEO_ANNOTATIONS,
    VIDEO_PREDICTIONS,
    VIDEO_RANGE_ANNOTATIONS,
    NEXT_ACTIVE_MEDIA_ITEM,
    PROJECT_STATUS_KEY,
    INFERENCE_SERVER_KEY,
    STATUS_KEY,
    JOBS_KEY,
    JOB_DELETE_KEY,
    PROJECTS_KEY,
    PROJECT_KEY,
    PROJECT_NAMES,
    CONFIGURATION,
    MODEL_CONFIG_PARAMETERS,
    SUPPORTED_ALGORITHMS,
    PROJECT_LABELS_KEY,
    EXPORT_MODEL,
    SETTINGS_KEY,
    PROJECT_SETTINGS_KEY,
    CODE_DEPLOYMENT_STATUS_KEY,
    TESTS,
    TEST,
    TEST_PREDICTIONS,
    TEST_ADVANCED_FILTER_MEDIA,
    TRAINING_DATASET_REVISION_KEY,
    TRAINING_DATASET_ADVANCED_FILTER_MEDIA,
    TRAINING_DATASET_ADVANCED_FILTER_VIDEO,
    SERVICE_ACCOUNTS_API_KEY,
    PROJECT_EXPORT_STATUS_KEY,
    PROJECT_IMPORT_STATUS_KEY,
    FEATURE_FLAGS,
    PLATFORM_UTILS_KEYS,
    ORGANIZATIONS,
    ORGANIZATION,
    ORGANIZATION_BALANCE,
    CREDIT_TRANSACTIONS,
    CREDIT_TRANSACTIONS_AGGREGATES,
    CREDIT_ACCOUNTS,
    CREDIT_ACCOUNT,
    ACTIVE_SUBSCRIPTION,
    ORGANIZATION_QUOTAS,
    USERS,
    USER,
    ACTIVE_USER,
    USER_ROLES,
    USER_ONBOARDING_PROFILE,
    EXPORT_DATASET_STATUS_JOB_KEY,
    PREPARE_DATASET_STATUS_JOB_KEY,
    IMPORT_DATASET_NEW_PROJECT_STATUS_JOB_KEY,
    IMPORT_DATASET_EXISTING_PROJECT_STATUS_JOB_KEY,
    PRODUCTS,
    PRODUCT,
    MAINTENANCE,
    CONFIGURATION_PARAMETERS,
} as const;

export default QUERY_KEYS;
