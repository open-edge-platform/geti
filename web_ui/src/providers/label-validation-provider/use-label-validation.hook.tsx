// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useState } from 'react';

import { LabelItemType } from '../../core/labels/label-tree-view.interface';
import { newLabelHotkeySchema, newLabelNameSchema } from '../../pages/create-project/components/utils';
import { isYupValidationError } from '../../pages/user-management/profile-page/utils';
import {
    DEFAULT_LABEL_INPUT_DIRTY,
    DEFAULT_LABEL_INPUT_ERRORS,
    LabelFieldsDirty,
    LabelFieldsErrors,
} from '../../shared/components/label-tree-view/label-tree-view-item/utils';
import { UseLabelValidationProps, UseLabelValidationResult } from './label-validation-types';

export function useLabelValidation({
    initialName = '',
    initialHotkey = '',
    projectLabels = [],
    labelType = LabelItemType.LABEL,
    currentLabelId,
    usedAnnotatorHotkeys = [],
    setDialogValidationError,
}: UseLabelValidationProps): UseLabelValidationResult {
    const [validationErrors, setValidationErrors] = useState<LabelFieldsErrors>(DEFAULT_LABEL_INPUT_ERRORS);
    const [isDirty, setDirty] = useState<LabelFieldsDirty>(DEFAULT_LABEL_INPUT_DIRTY);

    const validateName = useCallback(
        (changedName: string): boolean => {
            try {
                newLabelNameSchema(changedName, currentLabelId, projectLabels, labelType).validateSync(
                    { name: changedName },
                    { abortEarly: false }
                );
                // Always clear error on success
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

    const updateDialogValidationError = useCallback(() => {
        if (setDialogValidationError) {
            const formHasError = Object.values(validationErrors).some(Boolean);

            setDialogValidationError(formHasError ? 'Fix all the errors before moving forward' : undefined);
        }
    }, [setDialogValidationError, validationErrors]);

    return {
        validationErrors,
        setValidationErrors,
        isDirty,
        setDirty,
        validateName,
        validateHotkey,
        updateDialogValidationError,
        hasError: Object.values(validationErrors).some(Boolean),
    };
}
