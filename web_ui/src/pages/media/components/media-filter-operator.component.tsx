// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useMemo } from 'react';

import { Item, Menu, MenuTrigger, Text } from '@adobe/react-spectrum';

import { ChevronDownSmall } from '../../../assets/icons';
import { SearchRuleField, SearchRuleOperator } from '../../../core/media/media-filter.interface';
import { ActionButton } from '../../../shared/components/button/button.component';
import { getKeyConfig, OPERATOR_OPTIONS } from '../utils';

import classes from '../media-filter.module.scss';

interface MediaFilterOperatorProps {
    field: SearchRuleField | '';
    value: SearchRuleOperator | '';
    isAnomalyProject: boolean;
    isDatasetAccordion?: boolean;
    onSelectionChange: (key: SearchRuleOperator) => void;
}

const getAnomalyProjectOperator = (field: SearchRuleField | '') => {
    switch (field) {
        case SearchRuleField.LabelId:
            return SearchRuleOperator.In;
        case SearchRuleField.AnnotationSceneState:
            return SearchRuleOperator.Equal;
        default:
            return '';
    }
};

export const MediaFilterOperator = ({
    field,
    value,
    onSelectionChange,
    isAnomalyProject = false,
    isDatasetAccordion = false,
}: MediaFilterOperatorProps): JSX.Element => {
    const filteredItems = useMemo(() => {
        return field === '' ? [] : OPERATOR_OPTIONS.filter(({ fields }) => fields.includes(field));
    }, [field]);

    const isAnomalyAndFieldLabelOrAnnotation = useMemo(
        () =>
            field !== '' &&
            isAnomalyProject &&
            !isDatasetAccordion &&
            [SearchRuleField.LabelId, SearchRuleField.AnnotationSceneState].includes(field),
        [field, isAnomalyProject, isDatasetAccordion]
    );

    const selectedKey = isAnomalyAndFieldLabelOrAnnotation ? getAnomalyProjectOperator(field) : value;
    const keyConfig = getKeyConfig(filteredItems, value);

    useEffect(() => {
        if (isAnomalyAndFieldLabelOrAnnotation) {
            onSelectionChange(selectedKey as SearchRuleOperator);
        }

        if (filteredItems.length === 1) {
            onSelectionChange(filteredItems[0].key);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedKey, filteredItems.length]);

    return (
        <MenuTrigger>
            <ActionButton
                isQuiet
                id='media-filter-operator'
                aria-label='media-filter-operator'
                isDisabled={field === '' || isAnomalyAndFieldLabelOrAnnotation}
                UNSAFE_className={[classes.mediaPicker, keyConfig.isPlaceHolder && classes.placeHolder].join(' ')}
            >
                <Text>{keyConfig.text}</Text>
                <ChevronDownSmall width={22} height={22} />
            </ActionButton>
            <Menu
                items={filteredItems}
                selectionMode='single'
                onAction={(key) => onSelectionChange(key as SearchRuleOperator)}
            >
                {({ key, text }) => (
                    <Item textValue={text} key={key} aria-label={key.toLocaleLowerCase()}>
                        <Text>{text}</Text>
                    </Item>
                )}
            </Menu>
        </MenuTrigger>
    );
};
