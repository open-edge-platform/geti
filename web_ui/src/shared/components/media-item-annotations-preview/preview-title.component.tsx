// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Heading } from '@adobe/react-spectrum';

export const PreviewTitle = (): JSX.Element => {
    return (
        <>
            <Heading id={'preview-title'} data-testid={'preview-title'}>
                Preview of predictions vs annotations
            </Heading>
            <Divider />
        </>
    );
};
