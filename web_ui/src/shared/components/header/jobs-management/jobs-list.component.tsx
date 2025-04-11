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

import { Dispatch, SetStateAction } from 'react';

import { Text, View } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import isEmpty from 'lodash/isEmpty';
import { Virtuoso } from 'react-virtuoso';

import { JobState } from '../../../../core/jobs/jobs.const';
import { Job } from '../../../../core/jobs/jobs.interface';
import { Loading } from '../../loading/loading.component';
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
