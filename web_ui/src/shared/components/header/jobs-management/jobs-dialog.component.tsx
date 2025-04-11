// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Dispatch, Key, SetStateAction, useMemo, useState } from 'react';

import { Content, Dialog, Flex, Text } from '@adobe/react-spectrum';
import { DateValue, getLocalTimeZone, today } from '@internationalized/date';
import { RangeValue } from '@react-types/shared';
import { keepPreviousData } from '@tanstack/react-query';

import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { NORMAL_INTERVAL } from '../../../../core/jobs/hooks/utils';
import { JobState, JobType } from '../../../../core/jobs/jobs.const';
import { JobCount } from '../../../../core/jobs/jobs.interface';
import { useWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { CornerIndicator } from '../../corner-indicator/corner-indicator.component';
import { DateRangePickerSmall } from '../../date-range-picker-small/date-range-picker-small.component';
import { NumberBadge } from '../../number-badge/number-badge.component';
import { RefreshButton } from '../../refresh-button/refresh-button.component';
import { SortDirection } from '../../sort-by-attribute/sort-by-attribute.component';
import { Tabs } from '../../tabs/tabs.component';
import { TabItem } from '../../tabs/tabs.interface';
import { Fullscreen } from './jobs-actions/fullscreen.component';
import { JobsFiltering } from './jobs-actions/jobs-filtering.component';
import { JobsList } from './jobs-list.component';
import { getAllJobs } from './utils';

interface JobsDialogProps {
    isFullScreen: boolean;
    onClose: () => void;
    setIsFullScreen: Dispatch<SetStateAction<boolean>>;
}

const DEFAULT_LIMIT = 50;
const DEFAULT_JOBS_COUNT: JobCount = {
    numberOfRunningJobs: null,
    numberOfFinishedJobs: null,
    numberOfScheduledJobs: null,
    numberOfCancelledJobs: null,
    numberOfFailedJobs: null,
};

export const JobsDialog = ({ isFullScreen, onClose, setIsFullScreen }: JobsDialogProps): JSX.Element => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { useGetJobs } = useJobs({ organizationId, workspaceId });

    const TODAY = today(getLocalTimeZone());
    const INITIAL_DATES: RangeValue<DateValue> = useMemo(
        () => ({
            start: TODAY.subtract({ months: 3 }),
            end: TODAY,
        }),
        [TODAY]
    );

    const [filters, setFilters] = useState({
        projectId: undefined as string | undefined,
        userId: undefined as string | undefined,
        jobTypes: [] as JobType[],
    });
    const [range, setRange] = useState<RangeValue<DateValue>>(INITIAL_DATES);

    const [selectedJobState, setSelectedJobState] = useState<Key>(JobState.RUNNING);
    const [sortDirection, setSortDirection] = useState<SortDirection>(SortDirection.DESC);

    // Fetch jobs data
    const { data, isFetchingNextPage, isLoading, isPending, fetchNextPage, hasNextPage } = useGetJobs(
        {
            jobState: selectedJobState as JobState,
            projectId: filters.projectId,
            jobTypes: filters.jobTypes,
            author: filters.userId,
            limit: DEFAULT_LIMIT,
            startTimeFrom: range.start.toString(),
            startTimeTo: range.end.add({ days: 1 }).toString(),
            sortDirection,
        },
        {
            placeholderData: keepPreviousData,
            refetchInterval: NORMAL_INTERVAL,
        }
    );

    const isInitialRange = useMemo(
        () => JSON.stringify(range) === JSON.stringify(INITIAL_DATES),
        [range, INITIAL_DATES]
    );
    const areFiltersChanged = useMemo(
        () => !isInitialRange || !!filters.projectId || !!filters.userId || !!filters.jobTypes.length,
        [isInitialRange, filters]
    );

    const allJobs = getAllJobs(data);
    const {
        numberOfRunningJobs,
        numberOfFinishedJobs,
        numberOfScheduledJobs,
        numberOfCancelledJobs,
        numberOfFailedJobs,
    } = data?.pages?.at(0)?.jobsCount ?? DEFAULT_JOBS_COUNT;

    const createTab = (state: JobState, label: string, jobsNumber: number | null, testId: string): TabItem => ({
        id: `${state.toLowerCase()}-jobs-id`,
        key: state,
        name: (
            <>
                <Text>{label}</Text>
                <NumberBadge
                    id={`${state.toLowerCase()}-jobs`}
                    isPending={isPending}
                    aria-label={`${label} badge`}
                    data-testid={testId}
                    jobsNumber={jobsNumber}
                    isSelected={selectedJobState === state}
                />
            </>
        ),
        children: (
            <JobsList
                jobs={allJobs}
                hasNextPage={hasNextPage}
                fetchNextPage={fetchNextPage}
                isFetchingNextPage={isFetchingNextPage}
                isLoading={isLoading}
                jobState={state}
                jobClickHandler={onClose}
                setSortDirection={setSortDirection}
                sortDirection={sortDirection}
            />
        ),
    });

    const tabs: TabItem[] = [
        createTab(JobState.RUNNING, 'Running jobs', numberOfRunningJobs, 'running-jobs'),
        createTab(JobState.FINISHED, 'Finished jobs', numberOfFinishedJobs, 'finished-jobs'),
        createTab(JobState.SCHEDULED, 'Scheduled jobs', numberOfScheduledJobs, 'scheduled-jobs'),
        createTab(JobState.CANCELLED, 'Cancelled jobs', numberOfCancelledJobs, 'cancelled-jobs'),
        createTab(JobState.FAILED, 'Failed jobs', numberOfFailedJobs, 'failed-jobs'),
    ];

    const resetFilters = () => {
        setFilters({ projectId: undefined, userId: undefined, jobTypes: [] });
        setRange(INITIAL_DATES);
    };

    const handleFilteringChange = (projectId: string | undefined, userId: string | undefined, jobTypes: JobType[]) => {
        setFilters((prev) => ({ ...prev, projectId, userId, jobTypes }));
    };
    const handleRangeChange = (value: SetStateAction<RangeValue<DateValue>> | null) => {
        value === null ? setRange(INITIAL_DATES) : setRange(value);
    };

    return (
        <Dialog width='unset' UNSAFE_style={{ background: 'var(--spectrum-global-color-gray-50)' }}>
            <Content>
                <Flex alignItems='center' marginBottom='size-150'>
                    <Flex flex={4} alignItems='center' justifyContent='left' gap='size-300'>
                        <JobsFiltering
                            onChange={handleFilteringChange}
                            defaultValues={{
                                projectIdFilter: filters.projectId,
                                userIdFilter: filters.userId,
                                jobTypeFilter: filters.jobTypes,
                            }}
                            key={`${filters.projectId}${filters.userId}${filters.jobTypes}`}
                        />

                        <CornerIndicator isActive={!isInitialRange}>
                            <DateRangePickerSmall
                                onChange={handleRangeChange}
                                value={range}
                                maxValue={TODAY}
                                defaultValue={INITIAL_DATES}
                            />
                        </CornerIndicator>
                        <RefreshButton
                            onPress={resetFilters}
                            id='refresh-jobs-filters'
                            ariaLabel='Reset all filters'
                            tooltip='Reset all filters'
                            isLoading={isLoading}
                            isDisabled={!areFiltersChanged}
                        />
                    </Flex>
                    <Flex flex={1} alignItems='center' justifyContent='right'>
                        <Fullscreen enabled={isFullScreen} toggle={setIsFullScreen} />
                    </Flex>
                </Flex>
                <Tabs
                    items={tabs}
                    isQuiet={false}
                    maxWidth='100%'
                    minWidth='90.4rem'
                    minHeight='size-6000'
                    panelOverflowY='hidden'
                    aria-label={'Job management tabs'}
                    height={`calc(100% - size-600)`}
                    tabStyles={{ display: 'flex', height: '100%' }}
                    onSelectionChange={setSelectedJobState}
                />
            </Content>
        </Dialog>
    );
};
