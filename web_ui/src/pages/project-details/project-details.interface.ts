// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface SelectableOptimizationType {
    text: string;
    id: string;
}

export interface PreselectedModel {
    groupName: string;
    groupId: string;
    templateName: string;
    version: number;
    id: string;
    taskId: string;
    optimizedModel?: SelectableOptimizationType;
}
