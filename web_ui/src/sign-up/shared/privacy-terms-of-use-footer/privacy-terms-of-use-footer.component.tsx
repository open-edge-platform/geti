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

import { Text } from '@adobe/react-spectrum';

import classes from '../../pages/registration/registration.module.scss';

export const PrivacyTermsOfUseFooter = (): JSX.Element => (
    <Text marginTop={'size-600'} UNSAFE_className={classes.termsOfUseFooter}>
        By signing up, you agree to our{' '}
        <a
            href={'https://www.intel.com/content/www/us/en/privacy/intel-privacy-notice.html'}
            target={'_blank'}
            rel={'noopener noreferrer'}
        >
            Privacy
        </a>{' '}
        and{' '}
        <a
            href={'https://www.intel.com/content/www/us/en/legal/terms-of-use.html'}
            target={'_blank'}
            rel={'noopener noreferrer'}
        >
            Terms of use
        </a>
        .
    </Text>
);
