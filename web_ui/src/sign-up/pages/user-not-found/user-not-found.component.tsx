// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Heading, Text } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';

import { paths } from '../../../core/services/routes';
import { ErrorLayout } from '../../../pages/errors/error-layout/error-layout.component';
import { redirectTo } from '../../../shared/utils';

import classes from '../../../pages/errors/error-layout/error-layout.module.scss';

export const UserNotFound = (): JSX.Element => {
    const handleLoginRedirect = (): void => {
        redirectTo(paths.root({}));
    };

    const id = 'user-not-found';

    return (
        <ErrorLayout>
            <Heading
                level={1}
                marginBottom={'size-175'}
                UNSAFE_className={classes.errorCodeHeader}
                id={`${id}-error-code-id`}
            >
                404
            </Heading>
            <Heading
                level={2}
                marginBottom={'size-175'}
                UNSAFE_className={classes.errorMessageHeader}
                id={`${id}-title-id`}
            >
                Not found
            </Heading>
            <Text id={`${id}-text-id`}>User does not exist, it may have been deleted by an administrator.</Text>
            <Button id={`${id}-button-id`} variant={'primary'} marginTop={'size-250'} onPress={handleLoginRedirect}>
                Go to Intel® Geti™
            </Button>
        </ErrorLayout>
    );
};
