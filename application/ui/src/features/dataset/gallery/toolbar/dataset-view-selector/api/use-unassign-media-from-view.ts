// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { $api } from '@/api';

export const useUnassignMediaFromViewMutation = () => {
    return $api.useMutation('delete', '/api/projects/{project_id}/dataset/views/{dataset_view_id}/media');
};
