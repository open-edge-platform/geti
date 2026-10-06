// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { ReactNode } from 'react';

import type { TranslateFn } from '@/i18n';

import { Link } from '../../platform/components/link.component';

const ULTRALYTICS_TERMS_URL =
    // eslint-disable-next-line max-len
    'https://www.ultralytics.com/license?utm_source=intel&utm_medium=referral&utm_campaign=geti-model-garden&utm_content=user-notice';

// Verbatim legal notice supplied by Ultralytics; intentionally not translated.
/* eslint-disable max-len */
const ULTRALYTICS_NOTICE = [
    'Ultralytics YOLO software and models available through Geti are provided by Ultralytics under the GNU Affero General Public License v3.0 ("AGPL-3.0"), unless you have entered into a separate written license agreement with Ultralytics. Accessing, downloading, or retraining these materials through Geti does not grant you an Ultralytics Enterprise License or any other proprietary Ultralytics license.',
    'Depending on how Ultralytics YOLO is used, modified, integrated or made available, AGPL-3.0 may require applicable source code to be made available under AGPL-3.0, including in certain circumstances where software is made available for use over a network. You are responsible for reviewing the AGPL-3.0 terms and determining whether they apply to your intended use. Ultralytics position is that, if you wish to use YOLO in a proprietary commercial product, internal tool or production deployment without making applicable source code available under AGPL-3.0, you should obtain an Ultralytics Enterprise License.',
    'You are responsible for determining which applies to your use. Terms and enterprise licensing options are available at: ',
].join('\n\n');
/* eslint-enable max-len */

export type LicenseNotice = {
    id: string;
    name: string;
    notice: ReactNode;
    href: string;
    isRequired: boolean;
};

export const getIntelSimplifiedLicense = (t: TranslateFn): LicenseNotice => ({
    id: 'intel-simplified',
    name: t('license.notices.intelSimplified.name'),
    notice: t('license.notices.intelSimplified.notice'),
    // eslint-disable-next-line max-len
    href: 'https://www.intel.com/content/www/us/en/content-details/749362/intel-simplified-software-license-version-october-2022.html',
    isRequired: true,
});

export const getUltralyticsLicense = (t: TranslateFn): LicenseNotice => ({
    id: 'ultralytics',
    name: t('license.notices.ultralytics.name'),
    notice: (
        <>
            {ULTRALYTICS_NOTICE}
            <Link href={ULTRALYTICS_TERMS_URL} target={'_blank'} rel={'noopener noreferrer'}>
                {ULTRALYTICS_TERMS_URL}
            </Link>
        </>
    ),
    href: 'https://github.com/ultralytics/ultralytics/blob/main/LICENSE',
    isRequired: true,
});

export const getDinov3License = (t: TranslateFn): LicenseNotice => ({
    id: 'dinov3',
    name: t('license.notices.dinov3.name'),
    notice: t('license.notices.dinov3.notice'),
    href: 'https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md',
    isRequired: false,
});
