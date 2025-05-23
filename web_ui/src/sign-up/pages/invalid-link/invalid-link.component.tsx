// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { Button, Heading, Text } from '@geti/ui';

import { BrokenBulb } from '../../../assets/images';
import { ErrorLayout } from '../../../pages/errors/error-layout/error-layout.component';
import { redirectTo } from '../../../shared/utils';

import classes from '../../../pages/errors/error-layout/error-layout.module.scss';

export const InvalidLink = (): JSX.Element => {
    const handleLoginRedirect = (): void => {
        redirectTo(paths.root({}));
    };

    return (
        <ErrorLayout>
            <BrokenBulb aria-label={'Invalid link'} />
            <Heading marginTop={'size-175'} UNSAFE_className={classes.errorMessageHeader}>
                Oops, this link isn’t working...
            </Heading>
            <Text>It has already been used or expired.</Text>
            <Button variant={'primary'} marginTop={'size-250'} onPress={handleLoginRedirect}>
                Go to Intel® Geti™
            </Button>
        </ErrorLayout>
    );
};
