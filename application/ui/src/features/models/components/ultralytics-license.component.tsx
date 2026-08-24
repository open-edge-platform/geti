// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Link } from '../../../platform/components/link.component';
import { useTranslation } from 'react-i18next';

const ULTRALYTICS_LICENSE_KEY = 'models.ultralyticsLicense';

export const UltralyticsLicense = () => {
    const { t } = useTranslation();

    return (
        <Link
            href={'https://www.ultralytics.com/legal/agpl-3-0-software-license'}
            target={'_blank'}
            rel={'noopener noreferrer'}
        >
            {t(ULTRALYTICS_LICENSE_KEY)}
        </Link>
    );
};
