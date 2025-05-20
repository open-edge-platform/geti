// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { ActionButton, Flex, Tag } from '@geti/ui';
import { BorderClose } from '@geti/ui/icons';
import { getLocalTimeZone, parseAbsolute } from '@internationalized/date';
import { isEmpty } from 'lodash-es';

import { Label } from '../../../core/labels/label.interface';
import {
    AdvancedFilterOptions,
    SearchRuleField,
    SearchRuleOperator,
    SearchRuleValue,
} from '../../../core/media/media-filter.interface';
import { useUsers } from '../../../core/users/hook/use-users.hook';
import { RESOURCE_TYPE } from '../../../core/users/users.interface';
import { useOrganizationIdentifier } from '../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { hasEqualId } from '../../../shared/utils';
import { useProject } from '../../project-details/providers/project-provider/project-provider.component';
import {
    concatByProperty,
    deleteLastComa,
    findLabelsById,
    getAnnotationSceneStatesFromText,
    getShapesFromText,
    getTypesFromText,
    isAnnotationScene,
    isDate,
    isLabelID,
    isMediaType,
    isShapeAreaPercentage,
    isShapeType,
    removeRuleById,
} from '../utils';

import classes from '../media-filter.module.scss';

const getFormattedValue = (field: SearchRuleField, ruleValue: SearchRuleValue, labels: Label[]): string => {
    if (isDate(field)) {
        return parseAbsolute(String(ruleValue), getLocalTimeZone()).toDate().toLocaleString('en', {
            timeStyle: 'short',
            dateStyle: 'medium',
        });
    }

    if (isLabelID(field)) {
        return deleteLastComa(concatByProperty(findLabelsById(ruleValue as string[], labels), 'name'));
    }

    if (isAnnotationScene(field)) {
        return deleteLastComa(concatByProperty(getAnnotationSceneStatesFromText(ruleValue), 'text'));
    }

    if (isShapeAreaPercentage(field)) {
        return `${Number(ruleValue) * 100}%`;
    }

    if (isShapeType(field)) {
        return deleteLastComa(concatByProperty(getShapesFromText(ruleValue), 'text'));
    }

    if (isMediaType(field)) {
        return deleteLastComa(concatByProperty(getTypesFromText(ruleValue), 'text'));
    }

    return String(ruleValue);
};

const formatOperatorString = (ruleOperator: SearchRuleOperator): string => {
    return ruleOperator.split('_').join(' ').toLocaleLowerCase();
};

export const getRuleDescription = (ruleField: SearchRuleField, ruleOperator: SearchRuleOperator): string => {
    switch (ruleField) {
        case SearchRuleField.LabelId:
            if (ruleOperator === SearchRuleOperator.In) {
                return 'With label(s)';
            } else {
                return 'Without label(s)';
            }
        case SearchRuleField.AnnotationSceneState:
            return 'Annotation status Is';
        case SearchRuleField.AnnotationCreationDate:
            if (ruleOperator === SearchRuleOperator.Less) {
                return 'Annotated before';
            } else {
                return 'Annotated after';
            }
        case SearchRuleField.UserName:
            if (ruleOperator === SearchRuleOperator.NotEqual) {
                return 'Not annotated by';
            }

            return 'Annotated by';
        case SearchRuleField.MediaHeight:
            if (ruleOperator === SearchRuleOperator.NotEqual || ruleOperator === SearchRuleOperator.Equal) {
                return `Media height is ${formatOperatorString(ruleOperator)} to`;
            } else {
                return `Media height is ${formatOperatorString(ruleOperator)} than`;
            }
        case SearchRuleField.MediaWidth:
            if (ruleOperator === SearchRuleOperator.NotEqual || ruleOperator === SearchRuleOperator.Equal) {
                return `Media width is ${formatOperatorString(ruleOperator)} to`;
            } else {
                return `Media width is ${formatOperatorString(ruleOperator)} than`;
            }
        case SearchRuleField.MediaUploadDate:
            if (ruleOperator === SearchRuleOperator.Less) {
                return 'Uploaded before';
            } else {
                return 'Uploaded after';
            }
        case SearchRuleField.MediaName:
            if (ruleOperator === SearchRuleOperator.Contains) {
                return 'Media name contains';
            } else {
                return `Media name is ${formatOperatorString(ruleOperator)} to`;
            }
        case SearchRuleField.MediaType:
            return 'Media is ';
        case SearchRuleField.ShapeType:
            if (ruleOperator === SearchRuleOperator.In) {
                return 'Has shape(s)';
            } else if (ruleOperator === SearchRuleOperator.NotIn) {
                return "Doesn't have shape(s)";
            } else {
                return `Shape is ${formatOperatorString(ruleOperator)} to`;
            }
        case SearchRuleField.ShapeAreaPercentage:
            return `Area % ${formatOperatorString(ruleOperator)} than`;
        case SearchRuleField.ShapeAreaPixel:
            return `Area pixel ${formatOperatorString(ruleOperator)} than`;

        default:
            return '';
    }
};

interface MediaFilterChipsProps {
    labels: Label[];
    isAnomalyProject: boolean;
    readonly mediaFilterOptions: AdvancedFilterOptions;
    setMediaFilterOptions: (options: AdvancedFilterOptions) => void;
    darkMode?: boolean;
    id?: string;
}

const useGetFormattedValue = () => {
    const { organizationId } = useOrganizationIdentifier();
    const { useGetUsersQuery } = useUsers();
    const { project } = useProject();
    const { users } = useGetUsersQuery(organizationId, {
        resourceType: RESOURCE_TYPE.PROJECT,
        resourceId: project.id,
    });

    return (field: SearchRuleField, ruleValue: SearchRuleValue, labels: Label[]): string => {
        if (field == SearchRuleField.UserName) {
            const userId = String(ruleValue);

            const user = users.find(hasEqualId(userId));

            if (user === undefined) {
                return '';
            }
            const fullName = `${user.firstName} ${user.lastName}`;

            return fullName;
        }

        return getFormattedValue(field, ruleValue, labels);
    };
};

export const MediaFilterChips = ({
    labels,
    isAnomalyProject,
    mediaFilterOptions,
    setMediaFilterOptions,
    darkMode,
    id,
}: MediaFilterChipsProps): JSX.Element => {
    const filterRulesWithoutDefaultAnomalyOptions = useMemo(() => {
        return isAnomalyProject
            ? mediaFilterOptions?.rules?.filter(({ field }) => field !== SearchRuleField.LabelId)
            : mediaFilterOptions?.rules;
    }, [mediaFilterOptions, isAnomalyProject]);

    const getFormattedRuleValue = useGetFormattedValue();

    if (isEmpty(filterRulesWithoutDefaultAnomalyOptions)) {
        return <></>;
    }

    return (
        <Flex gap={'size-100'} wrap>
            {mediaFilterOptions?.rules?.map((rule) => {
                const CHIP_RULE_ID = `${!isEmpty(id) ? `${id}-` : ''}chip-${rule.id}`;
                const REMOVE_RULE_ID = `${!isEmpty(id) ? `${id}-` : ''}remove-rule-${rule.id}`;

                const ruleField = rule.field as SearchRuleField;
                const ruleOperator = rule.operator as SearchRuleOperator;

                const ruleDescription = getRuleDescription(ruleField, ruleOperator);
                const formattedValue = getFormattedRuleValue(ruleField, rule.value, labels);

                return (
                    <Tag
                        key={rule.id}
                        aria-label={CHIP_RULE_ID}
                        data-testid={CHIP_RULE_ID}
                        text={`${ruleDescription} ${formattedValue}`}
                        withDot={false}
                        className={classes.chips}
                        darkMode={darkMode}
                        suffix={
                            <ActionButton
                                isQuiet
                                aria-label={REMOVE_RULE_ID}
                                onPress={() => setMediaFilterOptions(removeRuleById(mediaFilterOptions, rule.id))}
                            >
                                <BorderClose />
                            </ActionButton>
                        }
                    />
                );
            })}
        </Flex>
    );
};
