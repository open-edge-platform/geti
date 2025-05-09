// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';
import isNil from 'lodash/isNil';

import { PredictionCache, PredictionId } from '../annotations/services/prediction-service.interface';
import { VideoPaginationOptions } from '../annotations/services/video-pagination-options.interface';
import { Rect } from '../annotations/shapes.interface';
import { CreditAccountIdentifier } from '../credits/credits.interface';
import {
    GetTransactionsAggregatesQueryOptions,
    GetTransactionsQueryOptions,
} from '../credits/transactions/services/transactions-service.interface';
import { JobTypePayload } from '../jobs/jobs.const';
import { JobsQueryParams } from '../jobs/services/jobs-service.interface';
import { MEDIA_GROUP, MEDIA_TYPE } from '../media/base-media.interface';
import { AdvancedFilterSortingOptions } from '../media/media-filter.interface';
import { MediaIdentifier } from '../media/media.interface';
import { isVideo } from '../media/video.interface';
import { ModelGroupIdentifier, ModelIdentifier } from '../models/models.interface';
import { OrganizationIdentifier } from '../organizations/organizations.interface';
import { ProjectIdentifier } from '../projects/core.interface';
import { DatasetIdentifier } from '../projects/dataset.interface';
import { ProjectsQueryOptions } from '../projects/services/project-service.interface';
import { TaskIdentifier } from '../statistics/dtos/dataset-statistics.interface';
import { MemberRoleDTO, ResourceTypeDTO } from '../users/users.interface';
import { WorkspaceIdentifier } from '../workspaces/services/workspaces.interface';
import { addVideoPaginationSearchParams, buildAdvancedFilterSearchOptions } from './utils';

const API = '/api';

const API_VERSION = 'v1';

const PREFIX = (url: string) => url;

const WORKSPACES = (organizationId: string): string => {
    return `${ORGANIZATION(organizationId)}/workspaces`;
};

const WORKSPACE = (workspaceIdentifier: WorkspaceIdentifier): string =>
    `${WORKSPACES(workspaceIdentifier.organizationId)}/${workspaceIdentifier.workspaceId}`;

const ORGANIZATIONS = `${API_VERSION}/organizations`;

const ORGANIZATION = (organizationId: string): string => {
    return `${ORGANIZATIONS}/${organizationId}`;
};

const ORGANIZATION_BALANCE = ({ organizationId }: OrganizationIdentifier): string => {
    return `${ORGANIZATION(organizationId)}/balance`;
};

const CREDIT_TRANSACTIONS = (
    { organizationId }: OrganizationIdentifier,
    queryOptions: GetTransactionsQueryOptions
): string => {
    const searchOptionsUrl = new URLSearchParams();

    if (queryOptions.fromDate) searchOptionsUrl.set('from_date', queryOptions.fromDate);
    if (queryOptions.toDate) searchOptionsUrl.set('to_date', queryOptions.toDate);
    if (queryOptions.skip) searchOptionsUrl.set('skip', queryOptions.skip.toString());
    if (queryOptions.limit) searchOptionsUrl.set('limit', queryOptions.limit.toString());
    if (queryOptions.projectId) searchOptionsUrl.set('project_id', queryOptions.projectId);

    return `${ORGANIZATION(organizationId)}/transactions?${searchOptionsUrl.toString()}`;
};

const CREDIT_TRANSACTIONS_AGGREGATES = (
    { organizationId }: OrganizationIdentifier,
    queryOptions: GetTransactionsAggregatesQueryOptions
): string => {
    const { keys, fromDate, toDate, projectId, skip, limit } = queryOptions;

    const searchOptionsUrl = new URLSearchParams();

    for (const key of Array.from(keys.values())) {
        searchOptionsUrl.append('key', key);
    }

    if (fromDate) searchOptionsUrl.set('from_date', fromDate);
    if (toDate) searchOptionsUrl.set('to_date', toDate);
    if (skip) searchOptionsUrl.set('skip', skip.toString());
    if (limit) searchOptionsUrl.set('limit', limit.toString());
    if (projectId) searchOptionsUrl.set('project_id', projectId);

    return `${ORGANIZATION(organizationId)}/transactions/aggregates?${searchOptionsUrl.toString()}`;
};

const CREDIT_ACCOUNTS = ({ organizationId }: OrganizationIdentifier): string => {
    return `${ORGANIZATION(organizationId)}/credit_accounts`;
};

const CREDIT_ACCOUNT = (id: CreditAccountIdentifier): string => {
    return `${CREDIT_ACCOUNTS(id)}/${id.creditAccountId}`;
};

const CREDIT_ACCOUNT_BALANCE = (id: CreditAccountIdentifier): string => {
    return `${CREDIT_ACCOUNT(id)}/balance`;
};

const PROJECTS = (workspaceIdentifier: WorkspaceIdentifier): string => `${WORKSPACE(workspaceIdentifier)}/projects`;

const PROJECTS_SEARCH = (
    workspaceIdentifier: WorkspaceIdentifier,
    queryOptions: ProjectsQueryOptions,
    withSize: boolean
): string => {
    const searchOptionsUrl = new URLSearchParams();

    if (queryOptions.name) {
        searchOptionsUrl.set('name', queryOptions.name);
    }

    if (queryOptions && queryOptions.sortBy) {
        searchOptionsUrl.set('sort_by', queryOptions.sortBy);
        searchOptionsUrl.set('sort_direction', queryOptions.sortDir);
    }

    if (withSize) {
        searchOptionsUrl.set('with_size', 'true');
    }

    return `${PROJECTS(workspaceIdentifier)}?${searchOptionsUrl.toString()}`;
};

const PROJECT = (projectIdentifier: ProjectIdentifier): string =>
    `${PROJECTS(projectIdentifier)}/${projectIdentifier.projectId}`;

const PROJECT_NAMES = (workspaceIdentifier: WorkspaceIdentifier) => `${WORKSPACE(workspaceIdentifier)}/projects_names`;

const EXPORT_PROJECT = (projectIdentifier: ProjectIdentifier): string => `${PROJECT(projectIdentifier)}:export`;

// TODO Remove
const EXPORT_PROJECT_STATUS = (projectIdentifier: ProjectIdentifier, exportProjectId: string): string =>
    `${PROJECT(projectIdentifier)}/exports/${exportProjectId}`;

// TODO Remove(?)
const EXPORT_PROJECT_DOWNLOAD = (projectIdentifier: ProjectIdentifier, exportProjectId: string): string =>
    `${PROJECT(projectIdentifier)}/exports/${exportProjectId}/download`;

const GLOBAL_SETTINGS = () => `${API_VERSION}/user_settings`;

const PROJECT_SETTINGS = (projectIdentifier: ProjectIdentifier) => {
    const searchParams = new URLSearchParams();

    searchParams.set('project_id', projectIdentifier.projectId);

    return `${API_VERSION}/user_settings?${searchParams.toString()}`;
};

const DATASET_URL = (datasetIdentifier: DatasetIdentifier): string => {
    const { datasetId, ...projectIdentifier } = datasetIdentifier;
    return `${PROJECT(projectIdentifier)}/datasets/${datasetId}`;
};

const TRAINING_REVISION_URL = (
    projectIdentifier: ProjectIdentifier,
    datasetStorageId: string,
    trainingRevisionId: string
): string =>
    `${DATASET_URL({ ...projectIdentifier, datasetId: datasetStorageId })}/training_revisions/${trainingRevisionId}`;

const VIDEO_TRAINING_ADVANCED_DATASET_FILTER = (
    projectIdentifier: ProjectIdentifier,
    datasetStorageId: string,
    trainingRevisionId: string,
    videoId: string,
    mediaItemsLoadSize: number,
    sortingOptions: AdvancedFilterSortingOptions
): string => {
    const searchOptionsUrl = buildAdvancedFilterSearchOptions(mediaItemsLoadSize, sortingOptions);

    return `${TRAINING_REVISION_URL(
        projectIdentifier,
        datasetStorageId,
        trainingRevisionId
    )}/media/videos/${videoId}:query?${searchOptionsUrl.toString()}`;
};

const DATASET_DELETE_URL = (datasetIdentifier: DatasetIdentifier): string => `${DATASET_URL(datasetIdentifier)}/media`;

const SERVICE_ACCOUNTS = `${API_VERSION}/service_accounts`;

const ACTIVE_MEDIA = (projectIdentifier: ProjectIdentifier, mediaItemsLoadSize: number, taskId?: string): string => {
    const activeMediaUrl = `${PROJECT(projectIdentifier)}/datasets/active?limit=${mediaItemsLoadSize}`;

    if (taskId !== undefined) {
        return `${activeMediaUrl}&task_id=${taskId}`;
    }

    return activeMediaUrl;
};

const ADVANCED_DATASET_FILTER = (
    datasetIdentifier: DatasetIdentifier,
    mediaItemsLoadSize: number,
    sortingOptions: AdvancedFilterSortingOptions
): string => {
    const searchOptionsUrl = buildAdvancedFilterSearchOptions(mediaItemsLoadSize, sortingOptions);

    return `${DATASET_URL(datasetIdentifier)}/media:query?${searchOptionsUrl.toString()}`;
};
const ADVANCED_VIDEO_FRAMES_FILTER = (
    datasetIdentifier: DatasetIdentifier,
    videoId: string,
    mediaItemsLoadSize: number,
    sortingOptions: AdvancedFilterSortingOptions
): string => {
    const searchOptionsUrl = buildAdvancedFilterSearchOptions(mediaItemsLoadSize, sortingOptions);

    return `${DATASET_URL(datasetIdentifier)}/media/videos/${videoId}:query?${searchOptionsUrl.toString()}`;
};

const TRAINING_ADVANCED_DATASET_FILTER = (
    projectIdentifier: ProjectIdentifier,
    datasetStorageId: string,
    trainingRevisionId: string,
    mediaItemsLoadSize: number,
    sortingOptions: AdvancedFilterSortingOptions
): string => {
    const searchOptionsUrl = buildAdvancedFilterSearchOptions(mediaItemsLoadSize, sortingOptions);

    return `${TRAINING_REVISION_URL(
        projectIdentifier,
        datasetStorageId,
        trainingRevisionId
    )}/media:query?${searchOptionsUrl.toString()}`;
};

const MEDIA_UPLOAD = (datasetIdentifier: DatasetIdentifier, mediaGroup: MEDIA_GROUP): string => {
    return `${DATASET_URL(datasetIdentifier)}/media/${mediaGroup}`;
};

const MEDIA_DELETE = (datasetIdentifier: DatasetIdentifier, mediaGroup: MEDIA_GROUP, mediaItemId: string): string => {
    return `${DATASET_URL(datasetIdentifier)}/media/${mediaGroup}/${mediaItemId}`;
};

const ANNOTATIONS_STATISTICS = (taskIdentifier: TaskIdentifier): string => {
    const { taskId, ...datasetIdentifier } = taskIdentifier;

    const searchParams = new URLSearchParams();

    if (!isNil(taskId)) {
        searchParams.set('task_id', taskId);
    }

    return `${DATASET_URL(datasetIdentifier)}/statistics?${searchParams.toString()}`;
};

export const MEDIA_ITEM = (datasetIdentifier: DatasetIdentifier, mediaIdentifier: MediaIdentifier): string => {
    const baseUrl = `${DATASET_URL(datasetIdentifier)}/media`;

    if (mediaIdentifier.type === MEDIA_TYPE.IMAGE) {
        const { imageId } = mediaIdentifier;

        return `${baseUrl}/images/${imageId}`;
    }

    if (mediaIdentifier.type === MEDIA_TYPE.VIDEO) {
        const { videoId } = mediaIdentifier;

        return `${baseUrl}/${MEDIA_GROUP.VIDEOS}/${videoId}`;
    }

    if (mediaIdentifier.type === MEDIA_TYPE.VIDEO_FRAME) {
        const { videoId, frameNumber } = mediaIdentifier;

        return `${baseUrl}/${MEDIA_GROUP.VIDEOS}/${videoId}/frames/${frameNumber}`;
    }

    throw new Error(`Unsupported media type`);
};

enum MEDIA_IMAGE_TYPE {
    FULL = 'full',
    THUMB = 'thumb',
    STREAM = 'stream',
}

// Note: This returns the absolute url (including base url and api prefix) as it is used by img tags
const MEDIA_ITEM_IMAGE = (
    datasetIdentifier: DatasetIdentifier,
    mediaIdentifier: MediaIdentifier,
    type: MEDIA_IMAGE_TYPE
): string => {
    return `${API}/${MEDIA_ITEM(datasetIdentifier, mediaIdentifier)}/display/${type}`;
};

const MEDIA_ITEM_THUMBNAIL = (datasetIdentifier: DatasetIdentifier, mediaIdentifier: MediaIdentifier): string => {
    return MEDIA_ITEM_IMAGE(datasetIdentifier, mediaIdentifier, MEDIA_IMAGE_TYPE.THUMB);
};

const MEDIA_ITEM_SRC = (datasetIdentifier: DatasetIdentifier, mediaIdentifier: MediaIdentifier): string => {
    return MEDIA_ITEM_IMAGE(datasetIdentifier, mediaIdentifier, MEDIA_IMAGE_TYPE.FULL);
};

const MEDIA_ITEM_STREAM = (datasetIdentifier: DatasetIdentifier, mediaIdentifier: MediaIdentifier): string => {
    return MEDIA_ITEM_IMAGE(datasetIdentifier, mediaIdentifier, MEDIA_IMAGE_TYPE.STREAM);
};

const ANNOTATIONS = (
    datasetIdentifier: DatasetIdentifier,
    mediaIdentifier: MediaIdentifier,
    // Annotation id can either be 'latest', or an id for a historic annotation
    annotationId = 'latest',
    options?: VideoPaginationOptions
): string => {
    const searchParams = new URLSearchParams();

    if (isVideo({ identifier: mediaIdentifier }) && options !== undefined) {
        addVideoPaginationSearchParams(options, searchParams);
    }

    return `${MEDIA_ITEM(datasetIdentifier, mediaIdentifier)}/annotations/${annotationId}?${searchParams.toString()}`;
};

const SAVE_ANNOTATIONS = (datasetIdentifier: DatasetIdentifier, mediaIdentifier: MediaIdentifier): string =>
    `${MEDIA_ITEM(datasetIdentifier, mediaIdentifier)}/annotations`;

const RANGE_ANNOTATIONS = (datasetIdentifier: DatasetIdentifier, mediaIdentifier: MediaIdentifier): string =>
    `${MEDIA_ITEM(datasetIdentifier, mediaIdentifier)}/range_annotation`;

const PREDICTION = (
    datasetIdentifier: DatasetIdentifier,
    mediaIdentifier: MediaIdentifier,
    predictionId: PredictionId,
    taskId?: string,
    selectedInputId?: string,
    options?: VideoPaginationOptions
): string => {
    const searchParams = new URLSearchParams();
    if (taskId) {
        searchParams.set('task_id', taskId);
    }

    if (selectedInputId) {
        searchParams.set('roi_id', selectedInputId);
    }

    if (isVideo({ identifier: mediaIdentifier }) && options !== undefined) {
        addVideoPaginationSearchParams(options, searchParams);
    }

    return `${MEDIA_ITEM(datasetIdentifier, mediaIdentifier)}/predictions/${predictionId}?${searchParams.toString()}`;
};

const getRectRoiToString = (roi?: Omit<Rect, 'shapeType'>, cache?: PredictionCache) => {
    const searchParams = new URLSearchParams();

    if (!isNil(cache)) {
        searchParams.set('use_cache', cache);
    }
    if (!isNil(roi)) {
        searchParams.set('roi', `${roi.x},${roi.y},${roi.width},${roi.height}`);
    }

    return searchParams.toString();
};

const getPipelineType = (taskId?: string) => (isEmpty(taskId) ? 'active' : taskId);

const PIPELINES_STATUS = (projectIdentifier: ProjectIdentifier, taskId?: string): string =>
    `${PROJECT(projectIdentifier)}/pipelines/${getPipelineType(taskId)}/status`;

const PREDICTION_NEW = (
    projectIdentifier: ProjectIdentifier,
    cache = PredictionCache.AUTO,
    taskId?: string,
    roi?: Omit<Rect, 'shapeType'>
): string => {
    return `${PROJECT(projectIdentifier)}/pipelines/${getPipelineType(taskId)}:predict?${getRectRoiToString(
        roi,
        cache
    )}`;
};

const EXPLAIN_NEW = (projectIdentifier: ProjectIdentifier, taskId?: string, roi?: Omit<Rect, 'shapeType'>): string => {
    return `${PROJECT(projectIdentifier)}/pipelines/${getPipelineType(taskId)}:explain?${getRectRoiToString(roi)}`;
};

const BATCH_PREDICT_STREAM = (projectIdentifier: ProjectIdentifier, predictionMode: string | undefined): string => {
    const searchParams = new URLSearchParams();
    if (predictionMode) {
        searchParams.set('use_cache', predictionMode);
    }
    return `${PROJECT(projectIdentifier)}/pipelines/active:batch_predict_stream?${searchParams.toString()}`;
};

const BATCH_PREDICT = (projectIdentifier: ProjectIdentifier, predictionMode: string | undefined): string => {
    const searchParams = new URLSearchParams();
    if (predictionMode) {
        searchParams.set('use_cache', predictionMode);
    }
    return `${PROJECT(projectIdentifier)}/pipelines/active:batch_predict?${searchParams.toString()}`;
};

const PREDICTION_SINGLE_IMAGE = (projectIdentifier: ProjectIdentifier, explain: boolean): string =>
    `${PROJECT(projectIdentifier)}/predict?raw_maps=true${explain ? '&explain=true' : ''}`;

const INFERENCE_SERVER_STATUS = (projectIdentifier: ProjectIdentifier): string =>
    `${PROJECT(projectIdentifier)}/predict/status`;

const VISUAL_PROMPT_INFERENCE = (projectIdentifier: ProjectIdentifier, taskId: string): string => {
    return `${PROJECT(projectIdentifier)}/pipelines/${getPipelineType(taskId)}:prompt`;
};

const PROJECT_STATUS = (projectIdentifier: ProjectIdentifier): string => `${PROJECT(projectIdentifier)}/status`;

// TODO: check why this isn't used
const PROJECT_LABELS = (datasetIdentifier: DatasetIdentifier): string => `${DATASET_URL(datasetIdentifier)}/labels`;

const MODELS_BASE = (projectIdentifier: ProjectIdentifier): string => `${PROJECT(projectIdentifier)}/model_groups`;

const MODELS = (projectIdentifier: ProjectIdentifier): string =>
    `${MODELS_BASE(projectIdentifier)}?include_lifecycle_stage=true`;

const MODEL_GROUPS_BASE = (modelGroupIdentifier: ModelGroupIdentifier): string =>
    `${MODELS_BASE(modelGroupIdentifier)}/${modelGroupIdentifier.groupId}`;

const MODEL_GROUPS = (modelGroupIdentifier: ModelGroupIdentifier): string =>
    `${MODEL_GROUPS_BASE(modelGroupIdentifier)}?include_lifecycle_stage=true`;

const ACTIVATE_MODEL = (modelGroupIdentifier: ModelGroupIdentifier): string =>
    `${MODEL_GROUPS_BASE(modelGroupIdentifier)}:activate`;

const MODEL = (modelIdentifier: ModelIdentifier): string =>
    `${MODEL_GROUPS_BASE(modelIdentifier)}/models/${modelIdentifier.modelId}`;

const MODEL_STATISTICS = (modelIdentifier: ModelIdentifier): string => `${MODEL(modelIdentifier)}/statistics`;

const ARCHIVE_MODEL = (modelIdentifier: ModelIdentifier): string => `${MODEL(modelIdentifier)}:purge`;

const MANUAL_TRAIN_MODEL = (projectIdentifier: ProjectIdentifier): string => `${PROJECT(projectIdentifier)}:train`;

const EXPORT_MODEL = (modelIdentifier: ModelIdentifier, modelOnly = true): string => {
    return `${MODEL(modelIdentifier)}/export?model_only=${modelOnly}`;
};

const EXPORT_OPTIMIZED_MODEL = (
    modelIdentifier: ModelIdentifier,
    optimizedModelId: string,
    modelOnly = true
): string => {
    return `${MODEL(modelIdentifier)}/optimized_models/${optimizedModelId}/export?model_only=${modelOnly}`;
};

const OPTIMIZE_MODEL = (modelIdentifier: ModelIdentifier): string => `${MODEL(modelIdentifier)}:optimize`;

const JOBS = (workspaceIdentifier: WorkspaceIdentifier): string => `${WORKSPACE(workspaceIdentifier)}/jobs`;

const JOB = (workspaceIdentifier: WorkspaceIdentifier, jobId: string): string =>
    `${JOBS(workspaceIdentifier)}/${jobId}`;

const JOB_CANCEL = (workspaceIdentifier: WorkspaceIdentifier, jobId: string): string =>
    `${JOB(workspaceIdentifier, jobId)}:cancel`;

const JOBS_QUERY_PARAMS = (workspaceIdentifier: WorkspaceIdentifier, queryParams: JobsQueryParams): string => {
    const { projectId, jobState, jobTypes, key, author, startTimeFrom, startTimeTo, skip, limit, sortDirection } =
        queryParams;

    const baseUrl = `${JOBS(workspaceIdentifier)}?`;
    const params = new URLSearchParams([['sort_by', 'creation_time']]);

    if (projectId) params.append('project_id', projectId);
    if (jobState) params.append('state', jobState);
    if (jobTypes) jobTypes.forEach((jobType) => params.append('job_type', JobTypePayload[jobType]));
    if (key) params.append('key', key);
    if (author) params.append('author_id', author);
    if (startTimeFrom) params.append('start_time_from', startTimeFrom);
    if (startTimeTo) params.append('start_time_to', startTimeTo);
    if (skip) params.append('skip', skip.toString());
    if (limit) params.append('limit', limit.toString());
    // job_manager.py:89 use "desc"
    if (sortDirection) params.append('sort_direction', sortDirection === 'dsc' ? 'desc' : 'asc');

    return `${baseUrl}${params.toString()}`;
};

const STATUS = (organizationId?: string): string => {
    if (organizationId) {
        return `${API_VERSION}/organizations/${organizationId}/status`;
    }

    return `${API_VERSION}/status`;
};

const CONFIGURATION_PARAMETERS = (projectIdentifier: ProjectIdentifier): string =>
    `${PROJECT(projectIdentifier)}/configuration`;

const GLOBAL_CONFIGURATION_PARAMETERS = (projectIdentifier: ProjectIdentifier): string =>
    `${CONFIGURATION_PARAMETERS(projectIdentifier)}/global`;

const MODEL_CONFIG_PARAMETERS = (
    projectIdentifier: ProjectIdentifier,
    taskId: string,
    modelId?: string,
    modelTemplateId?: string | null
): string => {
    const baseUrl = `${CONFIGURATION_PARAMETERS(projectIdentifier)}/task_chain/${taskId}`;

    if (modelId) {
        return `${baseUrl}?model_id=${modelId}`;
    }

    if (modelTemplateId) {
        return `${baseUrl}?algorithm_name=${modelTemplateId}`;
    }

    return baseUrl;
};

const PROJECT_SUPPORTED_ALGORITHMS = (projectIdentifier: ProjectIdentifier): string =>
    `${PROJECT(projectIdentifier)}/supported_algorithms`;

const PRODUCT_INFO = `${API_VERSION}/product_info`;

const WORKFLOW_ID = `${API_VERSION}/users/workflow_id`;

const DATASET = {
    IMPORT_TUS: (workspaceIdentifier: WorkspaceIdentifier) => {
        return `${API}/${WORKSPACE(workspaceIdentifier)}/datasets/uploads/resumable`;
    },
    IMPORT_TUS_FILE: (workspaceIdentifier: WorkspaceIdentifier & { fileId: string }) => {
        return `${WORKSPACE(workspaceIdentifier)}/datasets/uploads/resumable/${workspaceIdentifier.fileId}`;
    },
    IMPORT_PREPARE: (workspaceIdentifier: WorkspaceIdentifier, uploadId: string): string => {
        return `${WORKSPACE(workspaceIdentifier)}/datasets:prepare-for-import?file_id=${uploadId}`;
    },
    IMPORT_CREATE: (workspaceIdentifier: WorkspaceIdentifier): string => {
        return `${WORKSPACE(workspaceIdentifier)}/projects:import-from-dataset`;
    },
    IMPORT_TO_EXISTING_PROJECT_PREPARE: (projectIdentifier: ProjectIdentifier, importDatasetId: string): string => {
        return `${PROJECT(projectIdentifier)}/datasets:prepare-for-import?file_id=${importDatasetId}`;
    },
    IMPORT_TO_EXISTING_PROJECT: (projectIdentifier: ProjectIdentifier): string => {
        return `${PROJECT(projectIdentifier)}:import-from-dataset`;
    },
    PREPARE_EXPORT: (
        datasetIdentifier: DatasetIdentifier,
        exportFormat: string,
        saveVideoAsImages: boolean
    ): string => {
        const urlParams = new URLSearchParams();
        urlParams.set('export_format', exportFormat);
        urlParams.set('save_video_as_images', String(saveVideoAsImages));

        return `${DATASET_URL(datasetIdentifier)}:prepare-for-export?${urlParams.toString()}`;
    },
    EXPORT_STATUS: (datasetIdentifier: DatasetIdentifier, exportDatasetId: string): string => {
        return `${DATASET_URL(datasetIdentifier)}/exports/${exportDatasetId}`;
    },
    EXPORT_DOWNLOAD: (datasetIdentifier: DatasetIdentifier, exportDatasetId: string): string => {
        return `${DATASET_URL(datasetIdentifier)}/exports/${exportDatasetId}/download`;
    },
    CREATE_DATASET: (projectIdentifier: ProjectIdentifier) => `${PROJECT(projectIdentifier)}/datasets`,
    DELETE_DATASET: (datasetIdentifier: DatasetIdentifier) => DATASET_URL(datasetIdentifier),
    UPDATE_DATASET: (datasetIdentifier: DatasetIdentifier) => DATASET_URL(datasetIdentifier),
};

// TODO
const PROJECT_IMPORT = {
    IMPORT_TUS: (workspaceIdentifier: WorkspaceIdentifier) =>
        `${API}/${WORKSPACE(workspaceIdentifier)}/projects/uploads/resumable`,
    IMPORT_PROJECT: (workspaceIdentifier: WorkspaceIdentifier): string => `${PROJECTS(workspaceIdentifier)}:import`,
    IMPORT_PROJECT_STATUS: (workspaceIdentifier: WorkspaceIdentifier, fileId: string): string =>
        `${PROJECTS(workspaceIdentifier)}/import/status/${fileId}`,
};

const FEATURE_FLAGS = `${API_VERSION}/feature_flags`;

const getAnalyticsUrl = (type: 'logs' | 'traces' | 'metrics' | 'k8s_logs' | 'k8s_metrics') => {
    const url = `${API}/${API_VERSION}/logs`;

    return (startDate: string, endDate: string): string => {
        const urlParams = new URLSearchParams();
        urlParams.set('type', type);
        urlParams.set('start_date', startDate);
        urlParams.set('end_date', endDate);

        return `${url}?${urlParams.toString()}`;
    };
};

const getServerInfoURL = () => {
    const url = `${API}/${API_VERSION}/logs`;

    const urlParams = new URLSearchParams();
    urlParams.set('type', 'cluster');

    return `${url}?${urlParams.toString()}`;
};

const ANALYTICS = {
    EXPORT_SERVER_LOGS: getAnalyticsUrl('k8s_logs'),
    EXPORT_LOGS: getAnalyticsUrl('logs'),
    EXPORT_SERVER_METRICS: getAnalyticsUrl('k8s_metrics'),
    EXPORT_METRICS: getAnalyticsUrl('metrics'),
    EXPORT_TRACES: getAnalyticsUrl('traces'),
    EXPORT_SERVER_INFO: getServerInfoURL(),
    DASHBOARD: `${API}/${API_VERSION}/grafana`,
    METRICS_EXPORTER: `${API}/${API_VERSION}/metrics`,
    TRACES_EXPORTER: `${API}/${API_VERSION}/traces`,
};

const TESTS = (projectIdentifier: ProjectIdentifier): string => `${PROJECT(projectIdentifier)}/tests`;

const TEST = (projectIdentifier: ProjectIdentifier, testId: string): string => `${TESTS(projectIdentifier)}/${testId}`;

const TEST_PREDICTIONS = (projectIdentifier: ProjectIdentifier, testId: string, predictionId: string): string =>
    `${TEST(projectIdentifier, testId)}/predictions/${predictionId}`;

const TEST_MEDIA_FILTER = (
    projectIdentifier: ProjectIdentifier,
    testId: string,
    mediaItemsLoadSize?: number,
    sortingOptions?: AdvancedFilterSortingOptions
): string => {
    const searchOptionsUrl = new URLSearchParams();

    if (sortingOptions?.sortBy) {
        searchOptionsUrl.set('sort_by', sortingOptions?.sortBy ?? 'score');
        searchOptionsUrl.set('sort_direction', sortingOptions?.sortDir ?? 'asc');
    }

    searchOptionsUrl.set('limit', mediaItemsLoadSize?.toString() ?? '');

    return `${TEST(projectIdentifier, testId)}/results:query?${searchOptionsUrl.toString()}`;
};

const DEPLOYMENT_PACKAGE_DOWNLOAD = (projectIdentifier: ProjectIdentifier): string => {
    return `${PROJECT(projectIdentifier)}/deployment_package:download`;
};

const USERS = (organizationId: string) => `${ORGANIZATION(organizationId)}/users`;

const CREATE_USER = (organizationId: string) => `${USERS(organizationId)}/create`;

const USER = (organizationId: string, userId: string) => `${ORGANIZATION(organizationId)}/users/${userId}`;

const USER_STATUSES = (organizationId: string, userId: string) =>
    `${ORGANIZATION(organizationId)}/users/${userId}/statuses`;

const PERSONAL_ACCESS_TOKENS = (organizationId: string, userId: string) =>
    `${ORGANIZATION(organizationId)}/users/${userId}/personal_access_tokens`;

const PERSONAL_ACCESS_TOKEN = (organizationId: string, userId: string, tokenId: string) =>
    `${PERSONAL_ACCESS_TOKENS(organizationId, userId)}/${tokenId}`;

const USER_PHOTO = (organizationId: string, userId: string) => `${USER(organizationId, userId)}/photos`;

const USER_ROLES = (organizationId: string, userId: string) => `${USER(organizationId, userId)}/roles`;

const USER_ROLES_RESOURCE = (organizationId: string, userId: string, resourceType: ResourceTypeDTO) =>
    `${USER_ROLES(organizationId, userId)}/${resourceType}`;

const INVITE_USER = (organizationId: string) => `${USERS(organizationId)}/invitations`;

const USERS_WITHOUT_ORGANIZATION_CONTEXT = `${API_VERSION}/users`;

const ACTIVE_USER = (organizationId: string) => `${ORGANIZATION(organizationId)}/activeUser`;

const USER_REGISTRATION = `${USERS_WITHOUT_ORGANIZATION_CONTEXT}/confirm_registration`;

const FORGOT_PASSWORD = `${USERS_WITHOUT_ORGANIZATION_CONTEXT}/request_password_reset`;

const RESET_PASSWORD = `${USERS_WITHOUT_ORGANIZATION_CONTEXT}/reset_password`;

const UPDATE_PASSWORD = (userId: string): string => `${USERS_WITHOUT_ORGANIZATION_CONTEXT}/${userId}/update_password`;

const PRODUCTS = () => `${API_VERSION}/products`;

const PRODUCT = (productId: number) => `${PRODUCTS()}/${productId}`;

const SUBSCRIPTIONS = (organizationId: string) => `${ORGANIZATION(organizationId)}/subscriptions`;

const ACTIVE_SUBSCRIPTION = (organizationId: string) => `${SUBSCRIPTIONS(organizationId)}/active`;

const ORGANIZATION_QUOTAS = (organizationId: string) => `${ACTIVE_SUBSCRIPTION(organizationId)}/quotas`;

const INVITE_ORGANIZATION = `${ORGANIZATIONS}/invitations`;

const USER_PROFILE = `${API_VERSION}/profile`;
const ONBOARDING = `${API_VERSION}/onboarding`;
const USER_ONBOARDING = `${ONBOARDING}/user`;
const GENERATE_ONBOARDING_TOKEN = `${API_VERSION}/admin/onboarding/tokens`;

const AUTH_COOKIE = `${API_VERSION}/set_cookie`;
const LOGOUT = `${API_VERSION}/logout`;

const MEMBERSHIP = {
    ROLES: (organizationId: string, memberId: string) => `${ORGANIZATION(organizationId)}/membership/${memberId}/roles`,
    DELETE_ROLE: (organizationId: string, memberId: string, { role, resourceId }: MemberRoleDTO) => {
        const searchParams = new URLSearchParams({
            resourceId,
            role,
        });

        return `${ORGANIZATION(organizationId)}/membership/${memberId}/roles?${searchParams.toString()}`;
    },
};

const CONFIGURATION = {
    TRAINING: (projectIdentifier: ProjectIdentifier) => `${PROJECT(projectIdentifier)}/training_configuration`,
    PROJECT: (projectIdentifier: ProjectIdentifier) => `${PROJECT(projectIdentifier)}/project_configuration`,
};

export const API_URLS = {
    PREFIX,
    WORKSPACES,
    WORKSPACE,
    PROJECTS,
    PROJECTS_SEARCH,
    PROJECT,
    PROJECT_NAMES,
    EXPORT_PROJECT,
    EXPORT_PROJECT_STATUS,
    EXPORT_PROJECT_DOWNLOAD,
    DATASET_URL,
    DATASET_DELETE_URL,
    DEPLOYMENT_PACKAGE_DOWNLOAD,
    ACTIVE_MEDIA,
    ADVANCED_DATASET_FILTER,
    ADVANCED_VIDEO_FRAMES_FILTER,
    TRAINING_ADVANCED_DATASET_FILTER,
    VIDEO_TRAINING_ADVANCED_DATASET_FILTER,
    MEDIA_UPLOAD,
    MEDIA_DELETE,
    MEDIA_ITEM,
    MEDIA_ITEM_SRC,
    MEDIA_ITEM_THUMBNAIL,
    MEDIA_ITEM_STREAM,
    ANNOTATIONS,
    SAVE_ANNOTATIONS,
    RANGE_ANNOTATIONS,
    PREDICTION,
    PIPELINES_STATUS,
    PREDICTION_NEW,
    BATCH_PREDICT,
    BATCH_PREDICT_STREAM,
    EXPLAIN_NEW,
    PREDICTION_SINGLE_IMAGE,
    INFERENCE_SERVER_STATUS,
    VISUAL_PROMPT_INFERENCE,
    ANNOTATIONS_STATISTICS,
    PROJECT_STATUS,
    MODELS,
    MODEL_GROUPS,
    MODEL,
    ACTIVATE_MODEL,
    ARCHIVE_MODEL,
    MODEL_STATISTICS,
    JOBS,
    JOB,
    JOB_CANCEL,
    JOBS_QUERY_PARAMS,
    STATUS,
    MANUAL_TRAIN_MODEL,
    CONFIGURATION_PARAMETERS,
    GLOBAL_CONFIGURATION_PARAMETERS,
    MODEL_CONFIG_PARAMETERS,
    PROJECT_SUPPORTED_ALGORITHMS,
    PROJECT_LABELS,
    EXPORT_MODEL,
    EXPORT_OPTIMIZED_MODEL,
    DATASET,
    OPTIMIZE_MODEL,
    PRODUCT_INFO,
    USER_REGISTRATION,
    FORGOT_PASSWORD,
    RESET_PASSWORD,
    UPDATE_PASSWORD,
    SERVICE_ACCOUNTS,
    TESTS,
    TEST,
    TEST_PREDICTIONS,
    TEST_MEDIA_FILTER,
    TRAINING_REVISION_URL,
    PROJECT_IMPORT,
    ANALYTICS,
    FEATURE_FLAGS,
    WORKFLOW_ID,
    ORGANIZATIONS,
    ORGANIZATION,
    ORGANIZATION_BALANCE,
    CREDIT_TRANSACTIONS,
    CREDIT_TRANSACTIONS_AGGREGATES,
    CREDIT_ACCOUNTS,
    CREDIT_ACCOUNT,
    CREDIT_ACCOUNT_BALANCE,
    ACTIVE_USER,
    CREATE_USER,
    USER,
    USER_STATUSES,
    PERSONAL_ACCESS_TOKENS,
    PERSONAL_ACCESS_TOKEN,
    USERS,
    USER_PHOTO,
    USER_ROLES,
    USER_ROLES_RESOURCE,
    INVITE_USER,
    PRODUCTS,
    PRODUCT,
    SUBSCRIPTIONS,
    ACTIVE_SUBSCRIPTION,
    ORGANIZATION_QUOTAS,
    INVITE_ORGANIZATION,
    USER_PROFILE,
    USER_ONBOARDING,
    GENERATE_ONBOARDING_TOKEN,
    AUTH_COOKIE,
    LOGOUT,
    GLOBAL_SETTINGS,
    PROJECT_SETTINGS,
    MEMBERSHIP,
    CONFIGURATION,
} as const;
