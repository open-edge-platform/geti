// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Bell } from '../../../assets/icons';
import { NumberBadge } from '../number-badge/number-badge.component';

import sharedClasses from '../../shared.module.scss';
import headerButtonClasses from '../header/header-actions/header-actions.module.scss';

interface JobsIconsWithNumberProps {
    runningJobs: number | undefined;
    isDarkMode?: boolean;
}

export const JobsIconWithNumber = ({ runningJobs, isDarkMode = false }: JobsIconsWithNumberProps): JSX.Element => {
    return (
        <>
            <Bell
                width={15}
                aria-label={'tasks in progress'}
                className={[
                    isDarkMode ? sharedClasses.actionButtonDark : sharedClasses.actionButtonLight,
                    headerButtonClasses.headerJobsIcon,
                ].join(' ')}
            />
            {!!runningJobs && (
                <div style={{ position: 'absolute', top: 1, right: 0 }}>
                    <NumberBadge
                        isAccented
                        id='running-jobs-icon'
                        aria-label='Running jobs badge icon'
                        data-testid='running-jobs-icon'
                        jobsNumber={runningJobs}
                    />
                </div>
            )}
        </>
    );
};
