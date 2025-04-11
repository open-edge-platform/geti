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

import { ButtonGroup, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { Reject } from '../../../../assets/icons';
import { ANIMATION_PARAMETERS } from '../../../../shared/animation-parameters/animation-parameters';
import { AcceptButton } from '../../../../shared/components/quiet-button/accept-button.component';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { useAnnotatorHotkeys } from '../../hooks/use-hotkeys-configuration.hook';
import { useAcceptRejectShortcut } from './use-accept-reject-shortcut/use-accept-reject-shortcut.hook';

interface AcceptRejectButtonGroupProps {
    id: string;
    isAcceptButtonDisabled?: boolean;
    shouldShowButtons: boolean;
    handleAcceptAnnotation: () => void;
    handleRejectAnnotation: () => void;
    rejectDeps?: Parameters<typeof useAcceptRejectShortcut>[0]['deps'];
    acceptDeps?: Parameters<typeof useAcceptRejectShortcut>[0]['deps'];
}

export const AcceptRejectButtonGroup = ({
    isAcceptButtonDisabled = false,
    handleAcceptAnnotation,
    handleRejectAnnotation,
    shouldShowButtons,
    acceptDeps = [],
    rejectDeps = [],
    id,
}: AcceptRejectButtonGroupProps): JSX.Element => {
    const { hotkeys } = useAnnotatorHotkeys();

    useAcceptRejectShortcut(
        { callback: handleAcceptAnnotation, isEnabled: shouldShowButtons && !isAcceptButtonDisabled, deps: acceptDeps },
        { callback: handleRejectAnnotation, isEnabled: shouldShowButtons, deps: rejectDeps }
    );

    return (
        <AnimatePresence>
            {shouldShowButtons && (
                <motion.div variants={ANIMATION_PARAMETERS.FADE_ITEM} initial={'hidden'} animate={'visible'}>
                    <ButtonGroup>
                        <TooltipTrigger placement={'bottom'}>
                            <QuietActionButton
                                key={`reject-${id}-annotation`}
                                onPress={handleRejectAnnotation}
                                id={`reject-${id}-annotation`}
                                aria-label={`reject ${id} annotation`}
                                marginEnd={'size-100'}
                            >
                                <Reject height={20} width={20} />
                            </QuietActionButton>
                            <Tooltip>{`Reject annotations - ${hotkeys.close.slice(0, 3).toUpperCase()}`}</Tooltip>
                        </TooltipTrigger>

                        <TooltipTrigger placement={'bottom'}>
                            <AcceptButton
                                key={`accept-${id}-annotation`}
                                onPress={handleAcceptAnnotation}
                                aria-label={`accept ${id} annotation`}
                                id={`accept-${id}-annotation`}
                                isDisabled={isAcceptButtonDisabled}
                            />
                            <Tooltip>{`Accept annotations - ${hotkeys.accept.toUpperCase()}`}</Tooltip>
                        </TooltipTrigger>
                    </ButtonGroup>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
