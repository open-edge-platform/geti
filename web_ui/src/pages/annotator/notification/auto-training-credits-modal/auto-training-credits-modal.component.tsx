// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useRef, useState } from 'react';

import { Button, Content, DialogContainer, Divider, Flex, Header, Heading, Text, View } from '@geti/ui';
import { InfiniteData } from '@tanstack/react-query';
import { isNil } from 'lodash-es';
import { useParams } from 'react-router-dom';

import { Info } from '../../../../assets/icons';
import { useFeatureFlags } from '../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useGetScheduledJobs } from '../../../../core/jobs/hooks/use-jobs.hook';
import { JobsResponse } from '../../../../core/jobs/services/jobs-service.interface';
import { ProjectIdentifier } from '../../../../core/projects/core.interface';
import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../../core/user-settings/hooks/use-global-settings.hook';
import { UserGlobalSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { getSettingsOfType } from '../../../../core/user-settings/utils';
import { CreditsToConsume } from '../../../../shared/components/header/credit-balance/credits-to-consume.component';
import { getFuxSetting } from '../../../../shared/components/tutorials/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useIsAutoTrainingOn } from '../../hooks/use-is-auto-training-on.hook';
import { onFirstScheduledOrRunningAutoTrainingJob } from './util';

import classes from './auto-training-credits-modal.module.scss';

interface AutoTrainingCreditsModalProps {
    settings: UseSettings<UserGlobalSettings>;
}

export const AutoTrainingCreditsModalFactory = () => {
    const params = useParams<{ projectId: string }>();
    const settings = useUserGlobalSettings();
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const fuxNotificationsConfig = getSettingsOfType(settings.config, FUX_NOTIFICATION_KEYS);

    //we check params.projectId to ensure the page is with a project provider
    if (
        isNil(params.projectId) ||
        !FEATURE_FLAG_CREDIT_SYSTEM ||
        !fuxNotificationsConfig[FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]?.isEnabled
    ) {
        return <></>;
    }

    return <AutoTrainingCreditsModal settings={settings} />;
};

const useAutoTrainingCreditsJobs = ({
    enabled,
    projectIdentifier,
    onSuccess,
}: {
    projectIdentifier: ProjectIdentifier;
    enabled: boolean;
    onSuccess: (data: InfiniteData<JobsResponse>) => void;
}) => {
    const handleSuccessRef = useRef(onSuccess);

    const jobsQuery = useGetScheduledJobs({ projectId: projectIdentifier.projectId, queryOptions: { enabled } });

    useEffect(() => {
        handleSuccessRef.current = onSuccess;
    }, [onSuccess]);

    useEffect(() => {
        if (!enabled || !jobsQuery.isSuccess) {
            return;
        }

        handleSuccessRef.current(jobsQuery.data);
    }, [enabled, jobsQuery.isSuccess, jobsQuery.data]);
};

export const AutoTrainingCreditsModal = ({ settings }: AutoTrainingCreditsModalProps) => {
    const { project, projectIdentifier } = useProject();
    const [isOpen, setIsOpen] = useState(false);

    const isAutoTrainingOn = useIsAutoTrainingOn({ project, projectIdentifier });
    const hasNeverAutotrained = getFuxSetting(FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED, settings.config);
    const isQueryEnabled = Boolean(isAutoTrainingOn && !settings.isSavingConfig && hasNeverAutotrained);

    const handleDisplayModal = async (jobId: string) => {
        settings.saveConfig({
            ...settings.config,
            [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: { isEnabled: false },
            [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: { value: project.id },
            [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: { value: false },
            [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: { value: jobId },
        });
    };

    useAutoTrainingCreditsJobs({
        enabled: isQueryEnabled,
        projectIdentifier,
        onSuccess: onFirstScheduledOrRunningAutoTrainingJob(settings, (jobId: string) => {
            if (isQueryEnabled && !isOpen) {
                setIsOpen(true);
                handleDisplayModal(jobId);
            }
        }),
    });

    const dismissModal = () => {
        setIsOpen(false);

        settings.saveConfig({
            ...settings.config,
            [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: { isEnabled: false },
            [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: { isEnabled: true },
            [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: { value: project.id },
        });
    };

    return (
        <DialogContainer onDismiss={dismissModal}>
            {isOpen && (
                <View width={'60rem'}>
                    <Header UNSAFE_className={classes.header}>
                        <Heading level={2}>Accelerate the time-to-model</Heading>

                        <Heading level={3}>Annotate with auto-training</Heading>
                    </Header>

                    <Content UNSAFE_className={classes.container}>
                        <Text UNSAFE_className={classes.description}>
                            The first auto-training job is scheduled and ready to start when resources are available.
                            This training job will consume <CreditsToConsume /> credits.
                        </Text>

                        <Divider UNSAFE_className={classes.divider} />
                        <Flex gap={'size-100'}>
                            <Info />
                            <Text>
                                You can disable auto-training from the active learning menu and start the training
                                manually to control the credits consumption.
                            </Text>
                        </Flex>

                        <Flex marginTop={'size-325'} gap={'size-200'} justifyContent={'end'}>
                            <Button
                                isQuiet
                                variant={'primary'}
                                onPress={dismissModal}
                                isDisabled={settings.isSavingConfig}
                            >
                                Dismiss
                            </Button>
                        </Flex>
                    </Content>
                </View>
            )}
        </DialogContainer>
    );
};
