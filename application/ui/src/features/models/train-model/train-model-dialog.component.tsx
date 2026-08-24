// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, ButtonGroup, Content, Dialog, Divider, Flex, Footer, Heading, InlineAlert, Text } from '@geti-ui/ui';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { useTranslation } from 'react-i18next';
import { Link, useMatch } from 'react-router-dom';

import { toast } from '../../../components/toast/toast.component';
import { paths } from '../../../constants/paths';
import { AdvancedSettings } from './advanced-settings/advanced-settings.component';
import { BasicTrainModelContent } from './basic-train-model-content.component';
import { useTrainModel } from './hooks/use-train-model';
import { useTrainModelDisabledReason } from './hooks/use-train-model-disabled-reason';
import { TrainModelDialogLayout } from './train-model-dialog-layout.component';
import { useTrainModelState } from './train-model-provider.component';

type TrainModelDialogProps = {
    onClose: () => void;
};

export const TrainModelDialog = ({ onClose }: TrainModelDialogProps) => {
    const { t } = useTranslation();
    const {
        selectedTrainingDevice,
        selectedModelArchitectureId,
        isAdvancedSettingsMode,
        onToggleAdvancedSettingsMode,
        trainingConfiguration,
    } = useTrainModelState();
    const projectId = useProjectIdentifier();
    const isModelsPage = useMatch(paths.project.models.pattern);
    const trainingDisabledReason = useTrainModelDisabledReason().reason;
    const isTrainingDisabled = trainingDisabledReason !== undefined;

    const { trainModel, isPending } = useTrainModel();

    const isStartButtonDisabled =
        isTrainingDisabled || selectedModelArchitectureId === null || selectedTrainingDevice === null || isPending;

    const isAdvancedSettingsModeDisabled = selectedModelArchitectureId === null || trainingConfiguration === undefined;

    const handleTrainModel = () => {
        trainModel({
            onSuccess: () => {
                onClose();

                toast({
                    message: isModelsPage ? (
                        <Text>{t('models.trainingStartedToast')}</Text>
                    ) : (
                        <Flex alignItems={'center'} gap={'size-50'} wrap={'wrap'}>
                            <Text>
                                Model training started successfully.{' '}
                                <Link to={paths.project.models({ projectId })} viewTransition>
                                    Open models screen to see progress.
                                </Link>
                            </Text>
                        </Flex>
                    ),
                    type: 'success',
                });
            },
        });
    };

    return (
        <Dialog width={'clamp(800px, 50vw, 1150px)'} height={isAdvancedSettingsMode ? '80vh' : undefined}>
            <Heading>{t('models.selectModelToTrain')}</Heading>

            <Divider size={'S'} />

            <Content>
                <TrainModelDialogLayout>
                    {isAdvancedSettingsMode ? <AdvancedSettings /> : <BasicTrainModelContent />}
                </TrainModelDialogLayout>
            </Content>

            <Divider size={'S'} />

            <Footer>
                <Flex alignItems={'center'} marginBottom={'size-200'}>
                    {isTrainingDisabled ? (
                        <InlineAlert variant={'notice'}>
                            <Heading>{t('models.whyCannotTrainHeading')}</Heading>
                            <Content>{trainingDisabledReason}</Content>
                        </InlineAlert>
                    ) : null}
                </Flex>

                <ButtonGroup marginStart={'auto'}>
                    <Button variant={'secondary'} onPress={onClose}>
                        {t('common.cancel')}
                    </Button>
                    {isAdvancedSettingsMode ? (
                        <Button
                            variant={'primary'}
                            onPress={() => onToggleAdvancedSettingsMode(!isAdvancedSettingsMode)}
                        >
                            {t('models.backButton')}
                        </Button>
                    ) : (
                        <Button
                            variant={'primary'}
                            isDisabled={isAdvancedSettingsModeDisabled}
                            onPress={() => onToggleAdvancedSettingsMode(!isAdvancedSettingsMode)}
                        >
                            {t('models.advancedSettingsButton')}
                        </Button>
                    )}

                    <Button
                        variant={'accent'}
                        onPress={handleTrainModel}
                        isDisabled={isStartButtonDisabled}
                        isPending={isPending}
                    >
                        {t('models.startButton')}
                    </Button>
                </ButtonGroup>
            </Footer>
        </Dialog>
    );
};
