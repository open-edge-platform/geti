// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Label } from '../../../../../core/labels/label.interface';

export interface TrainingDatasetProps {
    revisionId: string;
    storageId: string;
    modelInformation: string;
    modelLabels: Label[];
    taskId: string;
    isActive: boolean;
}
