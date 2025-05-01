// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';
import { ActionButton } from '@shared/components/button/button.component';
import { Tag } from '@shared/components/tag/tag.component';
import { hasEqualId } from '@shared/utils';
import isEmpty from 'lodash/isEmpty';

import { BorderClose } from '../../../../assets/icons';
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
