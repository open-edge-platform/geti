// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type {
    CreateProjectLabelName,
    CreateProjectRequest,
    CreateProjectResponse,
    CreateProjectTaskType,
} from '@/api/types';
import { Page } from '@playwright/test';

export type CreateProjectInput = {
    projectName?: CreateProjectRequest['name'];
    projectNamePrefix?: string;
    task: CreateProjectTaskType;
    labels: CreateProjectLabelName[];
};

export type UploadMediaItem = {
    name: string;
    mimeType: string;
    buffer: Buffer;
};

export type CreatedProject = Pick<CreateProjectResponse, 'id' | 'name'>;

export type InferenceSourceSinkConfig = {
    sourceName: string;
    sinkName: string;
    sinkFolderPath: string;
    rateLimitSamples: number;
    rateLimitSeconds: number;
};

export type FlowInput = {
    page: Page;
    projectNamePrefix: string;
};
