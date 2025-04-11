// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Heading, Text } from '@react-spectrum/text';

import { paths } from '../../../core/services/routes';
import { ErrorLayout } from '../../../pages/errors/error-layout/error-layout.component';
import { Button } from '../../../shared/components/button/button.component';
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
