// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { TranslateFn } from '@/i18n';

import { getDinov3License, getUltralyticsLicense, type LicenseNotice } from './license-notices';

export const getLicenses = (t: TranslateFn): LicenseNotice[] => [getUltralyticsLicense(t), getDinov3License(t)];
