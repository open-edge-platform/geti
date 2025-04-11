// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
