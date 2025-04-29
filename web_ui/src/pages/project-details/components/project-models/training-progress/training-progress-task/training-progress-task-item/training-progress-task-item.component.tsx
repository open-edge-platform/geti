// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Heading, Text } from '@adobe/react-spectrum';

import { idMatchingFormat } from '../../../../../../../test-utils/id-utils';

import classes from './training-progress-task-item.module.scss';

interface TrainingProgressTaskItemsProps {
    name: string;
    value: string;
}

export const TrainingProgressTaskItem = ({ name, value }: TrainingProgressTaskItemsProps): JSX.Element => {
    const headingId = `${idMatchingFormat(name)}-value-id`;

    return (
        <>
            <Text key={idMatchingFormat(name)} id={`${idMatchingFormat(name)}-id`}>
                {name}:
            </Text>
            <Heading key={headingId} data-testid={headingId} UNSAFE_className={classes.trainingItemValue}>
                {value}
            </Heading>
        </>
    );
};
