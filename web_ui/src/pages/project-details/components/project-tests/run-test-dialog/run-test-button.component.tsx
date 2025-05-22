// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Button } from '@geti/ui';

import { isVisualPromptModelGroup } from '../../../../../core/annotations/services/visual-prompt-service';
import { ModelsGroups } from '../../../../../core/models/models.interface';
import { hasActiveModels } from '../../../../../core/models/utils';
import { TooltipWithDisableButton } from '../../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { NO_MODELS_MESSAGE } from '../../../utils';
import { RunTestDialog } from './run-test-dialog.component';

interface RunTestButtonProps {
    modelsGroups: ModelsGroups[];
}

export const RunTestButton = ({ modelsGroups }: RunTestButtonProps): JSX.Element => {
    const [isRunTestDialogOpen, setIsRunTestDialogOpen] = useState<boolean>(false);

    const hasModels = modelsGroups?.some((group) => hasActiveModels(group) || isVisualPromptModelGroup(group));

    return (
        <>
            <TooltipWithDisableButton placement={'bottom'} disabledTooltip={NO_MODELS_MESSAGE}>
                <Button
                    id='run-test-button-id'
                    variant={'accent'}
                    onPress={() => setIsRunTestDialogOpen(true)}
                    isDisabled={!hasModels}
                >
                    Run test
                </Button>
            </TooltipWithDisableButton>
            <RunTestDialog
                modelsGroups={modelsGroups}
                isOpen={isRunTestDialogOpen}
                handleClose={() => setIsRunTestDialogOpen(false)}
            />
        </>
    );
};
