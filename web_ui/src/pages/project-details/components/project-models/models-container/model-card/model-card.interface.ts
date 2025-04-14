// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ModelVersion } from '../../../../../../core/models/models.interface';

export type { ModelVersion } from '../../../../../../core/models/models.interface';

export interface ModelCardProps {
    taskId: string;
    model: ModelVersion;
    isLatestModel: boolean; // latest model from the architecture
    modelTemplateId: string;
    isMenuOptionsDisabled: boolean;
    complexity: number | undefined;
}
