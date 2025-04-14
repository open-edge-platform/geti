// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Unpin } from '../../../../../assets/icons';
import { ActionButton } from '../../../../../shared/components/button/button.component';
import { useRenderDelay } from '../../../../../shared/hooks/use-render-delay.hook';

interface UnpinLabelButtonProps {
    unPinLabel: (labelId: string) => void;
    labelId: string;
    delay?: number;
    shift?: boolean;
}

export const UnpinLabelButton = ({ unPinLabel, labelId, delay = 0, shift = false }: UnpinLabelButtonProps) => {
    //NOTE: unpin should be shift by button right margin value
    const MARGIN = shift ? -12 : 0;
    const isShown = useRenderDelay(delay);

    return isShown ? (
        <ActionButton isQuiet onPress={() => unPinLabel(labelId)} marginEnd={MARGIN} width='size-225' height='size-225'>
            <Unpin aria-label={`${labelId}-unpin-icon`} id={'unpin-icon'} />
        </ActionButton>
    ) : (
        <></>
    );
};
