// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';

export const useAssignMediaToExistingDatasetView = () => {
    return $api.useMutation('post', '/api/projects/{project_id}/dataset/views/{dataset_view_id}/media');
};
