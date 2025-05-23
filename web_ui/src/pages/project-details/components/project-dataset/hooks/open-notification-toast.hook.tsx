// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { paths } from '@geti/core/src/services/routes';
import { ActionButton } from '@geti/ui';
import { isEmpty, noop } from 'lodash-es';
import { useNavigate } from 'react-router-dom';

import { useModels } from '../../../../../core/models/hooks/use-models.hook';
import { ModelGroupsAlgorithmDetails } from '../../../../../core/models/models.interface';
import { hasActiveModels } from '../../../../../core/models/utils';
import { LifecycleStage } from '../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { useTasksWithSupportedAlgorithms } from '../../../../../core/supported-algorithms/hooks/use-tasks-with-supported-algorithms';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { addAlgorithmDetails } from '../../project-models/utils';

import classes from './open-notification-toast.module.scss';

const GoToModelsPageButton = ({ onClick, remove = noop }: { onClick: () => void; remove?: () => void }) => (
    <ActionButton
        UNSAFE_className={classes.primaryButton}
        onPress={() => {
            remove();
            onClick();
        }}
    >
        Go to models page
    </ActionButton>
);

const DismissButton = ({ remove = noop }: { remove?: () => void }) => (
    <ActionButton isQuiet UNSAFE_className={classes.primaryButton} onPress={remove}>
        Dismiss
    </ActionButton>
);

const isDeprecated = ({ lifecycleStage }: ModelGroupsAlgorithmDetails) => lifecycleStage === LifecycleStage.DEPRECATED;
const isObsolete = ({ lifecycleStage }: ModelGroupsAlgorithmDetails) => lifecycleStage === LifecycleStage.OBSOLETE;

// eslint-disable-next-line max-len
const deprecatedText = `You can still train this model, but support for this model training inside the Intel® Geti™ platform will stop soon.
Train model using new architectures.`;
// eslint-disable-next-line max-len
const obsoleteText = `Previously trained models are still shown in the Intel® Geti™ platform and they can be used for inference, testing and deployment.
However, it is no longer possible to train new models with this architecture: try one of the new algorithms instead.`;

export const useOpenNotificationToast = () => {
    const { addToastNotification } = useNotification();
    const { useProjectModelsQuery } = useModels();
    const { data = [] } = useProjectModelsQuery();
    const { tasksWithSupportedAlgorithms } = useTasksWithSupportedAlgorithms();
    const models = data.map(addAlgorithmDetails(tasksWithSupportedAlgorithms));
    const navigate = useNavigate();
    const projectIdentifier = useProjectIdentifier();

    useEffect(() => {
        if (isEmpty(models)) {
            return;
        }

        const actionButtons = [
            <GoToModelsPageButton
                key={'primary-button'}
                onClick={() => {
                    navigate(paths.project.models.index(projectIdentifier));
                }}
            />,
            <DismissButton key={'secondary-button'} />,
        ];

        const activeModels: ModelGroupsAlgorithmDetails[] = models.filter(hasActiveModels);
        const activeObsoleteModel: ModelGroupsAlgorithmDetails | undefined = activeModels.find(isObsolete);
        const activeDeprecatedModel: ModelGroupsAlgorithmDetails | undefined = activeModels.find(isDeprecated);

        if (activeDeprecatedModel) {
            addToastNotification({
                title: `Your active model “${activeDeprecatedModel.groupName}" is deprecated`,
                message: deprecatedText,
                type: NOTIFICATION_TYPE.WARNING,
                actionButtons,
            });
        }

        if (activeObsoleteModel) {
            addToastNotification({
                title: `Your active model “${activeObsoleteModel.groupName}" is Obsolete`,
                message: obsoleteText,
                type: NOTIFICATION_TYPE.ERROR,
                actionButtons,
            });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [models]);
};
