// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useState } from 'react';

import { LabelItemType, LabelTreeItem } from '../../core/labels/label-tree-view.interface';
import { DOMAIN } from '../../core/projects/core.interface';
import { newLabelHotkeySchema, newLabelNameSchema } from '../../pages/create-project/components/utils';
import { validateLabelsSchema } from '../../pages/create-project/utils';
import { isYupValidationError } from '../../pages/user-management/profile-page/utils';
import {
    DEFAULT_LABEL_INPUT_DIRTY,
    DEFAULT_LABEL_INPUT_ERRORS,
    LabelFieldsDirty,
    LabelFieldsErrors,
} from '../../shared/components/label-tree-view/label-tree-view-item/utils';
import { UseLabelValidationProps, UseLabelValidationResult } from './label-validation-types';

export function useLabelValidation({
    projectLabels = [],
    labelType = LabelItemType.LABEL,
    currentLabelId,
    usedAnnotatorHotkeys = [],
    setDialogValidationError,
    domain,
    labels,
}: UseLabelValidationProps & { domain?: DOMAIN; labels?: LabelTreeItem[] }): UseLabelValidationResult {
    const [validationErrors, setValidationErrors] = useState<LabelFieldsErrors>(DEFAULT_LABEL_INPUT_ERRORS);
    const [treeValidationError, setTreeValidationError] = useState<string | undefined>(undefined);
    const [isDirty, setDirty] = useState<LabelFieldsDirty>(DEFAULT_LABEL_INPUT_DIRTY);

    // Field-level validation
    const validateName = useCallback(
        (changedName: string): boolean => {
            try {
                newLabelNameSchema(changedName, currentLabelId, projectLabels, labelType).validateSync(
                    { name: changedName },
                    { abortEarly: false }
                );
                setValidationErrors((prev) => ({ ...prev, name: '' }));

                return true;
            } catch (errors: unknown) {
                if (isYupValidationError(errors)) {
                    setValidationErrors((prev) => ({ ...prev, name: errors.errors[0] }));
                }

                return false;
            }
        },
        [currentLabelId, projectLabels, labelType]
    );

    const validateHotkey = useCallback(
        (changedHotkey: string | undefined): boolean => {
            try {
                newLabelHotkeySchema(currentLabelId, projectLabels, usedAnnotatorHotkeys).validateSync({
                    hotkey: changedHotkey,
                });
                setValidationErrors((prev) => ({ ...prev, hotkey: '' }));

                return true;
            } catch (errors: unknown) {
                if (isYupValidationError(errors)) {
                    setValidationErrors((prev) => ({ ...prev, hotkey: errors.errors[0] }));
                }

                return false;
            }
        },
        [currentLabelId, projectLabels, usedAnnotatorHotkeys]
    );

    // Tree-level validation
    const validateTree = useCallback(() => {
        if (!domain || !labels) return true;

        try {
            validateLabelsSchema(domain).validateSync({ labels }, { abortEarly: false });
            setTreeValidationError(undefined);

            return true;
        } catch (error: unknown) {
            if (isYupValidationError(error)) {
                setTreeValidationError(error.errors.join('\r\n'));
            }

            return false;
        }
    }, [domain, labels]);

    const hasError = Object.values(validationErrors).some(Boolean) || Boolean(treeValidationError);

    // TODO: might be removed after the refactor
    const updateDialogValidationError = useCallback(() => {
        if (setDialogValidationError) {
            setDialogValidationError(hasError ? 'Fix all the errors before moving forward' : undefined);
        }
    }, [setDialogValidationError, hasError]);

    return {
        validationErrors,
        setValidationErrors,
        isDirty,
        setDirty,
        validateName,
        validateHotkey,
        validateTree,
        treeValidationError,
        updateDialogValidationError,
        hasError,
    };
}
