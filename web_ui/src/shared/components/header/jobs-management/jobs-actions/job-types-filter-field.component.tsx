// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { JobType } from '../../../../../core/jobs/jobs.const';
import { JobsFilterField } from '../jobs-filter-field.component';

interface Props {
    selectedJobTypes: JobType[];
    setSelectedJobTypes: (jobs: JobType[]) => void;
}

const OPTIONS = [
    { key: 'all', name: 'All job types', jobTypes: [] },
    { key: 'train', name: 'Train', jobTypes: [JobType.TRAIN] },
    { key: 'test', name: 'Test', jobTypes: [JobType.TEST] },
    { key: 'optimize', name: 'Optimize', jobTypes: [JobType.OPTIMIZATION_POT] },
    {
        key: 'import_jobs',
        name: 'Import jobs',
        jobTypes: [
            JobType.PERFORM_IMPORT_DATASET_INTO_EXISTING_PROJECT,
            JobType.PREPARE_IMPORT_DATASET_INTO_EXISTING_PROJECT,
            JobType.PERFORM_IMPORT_DATASET_INTO_NEW_PROJECT,
            JobType.PREPARE_IMPORT_DATASET_INTO_NEW_PROJECT,
            JobType.IMPORT_PROJECT,
        ],
    },
    {
        key: 'export_jobs',
        name: 'Export jobs',
        jobTypes: [JobType.EXPORT_DATASET, JobType.EXPORT_PROJECT],
    },
];

export const JobsTypeFilterField = ({ selectedJobTypes, setSelectedJobTypes }: Props) => {
    const selectedOption =
        OPTIONS.find((option) => {
            return selectedJobTypes.every((jobType) => option.jobTypes.includes(jobType));
        }) ?? OPTIONS[0];

    const handleSelectJobType = (key: Key | null): void => {
        const newSelectedOption = OPTIONS.find((option) => option.key === key) ?? OPTIONS[0];

        setSelectedJobTypes(newSelectedOption.jobTypes);
    };

    return (
        <JobsFilterField
            id={'job-scheduler-filter-job-type'}
            ariaLabel={'Job scheduler filter job type'}
            dataTestId={'job-scheduler-filter-job-type'}
            options={OPTIONS}
            value={selectedOption.key}
            onSelectionChange={handleSelectJobType}
        />
    );
};
