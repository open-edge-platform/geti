// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { BorderClose } from '../../../../assets/icons';
import { ActionButton } from '../../../../shared/components/button/button.component';
import { Tag } from '../../../../shared/components/tag/tag.component';
import { hasEqualId } from '../../../../shared/utils';
import { useAnnotationFilters } from './use-annotation-filters.hook';
import { useTaskLabels } from './use-task-labels.hook';

import classes from './annotation-filter-trigger.module.scss';

export const AnnotationsFilterChips = (): JSX.Element => {
    const [filters, setFilters] = useAnnotationFilters();
    const labels = useTaskLabels();

    const handleRemoveLabel = (labelId: string) => {
        setFilters(filters.filter((id) => id !== labelId));
    };

    if (isEmpty(filters)) {
        return <></>;
    }
    return (
        <Flex gap={'size-100'} wrap marginBottom={'size-100'}>
            {filters.map((labelId) => {
                const label = labels.find(hasEqualId(labelId));

                if (label === undefined) {
                    return;
                }

                return (
                    <Tag
                        key={labelId}
                        aria-label={`Filter ${label.name}`}
                        text={label.name}
                        withDot={false}
                        className={classes.chips}
                        suffix={
                            <ActionButton
                                isQuiet
                                aria-label={`Remove label filter for ${label.name}`}
                                id={`remove-label-filter-${label.id}`}
                                onPress={() => handleRemoveLabel(labelId)}
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
