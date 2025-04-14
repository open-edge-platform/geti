// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MutableRefObject, ReactNode } from 'react';

import { Grid } from '@adobe/react-spectrum';

interface LabelEditionFieldsWrapperProps {
    children: ReactNode;
    wrapperRef?: MutableRefObject<null>;
}

export const LabelEditionFieldsWrapper = ({ children, wrapperRef }: LabelEditionFieldsWrapperProps): JSX.Element => {
    const GRID_AREAS = ['color name hotkey actionButtons', '. nameError hotkeyError hotkeyError'];
    const GRID_COLUMNS = ['min-content', '1fr', 'auto', 'min-content'];

    return (
        <Grid
            alignItems={'center'}
            justifyContent={'center'}
            width={'100%'}
            ref={wrapperRef}
            areas={GRID_AREAS}
            columns={GRID_COLUMNS}
            columnGap={'size-100'}
            rowGap={'size-50'}
        >
            {children}
        </Grid>
    );
};
