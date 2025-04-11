// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { isVisualPromptModelGroup } from '../../../../../core/annotations/services/visual-prompt-service';
import { ModelsGroups } from '../../../../../core/models/models.interface';
import { hasActiveModels } from '../../../../../core/models/utils';
import { Button } from '../../../../../shared/components/button/button.component';
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
