// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef, useState } from 'react';

import { Flex, Switch, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { TextFieldRef } from '@react-types/textfield';
import { isEmpty } from 'lodash-es';
import { ValidationError } from 'yup';

import { LabelItemType, LabelTreeGroupProps } from '../../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../../core/labels/label.interface';
import { newLabelNameSchema } from '../../../../../pages/create-project/components/utils';
import { isYupValidationError } from '../../../../../pages/user-management/profile-page/utils';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { LimitedTextField } from '../../../limited-text-field/limited-text-field.component';
import { PressableElement } from '../../../pressable-element/pressable-element.component';
import { ValidationErrorMsg } from '../../../validation-error-msg/validation-error-msg.component';
import { getEditedItem } from '../../utils';
import { ItemEditionState } from '../item-edition-state/item-edition-state.component';
import { TreeViewItemEditModeProps } from '../label-tree-view-item.interface';
import { isNewState } from '../utils';
import { MULTIPLE_SELECTION_SWITCH_TOOLTIP, NEW_GROUP_FIELD_TOOLTIP } from './utils';

type GroupEditionModeProps = Omit<TreeViewItemEditModeProps<LabelTreeGroupProps>, 'domains'>;

enum ErrorPath {
    NEW_LABEL_NAME = 'name',
}

export const GroupEditionMode = ({
    flatListProjectItems: flatProjectGroups,
    save,
    item: group,
    savedItem: savedGroup,
    validationErrors,
    setValidationError,
    newTree,
}: GroupEditionModeProps): JSX.Element => {
    const DEFAULT_ERROR = '';
    const nameValidationError = validationErrors ? validationErrors.name : DEFAULT_ERROR;
    const [isMultipleSelectionOn, setIsMultipleSelectionOn] = useState(
        group.relation === LabelsRelationType.MULTI_SELECTION
    );

    const setMultipleSelectionOnHandler = (value: boolean) => {
        setIsMultipleSelectionOn(value);
        saveHandler({ multipleSelection: value });
    };

    const inputRef = useRef<TextFieldRef>(null);

    useEffect(() => {
        isNewState(group.state) && inputRef.current?.select();

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const saveHandler = (options: { name?: string; multipleSelection?: boolean }) => {
        const changedIsMultipleSelectionOn =
            options.multipleSelection !== undefined ? options.multipleSelection : isMultipleSelectionOn;
        const relation = changedIsMultipleSelectionOn
            ? LabelsRelationType.MULTI_SELECTION
            : LabelsRelationType.SINGLE_SELECTION;

        let updatedGroup: LabelTreeGroupProps = {
            ...group,
            relation,
        };

        if (options.name !== undefined) {
            updatedGroup = {
                ...updatedGroup,
                name: options.name,
            };
        }

        save(getEditedItem(updatedGroup, savedGroup) as LabelTreeGroupProps);
    };

    const validateName = (changedName: string): void => {
        let validationError = DEFAULT_ERROR;

        try {
            newLabelNameSchema(changedName, group?.id, flatProjectGroups, LabelItemType.GROUP).validateSync(
                { name: changedName },
                { abortEarly: false }
            );
        } catch (errors) {
            if (isYupValidationError(errors)) {
                errors.inner.forEach(({ path, message }: ValidationError) => {
                    if (path === ErrorPath.NEW_LABEL_NAME) {
                        validationError = message;
                    }
                });
            }
        } finally {
            if (isEmpty(validationError)) {
                validationErrors && delete validationErrors['name'];
                setValidationError(group.id, validationErrors);
            } else {
                setValidationError(group.id, {
                    ...validationErrors,
                    name: validationError,
                });
            }
        }
    };

    const handleNameChange = (value: string) => {
        validateName(value);
        saveHandler({ name: value });
    };

    return (
        <Flex direction={'column'} width={'100%'}>
            <Flex alignItems={'center'} justifyContent={'space-between'}>
                <Flex gap={'size-100'} width={'100%'} alignItems={'center'}>
                    <Flex width={'100%'}>
                        <TooltipTrigger placement={'top'}>
                            <LimitedTextField
                                ref={inputRef}
                                value={group?.name}
                                width={'100%'}
                                onChange={handleNameChange}
                                placeholder={'Label group name'}
                                aria-label={'Label group name'}
                                data-testid={`${
                                    isEmpty(group?.name) ? 'empty' : group?.name
                                }-project-label-group-input-id`}
                                id={`${isEmpty(group?.name) ? 'empty' : group?.name}-project-label-group-input-id`}
                            />
                            <Tooltip>{NEW_GROUP_FIELD_TOOLTIP}</Tooltip>
                        </TooltipTrigger>
                    </Flex>

                    <TooltipTrigger placement={'top'}>
                        <PressableElement>
                            <Text UNSAFE_style={{ whiteSpace: 'nowrap' }} key={'multiple-selection-text'}>
                                Multiple selection
                            </Text>
                        </PressableElement>
                        <Tooltip>{MULTIPLE_SELECTION_SWITCH_TOOLTIP}</Tooltip>
                    </TooltipTrigger>

                    <TooltipTrigger placement={'top'}>
                        <Switch
                            key={'multiple-selection-switch'}
                            onChange={setMultipleSelectionOnHandler}
                            isSelected={isMultipleSelectionOn}
                            width={'size-1200'}
                        >
                            {isMultipleSelectionOn ? 'On' : 'Off'}
                        </Switch>
                        <Tooltip>{MULTIPLE_SELECTION_SWITCH_TOOLTIP}</Tooltip>
                    </TooltipTrigger>
                </Flex>

                {!newTree && <ItemEditionState state={group.state} idSuffix={idMatchingFormat(group.name)} />}
            </Flex>
            <ValidationErrorMsg inheritHeight errorMsg={nameValidationError} />
        </Flex>
    );
};
