// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export enum ACTION_TYPES {
    ENABLEMENT,
}

interface CPRule {
    groupTitle: string;
    action: ACTION_TYPES.ENABLEMENT;
    switchFieldName: string;
    groupFields: string[];
}
export const CP_RULES: CPRule[] = [
    {
        groupTitle: 'Tiling',
        action: ACTION_TYPES.ENABLEMENT,
        switchFieldName: 'enable_tiling',
        groupFields: ['tile_max_number', 'tile_overlap', 'tile_sampling_ratio', 'tile_size'],
    },
];
