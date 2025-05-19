// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text } from '@geti/ui';

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
