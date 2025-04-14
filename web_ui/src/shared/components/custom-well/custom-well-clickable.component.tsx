// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { usePress } from 'react-aria';

import { CustomWell, CustomWellProps } from './custom-well.component';

interface CustomWellClickableProps extends CustomWellProps {
    onPress: () => void;
    onAuxClick?: () => void;
}

export const CustomWellClickable = ({
    children,
    onPress,
    flex,
    onAuxClick,
    ...props
}: CustomWellClickableProps): JSX.Element => {
    const { pressProps } = usePress({
        onPress,
    });

    return (
        <div {...pressProps} style={{ flex }} onAuxClick={onAuxClick}>
            <CustomWell {...props}>{children}</CustomWell>
        </div>
    );
};
