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

import { useEffect, useState } from 'react';

import { Grid } from '@adobe/react-spectrum';

import { Delete } from '../../../assets/icons';
import {
    SearchOptionsRule,
    SearchRuleField,
    SearchRuleOperator,
    SearchRuleValue,
} from '../../../core/media/media-filter.interface';
import { isAnomalyDomain } from '../../../core/projects/domains';
import { usePrevious } from '../../../hooks/use-previous/use-previous.hook';
import { ActionButton } from '../../../shared/components/button/button.component';
import { useProject } from '../../project-details/providers/project-provider/project-provider.component';
import { FIELD_OPTIONS, isEmptyRule } from '../utils';
import { MediaFilterValueFactory } from './field-values/media-filter-value-factory';
import { MediaFilterField } from './media-filter-field.component';
import { MediaFilterOperator } from './media-filter-operator.component';

interface MediaFilterRowProps {
    rule: SearchOptionsRule;
    isDatasetAccordion?: boolean;
    disabledFilterRules?: SearchRuleField[];
    onReset: (id: string) => void;
    onRemove: (id: string) => void;
    onUpdate: (id: string, rule: SearchOptionsRule) => void;
}

const isMultiSelection = (value: SearchRuleOperator) =>
    [SearchRuleOperator.In, SearchRuleOperator.NotIn].includes(value);

const hasMultiSelection = (optionOne: SearchRuleOperator, optionTwo?: '' | SearchRuleOperator) => {
    if (!optionTwo) {
        return false;
    }

    const isSingle = (value: SearchRuleOperator) =>
        [
            SearchRuleOperator.Less,
            SearchRuleOperator.Equal,
            SearchRuleOperator.Greater,
            SearchRuleOperator.NotEqual,
            SearchRuleOperator.LessOrEqual,
            SearchRuleOperator.GreaterOrEqual,
        ].includes(value);

    return (isMultiSelection(optionOne) && isSingle(optionTwo)) || (isMultiSelection(optionTwo) && isSingle(optionOne));
};

export const MediaFilterRow = ({
    rule,
    onUpdate,
    onReset,
    onRemove,
    disabledFilterRules = [],
    isDatasetAccordion = false,
}: MediaFilterRowProps): JSX.Element => {
    const { isSingleDomainProject } = useProject();
    const isAnomalyProject = isSingleDomainProject(isAnomalyDomain);
    const [field, setField] = useState<SearchRuleField | ''>(rule.field);
    const [operator, setOperator] = useState<SearchRuleOperator | ''>(rule.operator);
    const [ruleValue, setRuleValue] = useState<SearchRuleValue>(rule.value);
    const prevOperator = usePrevious(operator);

    const fieldsOptions = FIELD_OPTIONS.map((option) =>
        option.filter((subOption) => {
            return !disabledFilterRules.some((disabledItem) => subOption.key === disabledItem);
        })
    );

    useEffect(() => {
        const newRule = { id: rule.id, field, operator, value: ruleValue };

        if (!isEmptyRule(newRule)) {
            onUpdate(rule.id, newRule);
        }

        if (operator && hasMultiSelection(operator, prevOperator)) {
            onReset(rule.id);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [field, operator, prevOperator, ruleValue]);

    return (
        <Grid columns={['28%', '28%', '28%', '1fr']} columnGap={'size-200'}>
            <MediaFilterField
                value={field}
                fieldsOptions={
                    // TODO: Leverage "disabledFilterRules" to declaratively exclude certain filters
                    // instead of relying on specific props
                    isAnomalyProject && !isDatasetAccordion
                        ? fieldsOptions.filter((fieldOption) =>
                              fieldOption.some(({ key }) => key !== SearchRuleField.LabelId)
                          )
                        : fieldsOptions
                }
                onSelectionChange={(updatedField) => {
                    setOperator('');
                    setRuleValue('');
                    setField(updatedField);
                }}
            />
            <MediaFilterOperator
                value={operator}
                field={field}
                onSelectionChange={(option) => {
                    setOperator(option);

                    if (operator !== '' && isMultiSelection(operator) !== isMultiSelection(option)) {
                        setRuleValue('');
                    }
                }}
                isAnomalyProject={isAnomalyProject}
                isDatasetAccordion={isDatasetAccordion}
            />
            <MediaFilterValueFactory
                field={field}
                value={ruleValue}
                onSelectionChange={(value) => {
                    setRuleValue(value);
                }}
                isAnomalyProject={isAnomalyProject}
                isDatasetAccordion={isDatasetAccordion}
                isDisabled={operator === ''}
                isMultiselection={isMultiSelection(operator as SearchRuleOperator)}
            />
            <ActionButton
                isQuiet
                onPress={() => onRemove(rule.id)}
                id='media-filter-delete-row'
                data-testid={'media-filter-delete-row'}
                marginStart={'size-50'}
            >
                <Delete width={20} />
            </ActionButton>
        </Grid>
    );
};
