// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, Key, SetStateAction, useState } from 'react';

import { Content, Dialog, Flex, Text } from '@adobe/react-spectrum';
import { keepPreviousData } from '@tanstack/react-query';

import { useJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { NORMAL_INTERVAL } from '../../../../core/jobs/hooks/utils';
import { JobState, JobType } from '../../../../core/jobs/jobs.const';
import { JobCount } from '../../../../core/jobs/jobs.interface';
import { useWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { NumberBadge } from '../../number-badge/number-badge.component';
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
const defaultJobsCount: JobCount = {
    numberOfRunningJobs: null,
    numberOfFinishedJobs: null,
    numberOfScheduledJobs: null,
    numberOfCancelledJobs: null,
    numberOfFailedJobs: null,
};

export const JobsDialog = ({ isFullScreen, onClose, setIsFullScreen }: JobsDialogProps): JSX.Element => {
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const { useGetJobs } = useJobs({ organizationId, workspaceId });

    const [projectIdFilter, setProjectIdFilter] = useState<string | undefined>();
    const [userIdFilter, setUserIdFilter] = useState<string | undefined>();
    const [jobTypeFilter, setJobTypeFilter] = useState<JobType[]>([]);
    const [selectedJobState, setSelectedJobState] = useState<Key>(JobState.RUNNING);
    const [sortDirection, setSortDirection] = useState<SortDirection>(SortDirection.DESC);

    const { data, isFetchingNextPage, isLoading, isPending, fetchNextPage, hasNextPage } = useGetJobs(
        {
            jobState: selectedJobState as JobState,
            projectId: projectIdFilter,
            jobTypes: jobTypeFilter,
            author: userIdFilter,
            limit: DEFAULT_LIMIT,
            sortDirection,
        },
        {
            placeholderData: keepPreviousData,
            refetchInterval: NORMAL_INTERVAL,
        }
    );

    const allJobs = getAllJobs(data);

    const {
        numberOfRunningJobs,
        numberOfFinishedJobs,
        numberOfScheduledJobs,
        numberOfCancelledJobs,
        numberOfFailedJobs,
    } = data?.pages?.at(0)?.jobsCount ?? defaultJobsCount;

    const tabs: TabItem[] = [
        {
            id: `${JobState.RUNNING.toLowerCase()}-jobs-id`,
            key: JobState.RUNNING,
            name: (
                <>
                    <Text>Running jobs</Text>
                    <NumberBadge
                        isAccented
                        id='running-jobs'
                        isPending={isPending}
                        aria-label='Running jobs badge'
                        data-testid='running-jobs'
                        jobsNumber={numberOfRunningJobs}
                        isSelected={selectedJobState === JobState.RUNNING}
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
                    jobState={JobState.RUNNING}
                    jobClickHandler={onClose}
                    setSortDirection={setSortDirection}
                    sortDirection={sortDirection}
                />
            ),
        },
        {
            id: `${JobState.FINISHED.toLowerCase()}-jobs-id`,
            key: JobState.FINISHED,
            name: (
                <>
                    <Text>Finished jobs</Text>

                    <NumberBadge
                        id='finished-jobs'
                        isPending={isPending}
                        aria-label='Finished jobs badge'
                        data-testid='finished-jobs'
                        jobsNumber={numberOfFinishedJobs}
                        isSelected={selectedJobState === JobState.FINISHED}
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
                    jobState={JobState.FINISHED}
                    jobClickHandler={onClose}
                    setSortDirection={setSortDirection}
                    sortDirection={sortDirection}
                />
            ),
        },
        {
            id: `${JobState.SCHEDULED.toLowerCase()}-jobs-id`,
            key: JobState.SCHEDULED,
            name: (
                <>
                    <Text>Scheduled jobs</Text>

                    <NumberBadge
                        id='scheduled-jobs'
                        isPending={isPending}
                        aria-label='Scheduled jobs badge'
                        data-testid='scheduled-jobs'
                        jobsNumber={numberOfScheduledJobs}
                        isSelected={selectedJobState === JobState.SCHEDULED}
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
                    jobState={JobState.SCHEDULED}
                    jobClickHandler={onClose}
                    setSortDirection={setSortDirection}
                    sortDirection={sortDirection}
                />
            ),
        },
        {
            id: `${JobState.CANCELLED.toLowerCase()}-jobs-id`,
            key: JobState.CANCELLED,
            name: (
                <>
                    <Text>Cancelled jobs</Text>

                    <NumberBadge
                        id='cancelled-jobs'
                        isPending={isPending}
                        aria-label='Cancelled jobs badge'
                        data-testid='canceled-jobs'
                        jobsNumber={numberOfCancelledJobs}
                        isSelected={selectedJobState === JobState.CANCELLED}
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
                    jobState={JobState.CANCELLED}
                    jobClickHandler={onClose}
                    setSortDirection={setSortDirection}
                    sortDirection={sortDirection}
                />
            ),
        },
        {
            id: `${JobState.FAILED.toLowerCase()}-jobs-id`,
            key: JobState.FAILED,
            name: (
                <>
                    <Text>Failed jobs</Text>

                    <NumberBadge
                        id='failed-jobs'
                        isPending={isPending}
                        aria-label='Failed jobs badge'
                        data-testid='failed-jobs'
                        jobsNumber={numberOfFailedJobs}
                        isSelected={selectedJobState === JobState.FAILED}
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
                    jobState={JobState.FAILED}
                    setSortDirection={setSortDirection}
                    sortDirection={sortDirection}
                />
            ),
        },
    ];

    const onFilteringChange = (projectId: string | undefined, userId: string | undefined, type: JobType[]) => {
        if (projectIdFilter !== projectId) {
            setProjectIdFilter(projectId);
        }

        if (userIdFilter !== userId) {
            setUserIdFilter(userId);
        }

        setJobTypeFilter(type);
    };

    return (
        <Dialog width={'unset'} UNSAFE_style={{ background: 'var(--spectrum-global-color-gray-50)' }}>
            <Content>
                <Flex alignItems='center' marginBottom={'size-150'}>
                    <Flex flex={4} alignItems='center' justifyContent='left' gap='size-300'>
                        <JobsFiltering
                            onChange={onFilteringChange}
                            defaultValues={{ projectIdFilter, userIdFilter, jobTypeFilter }}
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
