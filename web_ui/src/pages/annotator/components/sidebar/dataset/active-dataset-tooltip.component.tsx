// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Divider, Text, Tooltip, TooltipTrigger } from '@geti/ui';

import { InfoOutline } from '../../../../../assets/icons';

import classes from './dataset-accordion.module.scss';

interface ActiveDatasetTooltipProps {
    count: number;
}

export const ActiveDatasetTooltipComponent = ({ count }: ActiveDatasetTooltipProps): JSX.Element => (
    <TooltipTrigger placement={'bottom'}>
        <ActionButton isQuiet aria-label='Dataset help' UNSAFE_className={classes.datasetTooltipButton}>
            <InfoOutline width={16} height={16} />
        </ActionButton>
        <Tooltip UNSAFE_className={classes.datasetToolsTooltip}>
            <Text>{count} images in the Active set</Text>
            <Divider size='S' marginY={5} />
            <Text>
                Active set is set by default and displays media items in an order that is best for creating a
                well-balanced and fully functional model.
            </Text>
        </Tooltip>
    </TooltipTrigger>
);
