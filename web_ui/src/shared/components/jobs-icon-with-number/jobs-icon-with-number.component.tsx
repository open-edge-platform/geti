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
