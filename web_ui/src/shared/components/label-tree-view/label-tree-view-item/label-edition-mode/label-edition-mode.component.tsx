// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef } from 'react';

import { isEmpty } from 'lodash-es';

import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeItem,
    LabelTreeLabelProps,
} from '../../../../../core/labels/label-tree-view.interface';
import { getLabelId } from '../../../../../core/labels/utils';
import { ColorPickerDialog } from '../../../../../pages/create-project/components/project-labels-management/task-labels-management/color-picker-dialog.component';
import { useUsedAnnotatorHotkeys } from '../../../../../pages/create-project/components/use-used-annotator-hotkeys.hook';
import { newLabelHotkeySchema, newLabelNameSchema } from '../../../../../pages/create-project/components/utils';
import { getUnremovedLabels } from '../../../../../pages/project-details/components/project-labels/utils';
import { isYupValidationError } from '../../../../../pages/user-management/profile-page/utils';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { ValidationErrorMsg } from '../../../validation-error-msg/validation-error-msg.component';
import { getEditedItem } from '../../utils';
import { ItemEditionState } from '../item-edition-state/item-edition-state.component';
import { HotkeyNameField } from '../label-presentation-mode/hotkey-name-field/hotkey-name-field.component';
import { TreeViewItemEditModeProps } from '../label-tree-view-item.interface';
import { DEFAULT_LABEL_INPUT_ERRORS } from '../utils';
import { LabelEditionFieldsWrapper } from './label-edition-fields-wrapper.component';
import { NameEditionField } from './name-edition-field/name-edition-field.component';

export const LabelEditionMode = ({
    item: label,
    savedItem: savedLabel,
    flatListProjectItems: flatProjectLabels,
    save,
    domains,
    setValidationError,
    validationErrors,
    newTree,
}: TreeViewItemEditModeProps<LabelTreeLabelProps>): JSX.Element => {
    const wrapperRef = useRef(null);

    const isFocus = useRef(false);
    const usedAnnotatorHotkeys = useUsedAnnotatorHotkeys(domains);

    const nameValidationError = validationErrors ? validationErrors.name : '';
    const hotkeyValidationError = validationErrors ? validationErrors.hotkey : '';
    const hasInputChanged = [LabelItemEditionState.CHANGED, LabelItemEditionState.NEW].includes(label.state);

    useEffect(() => {
        if (!isFocus.current && hasInputChanged && nameValidationError !== '') {
            errorHandler(label.name);
        }
    });

    const validateAttribute = (
        value: string | undefined,
        id: string,
        labels: LabelTreeItem[],
        attribute: 'name' | 'hotkey'
    ): string => {
        let validationError = DEFAULT_LABEL_INPUT_ERRORS[attribute];

        try {
            if (attribute === 'name') {
                newLabelNameSchema(value, id, labels, LabelItemType.LABEL).validateSync({ name: value });
            }
            if (attribute === 'hotkey') {
                newLabelHotkeySchema(id, labels, usedAnnotatorHotkeys).validateSync({ hotkey: value });
            }
        } catch (errors: unknown) {
            if (isYupValidationError(errors)) {
                validationError = errors.errors[0];
            }
        }
        return validationError;
    };

    const saveHandler = (attribute: 'hotkey' | 'name' | 'color', value: string | undefined) => {
        const labelToSave = getEditedItem({ ...label, [attribute]: value }, savedLabel) as LabelTreeLabelProps;

        save(labelToSave);
    };

    const onHotkeyChangeHandler = (newHotkey: string | undefined) => {
        const hotkeyValidationResult = validateHotkey(newHotkey);

        if (isEmpty(hotkeyValidationResult)) {
            validationErrors && delete validationErrors['hotkey'];
            setValidationError(label.id, validationErrors);
        } else {
            setValidationError(label.id, {
                ...validationErrors,
                hotkey: validateHotkey(newHotkey),
            });
        }

        saveHandler('hotkey', newHotkey);
    };

    const errorHandler = (newValue: string | undefined) => {
        const nameValidationResult = validateName(newValue);

        if (nameValidationError === nameValidationResult) {
            return;
        }

        if (isEmpty(nameValidationResult)) {
            validationErrors && delete validationErrors['name'];
            setValidationError(label.id, validationErrors);
        } else {
            setValidationError(label.id, {
                ...validationErrors,
                name: nameValidationResult,
            });
        }
    };

    const onColorChangeHandler = (color: string) => {
        saveHandler('color', color);
    };

    const validateName = (newValue: string | undefined): string => {
        return validateAttribute(newValue, label.id, flatProjectLabels, 'name');
    };

    const validateHotkey = (newHotkey: string | undefined): string => {
        const labelsWithoutRemoved = getUnremovedLabels(flatProjectLabels);

        return validateAttribute(newHotkey, label.id, labelsWithoutRemoved, 'hotkey');
    };

    return (
        <LabelEditionFieldsWrapper wrapperRef={wrapperRef}>
            <ColorPickerDialog
                color={label.color}
                onColorChange={onColorChangeHandler}
                id={`${getLabelId('tree', label)}-color`}
                size={'S'}
                gridArea={'color'}
                ariaLabelPrefix={label.name}
            />
            <NameEditionField
                value={label.name}
                error={nameValidationError}
                gridArea={'name'}
                labelState={label.state}
                onChange={(newValue) => {
                    errorHandler(newValue);
                    saveHandler('name', newValue);
                }}
                onFocusChange={(focus) => (isFocus.current = focus)}
            />
            <ValidationErrorMsg errorMsg={nameValidationError} gridArea={'nameError'} inheritHeight />

            <HotkeyNameField
                text={'+ Add hotkey'}
                value={label.hotkey}
                onChange={onHotkeyChangeHandler}
                error={hotkeyValidationError}
                gridArea={'hotkey'}
            />
            <ValidationErrorMsg errorMsg={hotkeyValidationError} gridArea={'hotkeyError'} inheritHeight />
            {!newTree && <ItemEditionState state={label.state} idSuffix={idMatchingFormat(label.name)} />}
        </LabelEditionFieldsWrapper>
    );
};
