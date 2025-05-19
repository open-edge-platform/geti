// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FormEvent, useEffect, useRef, useState } from 'react';

import { Button, Flex, PressableElement, Switch, Text, Tooltip, TooltipTrigger } from '@geti/ui';
import { TextFieldRef } from '@react-types/textfield';
import { isEmpty } from 'lodash-es';
import { ValidationError } from 'yup';

import {
    LabelItemType,
    LabelTreeGroupProps,
    LabelTreeItem,
} from '../../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../../core/labels/label.interface';
import { filterGroups } from '../../../../../core/labels/utils';
import { newLabelNameSchema } from '../../../../../pages/create-project/components/utils';
import { isYupValidationError } from '../../../../../pages/user-management/profile-page/utils';
import { LimitedTextField } from '../../../limited-text-field/limited-text-field.component';
import { ValidationErrorMsg } from '../../../validation-error-msg/validation-error-msg.component';
import { getNewGroup } from '../../utils';
import { MULTIPLE_SELECTION_SWITCH_TOOLTIP, NEW_GROUP_FIELD_TOOLTIP } from './utils';

interface GroupCreationProps {
    flatProjectItems: LabelTreeItem[];
    save: (editedGroup: LabelTreeGroupProps) => void;
    parentGroupName: string | null;
    parentLabelId: string | null;
}

export const GroupCreation = ({
    flatProjectItems,
    save,
    parentGroupName,
    parentLabelId,
}: GroupCreationProps): JSX.Element => {
    const DEFAULT_ERROR = '';
    const [error, setError] = useState<string>(DEFAULT_ERROR);
    const [isDirty, setDirty] = useState<{ name: boolean; mode: boolean }>({ name: false, mode: false });
    const [name, setName] = useState<string>('');
    const [multipleSelectionOn, setMultipleSelectionOn] = useState(false);

    const flatProjectGroups = filterGroups(flatProjectItems);
    const inputRef = useRef<TextFieldRef>(null);

    const validateName = (changedName: string): void => {
        setError(DEFAULT_ERROR);

        try {
            newLabelNameSchema(changedName, undefined, flatProjectGroups, LabelItemType.GROUP).validateSync(
                { name: changedName },
                { abortEarly: false }
            );
        } catch (validationError) {
            if (isYupValidationError(validationError)) {
                validationError.inner.forEach(({ message }: ValidationError) => {
                    setError(message);
                });
            }
        }
    };

    useEffect(() => {
        //Note: validate name at the beginning to disable create button
        validateName(name);
        inputRef.current?.focus();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const setMultipleSelectionOnHandler = (value: boolean) => {
        setMultipleSelectionOn(value);
        setDirty({ ...isDirty, mode: true });
    };

    const clear = () => {
        setName('');
        setDirty({ name: false, mode: false });
        setMultipleSelectionOn(false);
        validateName('');
    };

    const saveHandler = (event: FormEvent) => {
        const currentRelation = multipleSelectionOn
            ? LabelsRelationType.MULTI_SELECTION
            : LabelsRelationType.SINGLE_SELECTION;
        save(getNewGroup(name, currentRelation, flatProjectItems, parentGroupName, parentLabelId));
        clear();
        event.preventDefault();
    };

    const handleNameChange = (value: string) => {
        setDirty({ ...isDirty, name: true });
        validateName(value);
        setName(value);
    };

    return (
        <form onSubmit={saveHandler} style={{ width: '100%' }}>
            <Flex direction={'column'} width={'100%'}>
                <Flex alignItems={'center'} justifyContent={'space-between'}>
                    <Flex gap={'size-100'} width={'100%'} alignItems={'center'}>
                        <Flex width={'100%'}>
                            <TooltipTrigger placement={'top'}>
                                <LimitedTextField
                                    ref={inputRef}
                                    value={name}
                                    width={'100%'}
                                    onChange={handleNameChange}
                                    placeholder={'Label group name'}
                                    aria-label={'Label group name'}
                                    id={'project-label-group-input-id'}
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
                                isSelected={multipleSelectionOn}
                                width={'size-1200'}
                            >
                                {multipleSelectionOn ? 'On' : 'Off'}
                            </Switch>
                            <Tooltip>{MULTIPLE_SELECTION_SWITCH_TOOLTIP}</Tooltip>
                        </TooltipTrigger>
                    </Flex>

                    <Flex>
                        <Button
                            variant={'secondary'}
                            type={'submit'}
                            isDisabled={!isEmpty(error)}
                            data-testid={'add-label-button'}
                            id={'add-label-button'}
                            UNSAFE_style={{ whiteSpace: 'nowrap' }}
                        >
                            Create group
                        </Button>
                    </Flex>
                </Flex>
                <ValidationErrorMsg errorMsg={isDirty.name ? error : ''} />
            </Flex>
        </form>
    );
};
