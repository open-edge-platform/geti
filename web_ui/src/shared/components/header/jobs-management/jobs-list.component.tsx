// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import { Text, View } from '@adobe/react-spectrum';
import { Loading } from '@geti/ui';
import { dimensionValue } from '@react-spectrum/utils';
import { isEmpty } from 'lodash-es';
import { Virtuoso } from 'react-virtuoso';

import { JobState } from '../../../../core/jobs/jobs.const';
import { Job } from '../../../../core/jobs/jobs.interface';
import { SortByAttribute, SortDirection } from '../../sort-by-attribute/sort-by-attribute.component';
import { JobsListItem } from './jobs-list-item.component';
import { DISCARD_TYPE, JOB_STATE_TO_DISCARD_TYPE } from './utils';

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

    const handleFetchNextPage = async () => {
        if (hasNextPage && !isFetchingNextPage) {
            await fetchNextPage();
        }
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
        <View paddingTop={'size-50'} overflow={'hidden'} width={'100%'}>
            <View marginBottom={'size-100'}>
                <SortByAttribute
                    sortIconId={SORT_ICON_ID}
                    sortDirection={sortDirection}
                    attributeName={'Creation time'}
                    setSortDirection={setSortDirection}
                />
            </View>
            <Virtuoso
                style={{ height: `calc(100% - ${dimensionValue('size-400')})` }}
                data={jobs}
                endReached={handleFetchNextPage}
                itemContent={(index, job) => {
                    return (
                        <JobsListItem
                            key={job.id}
                            job={job}
                            discardType={discardType}
                            jobClickHandler={jobClickHandler}
                            style={{ marginBottom: index === jobs.length - 1 ? 0 : gap }}
                        />
                    );
                }}
            />
        </View>
    );
};
