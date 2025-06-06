// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

interface LabelCommon {
    name: string;
    color: string;
    group: string;
    hotkey?: string;
    is_empty: boolean;
    is_background: boolean;
    parent_id: string | null;
}

export type LabelCreation = Omit<LabelCommon, 'is_empty' | 'is_background'>;

export interface LabelDTO extends LabelCommon {
    id: string;
    is_anomalous: boolean;
}

export interface NewLabelDTO extends LabelCommon {
    revisit_affected_annotations: boolean;
}

export interface RevisitLabelDTO extends LabelCommon {
    id: string;
    revisit_affected_annotations: boolean;
}

export interface DeletedLabelDTO extends LabelDTO {
    is_deleted: boolean;
}
export type EditedLabelDTO = DeletedLabelDTO | RevisitLabelDTO | NewLabelDTO | LabelDTO;
