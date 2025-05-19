// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useState } from 'react';

import { Loading, Text, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';
import { Selection } from 'react-aria-components';

import { JobState } from '../../../../core/jobs/jobs.const';
import { Job } from '../../../../core/jobs/jobs.interface';
import { SortByAttribute, SortDirection } from '../../sort-by-attribute/sort-by-attribute.component';
import { JobsListItem } from './jobs-list-item.component';
import { DISCARD_TYPE, JOB_STATE_TO_DISCARD_TYPE } from './utils';
import { VirtualizedJobList } from './virtualized-jobs-list.component';

export interface JobsListProps {
    jobState: JobState;
    jobs: Job[];
    hasNextPage: boolean;
    fetchNextPage: () => void;
    isFetchingNextPage: boolean;
    isLoading: boolean;
    jobClickHandler?: () => void;
    sortDirection: SortDirection;
    setSortDirection: Dispatch<SetStateAction<SortDirection>>;
    gap?: number;
}

const SORT_ICON_ID = 'job-scheduler-action-sort-by-start-time';

export const JobsList = ({
    jobState,
    jobClickHandler,
    jobs,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
    isLoading,
    sortDirection,
    setSortDirection,
    gap = 10,
}: JobsListProps): JSX.Element => {
    const discardType: DISCARD_TYPE | undefined = JOB_STATE_TO_DISCARD_TYPE[jobState];
    const [selected, setSelected] = useState<Selection>(new Set([]));

    const handleFetchNextPage = () => {
        hasNextPage && fetchNextPage();
    };

    if (isLoading || isEmpty(jobs)) {
        return (
            <View paddingTop={'size-50'} overflow={'hidden'} width={'100%'}>
                {isLoading && <Loading />}
                {!isLoading && isEmpty(jobs) && <Text>{`There are no ${jobState} jobs`}</Text>}
            </View>
        );
    }

    return (
        <View paddingTop={'size-50'} width={'100%'}>
            <View marginBottom={'size-100'}>
                <SortByAttribute
                    sortIconId={SORT_ICON_ID}
                    sortDirection={sortDirection}
                    attributeName={'Creation time'}
                    setSortDirection={setSortDirection}
                />
            </View>

            <VirtualizedJobList
                gap={gap}
                items={jobs}
                selected={selected}
                isLoading={isFetchingNextPage}
                onLoadMore={handleFetchNextPage}
            >
                {(job) => (
                    <JobsListItem
                        job={job}
                        discardType={discardType}
                        jobClickHandler={jobClickHandler}
                        onItemChange={() => setSelected(new Set([job.id]))}
                    />
                )}
            </VirtualizedJobList>
        </View>
    );
};
