// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useUsers } from '@geti/core/src/users/hook/use-users.hook';
import { Flex, PressableElement, Tooltip, TooltipTrigger } from '@geti/ui';
import { AiIcon, ChevronRightSmallLight } from '@geti/ui/icons';
import { isFunction } from 'lodash-es';
import { useNumberFormatter, usePress } from 'react-aria';

import { AnnotationLabel } from '../../../../core/annotations/annotation.interface';
import { isPrediction, showLabelScore } from '../../../../core/labels/utils';
import { useOrganizationIdentifier } from '../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { TruncatedText } from '../../../../shared/components/truncated-text/truncated-text.component';
import { FullnameWithLoading } from '../../../../shared/components/users/fullname.component';
import { idMatchingFormat } from '../../../../test-utils/id-utils';
import { getForegroundColor, hexaToRGBA } from '../../../utils';
import { useTask } from '../../providers/task-provider/task-provider.component';

import classes from './labels.module.scss';

export const DEFAULT_LABEL_WIDTH = 200;

interface LabelProps {
    id: string;
    handleEditLabels: (() => void) | undefined;
    label: AnnotationLabel;
    zIndex: number;
    slots?: number;
    hasChildren: boolean;
    maxWidth: number;
}

export const SourceTooltip = ({ label }: { label: AnnotationLabel }) => {
    const { organizationId } = useOrganizationIdentifier();
    const { userId, modelId } = label.source;
    const { useGetUserQuery } = useUsers();
    const userQuery = useGetUserQuery(organizationId, userId);

    // Annotations coming from imported projects do not have source info; we return empty text to hide the tooltip
    if (!userId && !modelId) {
        return <></>;
    }

    const model = `model id \n${modelId}`;

    if (isPrediction(label)) {
        return <>Annotated by {model}</>;
    }

    return (
        <>
            Annotated by <FullnameWithLoading user={userQuery.data} isLoading={userQuery.isPending} />
        </>
    );
};

export const Label = ({
    id,
    label,
    handleEditLabels,
    hasChildren,
    slots = 1,
    zIndex,
    maxWidth,
}: LabelProps): JSX.Element => {
    const { selectedTask } = useTask();
    const pressHandler = { onPress: handleEditLabels };
    const { pressProps } = usePress({ ...pressHandler });

    const formatter = useNumberFormatter({
        style: 'percent',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    });

    const color = getForegroundColor(
        hexaToRGBA(label.color),
        'var(--spectrum-global-color-gray-50)',
        'var(--spectrum-global-color-gray-900)'
    );
    const maxLabelWidth = Math.round(maxWidth / slots);
    const labelId = `${isPrediction(label) ? 'prediction' : 'annotation'}-${id}`;
    const labelNameId = idMatchingFormat(`${isPrediction(label) ? 'prediction' : 'annotation'}-${label.name}`);

    return (
        <li
            key={label.id}
            id={labelId}
            className={classes.label}
            style={{
                zIndex,
                color,
                backgroundColor: label.color,
                opacity: 'var(--label-opacity)',
                cursor: isFunction(handleEditLabels) ? 'pointer' : 'default',
            }}
            {...pressProps}
        >
            <Flex>
                {isPrediction(label) && <AiIcon width={10} style={{ fill: color }} aria-label={'prediction icon'} />}
            </Flex>

            <TooltipTrigger>
                <PressableElement id={labelNameId} maxWidth={maxLabelWidth} aria-label={labelNameId} {...pressHandler}>
                    <TruncatedText>{label.name}</TruncatedText>
                </PressableElement>
                <Tooltip>
                    <SourceTooltip label={label} />
                </Tooltip>
            </TooltipTrigger>

            {showLabelScore(label, selectedTask?.domain) && <span> {formatter.format(label.score as number)}</span>}
            {hasChildren && <ChevronRightSmallLight />}
        </li>
    );
};
