// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, FC, SetStateAction, useEffect } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { WorkspaceIdentifier } from '@geti/core/src/workspaces/services/workspaces.interface';
import { Button, ButtonGroup, Flex, Loading, Text, View } from '@geti/ui';
import { AnimatePresence, motion } from 'framer-motion';

import { ExportStatusStateDTO } from '../../../../../../../core/configurable-parameters/dtos/configurable-parameters.interface';
import { useJobs } from '../../../../../../../core/jobs/hooks/use-jobs.hook';
import { getJobActiveStep } from '../../../../../../../core/jobs/utils';
import { ProjectIdentifier } from '../../../../../../../core/projects/core.interface';
import { useExportProjectStatusQuery } from '../../../../../../../core/projects/hooks/use-export-project-status.hook';
import { useLocalStorageProject } from '../../../../../../../core/projects/hooks/use-local-storage-project.hook';
import { ProjectExport, ProjectExportIdentifier } from '../../../../../../../core/projects/project.interface';
import { JobStateToExportStatus } from '../../../../../../../core/projects/services/api-project-service';
import { NOTIFICATION_TYPE } from '../../../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../../../notification/notification.component';
import { ANIMATION_PARAMETERS } from '../../../../../../../shared/animation-parameters/animation-parameters';
import { JobProgress } from '../../../../../../../shared/components/header/jobs-management/job-progress.component';
import { ThinProgressBar } from '../../../../../../../shared/components/thin-progress-bar/thin-progress-bar.component';
import { downloadFile, formatDownloadUrl, getDownloadNotificationMessage } from '../../../../../../../shared/utils';

import classes from './project.module.scss';

type ExportProjectMutationIdentifier = Partial<ProjectIdentifier> & Partial<ProjectExport>;

const useReopen = (
    setIsExporting: Dispatch<SetStateAction<boolean>>,
    lsIdentifier: ProjectExportIdentifier | null,
    exportProjectMutationIdentifier: ExportProjectMutationIdentifier
): Partial<ProjectExportIdentifier> => {
    const queryVariables = lsIdentifier ?? exportProjectMutationIdentifier;

    useEffect(() => {
        if (lsIdentifier) {
            setIsExporting(true);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return queryVariables;
};

interface ProjectExportStatusProps {
    projectId: string;
    isExporting: boolean;
    setIsExporting: Dispatch<SetStateAction<boolean>>;
    workspaceIdentifier: WorkspaceIdentifier;
    exportProjectMutationIdentifier: ExportProjectMutationIdentifier;
    onSelectItem?: () => void;
    onResetProjectExport: () => void;
}

export const ProjectExportStatus: FC<ProjectExportStatusProps> = ({
    projectId,
    isExporting,
    workspaceIdentifier,
    exportProjectMutationIdentifier,
    onSelectItem,
    setIsExporting,
    onResetProjectExport,
}) => {
    const { router } = useApplicationServices();
    const { setLsExportId, removeLsExportId, getLsExportId } = useLocalStorageProject();
    const { useCancelJob } = useJobs(workspaceIdentifier);
    const { addNotification } = useNotification();

    const onSettled = () => {
        setIsExporting(false);
        removeLsExportId();
        onResetProjectExport();
    };

    const queryVariables = useReopen(setIsExporting, getLsExportId(projectId), exportProjectMutationIdentifier);

    const { data } = useExportProjectStatusQuery({
        isExporting,
        variables: queryVariables,
        onStart: () => {
            setLsExportId(queryVariables as ProjectExportIdentifier);
        },
        onSettled,
    });

    const jobActiveStep = data !== undefined ? getJobActiveStep(data) : undefined;

    const state = data?.state !== undefined ? JobStateToExportStatus[data.state] : undefined;
    const isProjectExportReadyToBeDownloaded = state === ExportStatusStateDTO.DONE;
    const isProjectExportFailed = state === ExportStatusStateDTO.ERROR;
    const isProjectExportInProgress =
        data !== undefined && !isProjectExportReadyToBeDownloaded && !isProjectExportFailed;
    const downloadUrl = data?.metadata.downloadUrl;
    const progress = jobActiveStep?.progress ?? 0;

    const handleCancelExportProject = async () => {
        setIsExporting(false);

        if (!isProjectExportInProgress) {
            onSettled();

            return;
        }

        if (queryVariables.exportProjectId) {
            useCancelJob.mutate(queryVariables.exportProjectId, {
                onSettled,
            });
        }
    };

    const handleDownloadExportedProject = () => {
        downloadFile(
            router.PREFIX(formatDownloadUrl(String(downloadUrl))),
            `intel_geti_${queryVariables.projectId}.zip`
        );

        addNotification({ message: getDownloadNotificationMessage('project'), type: NOTIFICATION_TYPE.INFO });

        onSettled();
    };

    return (
        <AnimatePresence mode={'wait'}>
            {isExporting && (
                <motion.div
                    exit={'exit'}
                    initial={'hidden'}
                    animate={'visible'}
                    variants={ANIMATION_PARAMETERS.FADE_ITEM}
                    onAnimationComplete={onSelectItem}
                >
                    <Flex
                        gap={'size-200'}
                        alignItems={'center'}
                        position={'relative'}
                        UNSAFE_className={classes.exportStatus}
                        justifyContent={'space-between'}
                        id={`${projectId}-exporting-details-id`}
                        data-testid={`${projectId}-exporting-details-id`}
                    >
                        <View UNSAFE_className={classes.progressBar}>
                            <ThinProgressBar
                                size='size-25'
                                customColor='var(--energy-blue-shade)'
                                progress={progress}
                            />
                        </View>
                        {data !== undefined && jobActiveStep !== undefined ? (
                            <JobProgress idPrefix={`${projectId}-export-project-progress`} step={jobActiveStep} />
                        ) : (
                            <Flex alignItems={'center'} gap={'size-100'}>
                                <Loading mode='inline' size={'S'} />
                                <Text width={'size-3000'}>Exporting project</Text>
                            </Flex>
                        )}

                        <ButtonGroup>
                            <Button
                                aria-label={isProjectExportReadyToBeDownloaded ? 'close' : 'cancel export'}
                                onPress={handleCancelExportProject}
                                id={'cancel-project-export-id'}
                                variant={'secondary'}
                            >
                                {isProjectExportReadyToBeDownloaded ? 'Close' : 'Cancel'}
                            </Button>
                            {isProjectExportReadyToBeDownloaded && (
                                <Button
                                    variant={'primary'}
                                    aria-label={'Download exported project'}
                                    id={'download-exported-project-id'}
                                    onPress={handleDownloadExportedProject}
                                >
                                    Download
                                </Button>
                            )}
                        </ButtonGroup>
                    </Flex>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
