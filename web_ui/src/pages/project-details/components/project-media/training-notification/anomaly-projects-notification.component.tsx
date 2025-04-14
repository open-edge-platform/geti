// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useOverlayTriggerState } from '@react-stately/overlays';
import { useNavigate } from 'react-router-dom';

import { paths } from '../../../../../core/services/routes';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { QuietToggleButton } from '../../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { TrainModelDialog } from '../../project-models/train-model-dialog/train-model-dialog.component';
import { useShowStartTraining } from './use-show-start-training.hook';

export const AnomalyProjectsNotification = () => {
    const navigate = useNavigate();
    const projectIdentifier = useProjectIdentifier();
    const trainModelDialogState = useOverlayTriggerState({});
    const { removeNotifications, addNotification } = useNotification();

    useShowStartTraining(trainModelDialogState);

    return (
        <TrainModelDialog
            isOpen={trainModelDialogState.isOpen}
            onClose={() => {
                removeNotifications();
                trainModelDialogState.close();
            }}
            onSuccess={() => {
                trainModelDialogState.close();
                addNotification({
                    message: 'Training has started',
                    type: NOTIFICATION_TYPE.DEFAULT,
                    dismiss: { duration: 0 }, //0 will act as infinite duration
                    actionButtons: [
                        <QuietToggleButton
                            key={'open-train-model'}
                            onPress={() => navigate(paths.project.models.index(projectIdentifier))}
                        >
                            Progress
                        </QuietToggleButton>,
                    ],
                });
            }}
        />
    );
};
