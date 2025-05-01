// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MenuTrigger } from '@shared/components/menu-trigger/menu-trigger.component';
import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';

import { MoreMenu } from '../../../../assets/icons';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';

interface ContentMenuProps {
    point: KeypointNode;
    onUpdate: (point: KeypointNode) => void;
}

export const OPTION_VISIBLE = 'Mark as visible';
export const OPTION_OCCLUDED = 'Mark as occluded';

export const ContentMenu = ({ point, onUpdate }: ContentMenuProps) => {
    const option = point.isVisible ? OPTION_OCCLUDED : OPTION_VISIBLE;

    return (
        <MenuTrigger
            id={`pose-point-label-${point.label.id}`}
            items={[option]}
            onAction={() => onUpdate({ ...point, isVisible: !point.isVisible })}
        >
            <QuietActionButton aria-label='menu trigger'>
                <MoreMenu />
            </QuietActionButton>
        </MenuTrigger>
    );
};
