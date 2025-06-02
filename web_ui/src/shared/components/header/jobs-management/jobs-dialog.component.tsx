// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, Key, SetStateAction, useRef, useState } from 'react';

import { ActionButton, Content, CornerIndicator, Dialog, Flex, RangeValue, Text } from '@geti/ui';
import { Delete } from '@geti/ui/icons';
import { DateValue } from '@internationalized/date';
import { keepPreviousData } from '@tanstack/react-query';
import { isEmpty } from 'lodash-es';

import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { NORMAL_INTERVAL } from '../../../../core/jobs/hooks/utils';
import { JobState } from '../../../../core/jobs/jobs.const';
import { JobCount } from '../../../../core/jobs/jobs.interface';
import { SortDirection } from '../../../../core/shared/query-parameters';
import { useWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { InfoTooltip } from '../../info-tooltip/info-tooltip.component';
import { RefreshButton } from '../../refresh-button/refresh-button.component';
import { Tabs } from '../../tabs/tabs.component';
import { TabItem } from '../../tabs/tabs.interface';
import { DateRangePickerSmall } from './date-range-picker-small/date-range-picker-small.component';
import { Fullscreen } from './jobs-actions/fullscreen.component';
import { FiltersType } from './jobs-actions/jobs-dialog.interface';
import { JobsFiltering } from './jobs-actions/jobs-filtering.component';
import { JobsList } from './jobs-list.component';
import { NumberBadge } from './number-badge/number-badge.component';
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

//TODO: Remove after we will have filtering by creationDate available
// - keep previous number of scheduled jobs when filter set
const handleDataCountWhenScheduledShouldNotBeFiltered = (
    previousJobsCount: JobCount,
    responsedJobsCount: JobCount | undefined,
    isDateFilterSet: boolean,
    isNotScheduledFilter: boolean
): JobCount => {
    debugger;
    const jobsCount = isNotScheduledFilter
        ? (responsedJobsCount ?? DEFAULT_JOBS_COUNT)
        : {
              ...previousJobsCount,
              numberOfScheduledJobs: responsedJobsCount?.numberOfScheduledJobs ?? null,
          };

    if (isDateFilterSet && isNotScheduledFilter) {
        return {
            ...jobsCount,
            numberOfScheduledJobs: previousJobsCount.numberOfScheduledJobs,
        };
    }

    return jobsCount;
};

export const JobsDialog = ({ isFullScreen, onClose, setIsFullScreen }: JobsDialogProps): JSX.Element => {
    const RANGE_FILTER_TOOLTIP =
        'This component filters jobs by start date. For example if you select a range' +
        ' between yesterday and today it will show jobs started yesterday or today. ' +
        'Note: The filter is not applied to scheduled jobs.';

    // TODO & Note: This condition will be just for now
    // - there is already task for backend to enable filtering by creation date
    // - scheduled jobs do not have start date so there will be always empty tab
    const jobsCountRef = useRef(DEFAULT_JOBS_COUNT);

    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { useGetJobs } = useJobs({ organizationId, workspaceId });

    const [filters, setFilters] = useState<FiltersType>({
        projectId: undefined,
        userId: undefined,
        jobTypes: [],
    });

    const [range, setRange] = useState<RangeValue<DateValue> | null>();

    const [selectedJobState, setSelectedJobState] = useState<Key>(JobState.RUNNING);
    const [sortDirection, setSortDirection] = useState<SortDirection>(SortDirection.DESC);

    const { data, isFetchingNextPage, isLoading, isPending, fetchNextPage, hasNextPage } = useGetJobs(
        {
            jobState: selectedJobState as JobState,
            projectId: filters.projectId,
            jobTypes: filters.jobTypes,
            author: filters.userId,
            limit: DEFAULT_LIMIT,
            // TODO & Note: This condition will be just for now
            // - there is already task for backend to enable filtering by creation date
            // - scheduled jobs do not have start date so there will be always empty tab
            startTimeFrom: selectedJobState === JobState.SCHEDULED ? undefined : range?.start.toString(),
            //Filtering by date is exclusive - adding 1 day
            startTimeTo: selectedJobState === JobState.SCHEDULED ? undefined : range?.end.add({ days: 1 }).toString(),
            sortDirection,
        },
        {
            placeholderData: keepPreviousData,
            refetchInterval: NORMAL_INTERVAL,
        }
    );

    const isInitialRange = isEmpty(range);

    const areFiltersChanged = !isInitialRange || !!filters.projectId || !!filters.userId || !!filters.jobTypes.length;

    const allJobs = getAllJobs(data);

    jobsCountRef.current = handleDataCountWhenScheduledShouldNotBeFiltered(
        jobsCountRef.current,
        data?.pages?.at(0)?.jobsCount,
        !isEmpty(range),
        selectedJobState !== JobState.SCHEDULED
    );

    const {
        numberOfRunningJobs,
        numberOfFinishedJobs,
        numberOfScheduledJobs,
        numberOfCancelledJobs,
        numberOfFailedJobs,
    } = jobsCountRef.current;

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
        setRange(null);
    };

    const handleRangeChange = (value: SetStateAction<RangeValue<DateValue>> | null) => {
        value === null ? setRange(undefined) : setRange(value as RangeValue<DateValue>);
    };

    return (
        <Dialog width='unset' UNSAFE_style={{ background: 'var(--spectrum-global-color-gray-50)' }}>
            <Content>
                <Flex alignItems='center' marginBottom='size-150'>
                    <Flex flex={4} alignItems='center' justifyContent='left' gap='size-300'>
                        <JobsFiltering onChange={setFilters} values={filters} />

                        <CornerIndicator isActive={!isInitialRange}>
                            <DateRangePickerSmall
                                onChange={handleRangeChange}
                                value={range}
                                hasManualEdition
                                isDisabled={selectedJobState === JobState.SCHEDULED}
                                headerContent={
                                    <Flex justifyContent={'end'} alignItems={'center'}>
                                        <ActionButton onPress={() => setRange(null)}>
                                            <Delete />
                                        </ActionButton>
                                        <InfoTooltip id={`range-filter-tooltip`} tooltipText={RANGE_FILTER_TOOLTIP} />
                                    </Flex>
                                }
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
