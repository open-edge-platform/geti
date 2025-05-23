// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { LabelItemType, LabelTreeItem } from '../../core/labels/label-tree-view.interface';
import { DOMAIN } from '../../core/projects/core.interface';
import {
    LabelFieldsDirty,
    LabelFieldsErrors,
} from '../../shared/components/label-tree-view/label-tree-view-item/utils';

export interface UseLabelValidationProps {
    initialName?: string;
    initialHotkey?: string;
    projectLabels?: LabelTreeItem[];
    labelType?: LabelItemType;
    currentLabelId?: string;
    usedAnnotatorHotkeys?: string[];
    setDialogValidationError?: (msg: string | undefined) => void;
    domain?: DOMAIN;
    labels?: LabelTreeItem[];
}

export interface UseLabelValidationResult {
    validationErrors: LabelFieldsErrors;
    setValidationErrors: React.Dispatch<React.SetStateAction<LabelFieldsErrors>>;
    isDirty: LabelFieldsDirty;
    setDirty: React.Dispatch<React.SetStateAction<LabelFieldsDirty>>;
    validateName: (changedName: string) => boolean;
    validateHotkey: (changedHotkey: string | undefined) => boolean;
    validateTree: () => boolean;
    treeValidationError: string | undefined;
    updateDialogValidationError: () => void;
    hasError: boolean;
}
