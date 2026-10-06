// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { TranslateFn } from '@/i18n';

import {
    getDinov3License,
    getIntelSimplifiedLicense,
    getUltralyticsLicense,
    type LicenseNotice,
} from './license-notices';

// The desktop (MSIX) app is itself distributed under the Intel Simplified Software License.
export const getLicenses = (t: TranslateFn): LicenseNotice[] => [
    getIntelSimplifiedLicense(t),
    getUltralyticsLicense(t),
    getDinov3License(t),
];
