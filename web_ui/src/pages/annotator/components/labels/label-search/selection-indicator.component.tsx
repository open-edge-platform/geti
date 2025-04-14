// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, PropsWithChildren } from 'react';

import { dimensionValue } from '@react-spectrum/utils';

import { AcceptSmall, Add, CloseSmall } from '../../../../../assets/icons';
import { COLOR_MODE } from '../../../../../assets/icons/color-mode.enum';

const Wrapper: FC<PropsWithChildren & { ariaLabel?: string }> = ({ children, ariaLabel }) => {
    return (
        <div
            aria-label={ariaLabel}
            data-testid={'selection-suffix-id'}
            id={'selection-suffix-id'}
            style={{ width: dimensionValue('size-225'), height: dimensionValue('size-225') }}
        >
            {children}
        </div>
    );
};

export const SelectionIndicator = ({
    isHovered,
    isSelected,
}: {
    isHovered: boolean;
    isSelected: boolean;
}): JSX.Element => {
    if (isSelected) {
        if (isHovered) {
            return (
                <Wrapper ariaLabel={'Unassign label'}>
                    <CloseSmall color={COLOR_MODE.NEGATIVE} />
                </Wrapper>
            );
        }

        return (
            <Wrapper ariaLabel={'Assigned label'}>
                <AcceptSmall color={COLOR_MODE.POSITIVE} />
            </Wrapper>
        );
    } else {
        if (isHovered) {
            return (
                <Wrapper ariaLabel={'Assign label'}>
                    <Add />
                </Wrapper>
            );
        }

        return <Wrapper />;
    }
};
