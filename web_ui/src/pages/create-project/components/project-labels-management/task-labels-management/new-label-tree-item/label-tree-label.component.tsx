// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, ForwardedRef, forwardRef, useEffect, useMemo, useRef, useState } from 'react';

import { Button, Flex, Form, type TextFieldRef } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeItem,
    LabelTreeLabelProps,
} from '../../../../../../core/labels/label-tree-view.interface';
import { getFlattenedLabels } from '../../../../../../core/labels/utils';
import { DOMAIN } from '../../../../../../core/projects/core.interface';
import { TaskMetadata } from '../../../../../../core/projects/task.interface';
import { LabelEditionFieldsWrapper } from '../../../../../../shared/components/label-tree-view/label-tree-view-item/label-edition-mode/label-edition-fields-wrapper.component';
import { HotkeyNameField } from '../../../../../../shared/components/label-tree-view/label-tree-view-item/label-presentation-mode/hotkey-name-field/hotkey-name-field.component';
import {
    DEFAULT_LABEL_INPUT_DIRTY,
    DEFAULT_LABEL_INPUT_ERRORS,
    LabelFieldsDirty,
    LabelFieldsErrors,
} from '../../../../../../shared/components/label-tree-view/label-tree-view-item/utils';
import {
    DEFAULT_LABEL,
    getDefaultGroupName,
    getGroupBasedOnRelationType,
    getNextColor,
} from '../../../../../../shared/components/label-tree-view/utils';
import { LimitedTextField } from '../../../../../../shared/components/limited-text-field/limited-text-field.component';
import { ValidationErrorMsg } from '../../../../../../shared/components/validation-error-msg/validation-error-msg.component';
import { isYupValidationError } from '../../../../../user-management/profile-page/utils';
import { useUsedAnnotatorHotkeys } from '../../../use-used-annotator-hotkeys.hook';
import { newLabelHotkeySchema, newLabelNameSchema } from '../../../utils';
import { LABEL_TREE_TYPE } from '../../label-tree-type.enum';
import { ColorPickerDialog } from '../color-picker-dialog.component';
import { Label } from './label/label.component';

interface NewLabelProps {
    type: LABEL_TREE_TYPE;
    addLabel: (label: LabelTreeItem, shouldGoNext?: boolean) => void;
    taskMetadata: TaskMetadata;
    projectLabels: LabelTreeItem[];
    color?: string;
    hotkey?: string;
    name: string;
    withLabel?: boolean;
    setDialogValidationError?: (message: string | undefined) => void;
    domains: DOMAIN[];
    shouldFocus?: boolean;
    parentGroupName?: string | null;
}

export const LabelTreeLabel = forwardRef(
    (
        {
            type,
            addLabel,
            color,
            name,
            hotkey,
            projectLabels,
            withLabel = false,
            setDialogValidationError,
            domains,
            shouldFocus,
            taskMetadata,
            parentGroupName = null,
        }: NewLabelProps,
        ref: ForwardedRef<never>
    ): JSX.Element => {
        const isSingleLabelTree = type === LABEL_TREE_TYPE.SINGLE;

        const { labels, domain, relation } = taskMetadata;

        const [newColor, setNewColor] = useState<string | undefined>(color || getNextColor(labels));
        const [newName, setNewName] = useState<string>(name);
        const [newHotkey, setNewHotkey] = useState<string | undefined>(hotkey);
        const [validationErrors, setValidationErrors] = useState<LabelFieldsErrors>(DEFAULT_LABEL_INPUT_ERRORS);
        const [isDirty, setDirty] = useState<LabelFieldsDirty>(DEFAULT_LABEL_INPUT_DIRTY);
        const usedAnnotatorHotkeys = useUsedAnnotatorHotkeys(domains);

        const inputRef = useRef<TextFieldRef>(null);

        const projectLabelsFlattenedWithoutGroups = useMemo(() => getFlattenedLabels(projectLabels), [projectLabels]);

        const handleColorChange = (c: string) => {
            setNewColor(c);
        };

        const formHasError = useMemo(() => {
            const hasError = Object.values(validationErrors).some((error) => !!error);

            if (isSingleLabelTree && !!setDialogValidationError && (isDirty.name || isDirty.hotkey)) {
                setDialogValidationError(hasError ? 'Fix all the errors before moving forward' : undefined);
            }

            return hasError;
        }, [isSingleLabelTree, setDialogValidationError, validationErrors, isDirty]);

        const cleanForm = (newLabel: LabelTreeLabelProps) => {
            setNewName('');
            setNewHotkey('');
            handleColorChange(getNextColor([...labels, newLabel]));

            shouldFocus && inputRef.current && inputRef.current.focus();

            validateName('');
            setDirty(DEFAULT_LABEL_INPUT_DIRTY);
        };

        const confirmNewLabel = (
            shouldGoNext = true,
            labelValue?: Partial<LabelTreeLabelProps>
        ): LabelTreeLabelProps => {
            const defaultGroupName = getDefaultGroupName(domain, parentGroupName);
            const groupName = getGroupBasedOnRelationType(relation, defaultGroupName, newName);
            const defaultLabel = DEFAULT_LABEL({
                name: newName.trim(),
                color: newColor || color || getNextColor(labels),
                groupName,
                relation,
                inEditMode: false,
                parentLabelId: null,
                state: LabelItemEditionState.IDLE,
                hotkey: newHotkey,
            });
            const newLabel = { ...defaultLabel, ...labelValue };

            addLabel(newLabel, shouldGoNext);

            return newLabel;
        };

        const handleOnSubmit = (event: FormEvent) => {
            if (!formHasError) {
                const newLabel = confirmNewLabel();

                if (!isSingleLabelTree) {
                    shouldFocus && inputRef.current && inputRef.current.focus();
                    cleanForm(newLabel);
                }
            }

            event.preventDefault();
        };

        const validateName = (changedName: string): boolean => {
            try {
                const currentLabelId = isSingleLabelTree && labels.length >= 1 ? labels[0].id : undefined;

                newLabelNameSchema(
                    changedName,
                    currentLabelId,
                    projectLabelsFlattenedWithoutGroups,
                    LabelItemType.LABEL
                ).validateSync({ name: changedName }, { abortEarly: false });

                validationErrors.name &&
                    setValidationErrors(() => ({ ...validationErrors, name: DEFAULT_LABEL_INPUT_ERRORS.name }));

                return true;
            } catch (errors: unknown) {
                if (isYupValidationError(errors)) {
                    setValidationErrors({ ...validationErrors, name: errors.errors[0] });
                }
                return false;
            }
        };

        const validateHotkey = (changedHotkey: string | undefined): boolean => {
            try {
                const currentLabelId = isSingleLabelTree && labels.length >= 1 ? labels[0].id : undefined;

                newLabelHotkeySchema(
                    currentLabelId,
                    projectLabelsFlattenedWithoutGroups,
                    usedAnnotatorHotkeys
                ).validateSync({
                    hotkey: changedHotkey,
                });

                validationErrors.hotkey &&
                    setValidationErrors(() => ({ ...validationErrors, hotkey: DEFAULT_LABEL_INPUT_ERRORS.hotkey }));

                return true;
            } catch (errors: unknown) {
                if (isYupValidationError(errors)) {
                    setValidationErrors({ ...validationErrors, hotkey: errors.errors[0] });
                }

                return false;
            }
        };

        const handleNameChange = (value: string) => {
            setDirtyOnChange('name');

            const nameValid = validateName(value);
            setNewName(value);

            if (isSingleLabelTree && nameValid) {
                confirmNewLabel(false, { name: value });
            }
        };

        const setDirtyOnChange = (key: 'name' | 'hotkey') => {
            if (!isDirty[key]) {
                setDirty({ ...isDirty, [key]: true });
            }
        };

        const handleHotkeyChange = (value: string | undefined) => {
            setDirtyOnChange('hotkey');

            const hotkeyValid = validateHotkey(value);

            setNewHotkey(value);

            if (isSingleLabelTree && hotkeyValid) {
                confirmNewLabel(false, { hotkey: value });
            }
        };

        useEffect(() => {
            // Set focus on name field on mounting
            inputRef.current && inputRef.current.focus();
        }, []);

        useEffect(() => {
            validateName(newName);

            // eslint-disable-next-line react-hooks/exhaustive-deps
        }, [projectLabelsFlattenedWithoutGroups]);

        return (
            <Form onSubmit={handleOnSubmit}>
                <Flex direction={'column'} ref={ref} marginBottom={'size-100'}>
                    {withLabel && <Label htmlFor={'project-label-name-input-id'}>Label</Label>}
                    <LabelEditionFieldsWrapper>
                        <ColorPickerDialog
                            color={newColor}
                            id={'change-color-button'}
                            data-testid={'change-color-button'}
                            onColorChange={handleColorChange}
                            size={'S'}
                            gridArea={'color'}
                            ariaLabelPrefix={newName}
                        />

                        <ValidationErrorMsg
                            errorMsg={isDirty.name ? validationErrors.name : ''}
                            gridArea={'nameError'}
                            inheritHeight
                        />

                        <LimitedTextField
                            ref={inputRef}
                            width={'100%'}
                            value={newName}
                            onChange={handleNameChange}
                            placeholder={'Label name'}
                            id={'project-label-name-input-id'}
                            aria-label={'Project label name input'}
                            gridArea={'name'}
                        />

                        <HotkeyNameField
                            text={'+ Add hotkey'}
                            value={newHotkey}
                            onChange={handleHotkeyChange}
                            error={isDirty.hotkey ? validationErrors.hotkey : ''}
                            gridArea={'hotkey'}
                        />

                        <ValidationErrorMsg
                            errorMsg={isDirty.hotkey ? validationErrors.hotkey : ''}
                            gridArea={'hotkeyError'}
                            inheritHeight
                        />

                        {isSingleLabelTree ? (
                            <></>
                        ) : (
                            <Button
                                variant={'secondary'}
                                isDisabled={formHasError || isEmpty(newName)}
                                type='submit'
                                data-testid={'add-label-button'}
                                id={'add-label-button'}
                                gridArea={'actionButtons'}
                                UNSAFE_style={{ whiteSpace: 'nowrap' }}
                            >
                                Create label
                            </Button>
                        )}
                    </LabelEditionFieldsWrapper>
                </Flex>
            </Form>
        );
    }
);
